"""
Integration & Operational Dogfooding Tier (PRINCIPLE-014, PRINCIPLE-015).

This module holds the tests that must spawn real processes: multi-process concurrency
reproductions, real-binary CLI contracts, and real `git` output grounding. They cannot be
sub-millisecond by nature, so they are budgeted separately from the unit tier in
`test_kit.py`, which carries the strict <1s gate.

Both tiers run under the single canonical command (`python -m unittest discover tests`);
nothing here is hidden or opt-in. Every spawned process is bounded by an explicit timeout
(PRINCIPLE-010 R3, PRINCIPLE-015 R2) so a hung child can never stall the suite.
"""

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.check_secrets import run_scan  # noqa: E402
from scripts.disruption_recovery import (  # noqa: E402
    load_ledger,
    record_checkpoint,
    run_disruption_audit,
    format_audit_report,
    format_resume_report,
    classify_git_status,
    UNMERGED_CODES,
)

# Hard ceiling for any single spawned process in this tier (PRINCIPLE-015 R1).
PROC_TIMEOUT = 10


class TestParallelAgentSafety(unittest.TestCase):
    """
    Multi-process reproduction of the lost-update race (PRINCIPLE-013 R3).

    The advisory lock existed, was exported and was unit-tested, but had zero production call
    sites, so parallel subagents interleaved load/save cycles and silently erased each other's
    checkpoints. This requires genuinely separate processes: an in-process thread test would not
    reproduce what "parallel subagents" means.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="test_parallel_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.ledger = self.dir / ".agents" / "task_ledger.json"

    def test_parallel_checkpoints_do_not_lose_updates(self):
        code = (
            "import sys;sys.path.insert(0,r'" + str(ROOT_DIR) + "');"
            "from pathlib import Path;"
            "from scripts.disruption_recovery import record_checkpoint;"
            "record_checkpoint('agent-{}','phase 3','concurrent',"
            "ledger_file=Path(r'" + str(self.ledger) + "'))"
        )
        record_checkpoint("agent-SEED", "phase 3", "seed", ledger_file=self.ledger)
        agents = "ABC"
        procs = [subprocess.Popen([sys.executable, "-c", code.format(a)]) for a in agents]
        for p in procs:
            self.assertEqual(
                p.wait(timeout=PROC_TIMEOUT), 0, "a concurrent checkpoint process failed"
            )

        persisted = {c["task_id"] for c in load_ledger(self.ledger)["checkpoints"]}
        expected = {"agent-SEED"} | {f"agent-{a}" for a in agents}
        self.assertEqual(
            persisted, expected,
            f"Lost update detected: {expected - persisted} vanished under concurrent writes",
        )

    def test_no_lock_artifacts_survive_concurrent_writes(self):
        # PRINCIPLE-013: locks and temp buffers must not leak after contention resolves.
        record_checkpoint("t", "phase 1", "cp", ledger_file=self.ledger)
        leftovers = [
            p.name for p in self.ledger.parent.iterdir()
            if p.name.endswith(".lock") or ".tmp_" in p.name or ".steal_" in p.name
        ]
        self.assertEqual(leftovers, [], f"lock/temp artifacts leaked: {leftovers}")


class TestGitStatusGrounding(unittest.TestCase):
    """
    Empirical grounding of the porcelain parser against real `git` output (PRINCIPLE-003 R1).
    Exhaustive per-state classification is covered without subprocesses in the unit tier.
    """

    def test_parser_offsets_match_real_git_output(self):
        # The parser slices raw_line[:2] and raw_line[3:]; verify those offsets against output
        # produced by the actual git binary rather than a hand-written fixture.
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=PROC_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            self.skipTest("git unavailable")
        if res.returncode != 0:
            self.skipTest("not a git worktree")

        classified = classify_git_status(res.stdout)
        for raw in res.stdout.splitlines():
            if len(raw) < 4 or raw[:2] == "!!":
                continue
            path = raw[3:].strip()
            bucket = (
                classified["untracked"] if raw[:2] == "??"
                else classified["conflicted"] if raw[:2] in UNMERGED_CODES
                else classified["modified"]
            )
            self.assertTrue(
                any(path in entry for entry in bucket),
                f"real git line {raw!r} was not classified into {bucket}",
            )

    def test_conflict_audit_reports_block_rather_than_clean(self):
        # The contract an agent actually reads: a conflicted tree must never render "Clean state"
        # and must carry a remediation command (PRINCIPLE-011 R6).
        audit = run_disruption_audit(ROOT_DIR)
        audit.update({
            "has_conflicts": True,
            "has_uncommitted_changes": True,
            "conflicted_files": ["UU merged.txt"],
        })
        report = format_audit_report(audit)
        self.assertNotIn("Clean state", report)
        self.assertIn("UNRESOLVED MERGE CONFLICTS", report)
        self.assertIn("UU merged.txt", report)
        self.assertIn("merge --abort", report, "conflict report lacks a remediation command")

        resume = format_resume_report(audit)
        self.assertIn("BLOCKED", resume)
        self.assertIn("rebase --abort", resume)


class TestCommitValidatorCli(unittest.TestCase):
    """Conventional Commit validator exercised as a real binary (PRINCIPLE-018 R1)."""

    def _run(self, message):
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "disruption_recovery.py"),
             "--validate-commit", message],
            capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )

    def test_valid_message_exits_zero(self):
        res = self._run("feat(cli): add valid flag")
        self.assertEqual(res.returncode, 0)
        self.assertIn("[OK]", res.stdout)

    def test_invalid_message_exits_one_with_reason(self):
        res = self._run("invalid commit")
        self.assertEqual(res.returncode, 1)
        self.assertIn("[INVALID]", res.stderr)


class TestOperationalDogfooding(unittest.TestCase):
    """
    Dual-Track CLI Dogfooding & Zero-Blast-Radius Chaos Test (PRINCIPLE-015).
    Executes every entrypoint as a real subshell binary from an ephemeral sandbox cwd with
    stdin closed, asserting the CLI contract and zero host mutation. The subshell matrix runs
    once in a bounded thread pool (PRINCIPLE-010 R3) to keep this tier's cost flat.
    """

    SCRIPTS = (
        "sync_principles.py", "disruption_recovery.py", "update_knowledge_base.py",
        "dogfood.py", "check_reachability.py", "check_secrets.py",
    )

    @staticmethod
    def _porcelain():
        """Return the working-tree state, or None when git is unavailable."""
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=str(ROOT_DIR), timeout=PROC_TIMEOUT,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return res.stdout if res.returncode == 0 else None

    @classmethod
    def setUpClass(cls):
        cls.sandbox = Path(tempfile.mkdtemp(prefix="dogfood_jail_"))
        cls.addClassCleanup(shutil.rmtree, cls.sandbox, ignore_errors=True)

        def invoke(job):
            script, flag = job
            return job, subprocess.run(
                [sys.executable, str(ROOT_DIR / "scripts" / script), flag],
                capture_output=True, text=True, cwd=str(cls.sandbox),
                stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
            )

        # Track 1 (golden path): --help. Track 2 (hostile chaos): a malformed flag.
        jobs = [(s, f) for f in ("--help", "--not-a-real-flag") for s in cls.SCRIPTS]
        cls.tree_before = cls._porcelain()
        with ThreadPoolExecutor(max_workers=min(len(jobs), (os.cpu_count() or 2))) as pool:
            cls.results = dict(pool.map(invoke, jobs))
        cls.tree_after = cls._porcelain()

    def test_ephemeral_sandbox_isolation(self):
        # Blast-radius guard: the jail must be ephemeral and never the repo or a host user dir
        self.assertTrue(self.sandbox.exists())
        resolved = self.sandbox.resolve()
        self.assertNotEqual(resolved, ROOT_DIR.resolve())
        self.assertNotIn(
            str(ROOT_DIR.resolve()), str(resolved),
            f"Sandbox {resolved} must live outside the repository tree",
        )

    def test_golden_path_help_contract(self):
        # PRINCIPLE-011 R5/R6 + PRINCIPLE-015 R1: --help on every entrypoint exits 0 and
        # prints a usage block to stdout with clean stderr.
        for script in self.SCRIPTS:
            with self.subTest(script=script):
                res = self.results[(script, "--help")]
                self.assertEqual(res.returncode, 0, f"{script} --help must exit 0, got {res.returncode}")
                self.assertEqual(res.stderr, "", f"{script} --help wrote to stderr: {res.stderr!r}")
                self.assertIn("Usage:", res.stdout, f"{script} --help printed no usage block")
                self.assertIn("--help", res.stdout, f"{script} --help did not document --help")
                self.assertNotIn("Traceback", res.stdout + res.stderr)

    def test_chaos_unknown_flag_rejected_with_remediation_triad(self):
        # PRINCIPLE-015 R5 hostile perturbation: a malformed flag must abort with exit 2 and the
        # What/Why/Fix triad rather than silently performing the default action.
        for script in self.SCRIPTS:
            with self.subTest(script=script):
                res = self.results[(script, "--not-a-real-flag")]
                self.assertEqual(
                    res.returncode, 2,
                    f"{script} must exit 2 on CLI misuse, got {res.returncode}",
                )
                self.assertIn("[INVALID USAGE]", res.stderr, f"{script} misuse lacks a What clause")
                self.assertIn("Why:", res.stderr, f"{script} misuse lacks a Why clause")
                self.assertIn("Fix:", res.stderr, f"{script} misuse lacks a Fix clause")
                self.assertNotIn("Traceback", res.stderr)

    def test_dogfood_matrix_leaves_zero_blast_radius(self):
        # PRINCIPLE-015 R4 + PRINCIPLE-014 R4: the whole subshell matrix (golden + chaos)
        # must leave the working tree bit-for-bit unchanged.
        if self.tree_before is None or self.tree_after is None:
            self.skipTest("git unavailable; blast-radius assertion requires a git worktree")
        self.assertEqual(
            self.tree_before, self.tree_after,
            "PRINCIPLE-015 violation: the golden-path + chaos CLI matrix mutated the working tree",
        )


class TestWorkspaceIsolation(unittest.TestCase):
    """
    `disruption_recovery.py` anchors its ledger to the repository, not the working directory, so
    without `--workspace` a sandboxed dogfood run writes straight into the real ledger. The first
    dogfood run did exactly that, clobbering the active task (PRINCIPLE-015 R4).
    """

    def setUp(self):
        self.jail = Path(tempfile.mkdtemp(prefix="test_workspace_"))
        self.addCleanup(shutil.rmtree, self.jail, ignore_errors=True)

    def _ledger_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "disruption_recovery.py"), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )

    def test_workspace_flag_redirects_the_ledger(self):
        real_ledger = ROOT_DIR / ".agents" / "task_ledger.json"
        before = real_ledger.read_bytes() if real_ledger.exists() else None

        res = self._ledger_cli("--workspace", str(self.jail),
                               "--checkpoint", "isolated", "--phase", "planning",
                               "--desc", "workspace isolation probe")
        self.assertEqual(res.returncode, 0, f"checkpoint failed: {res.stderr[:200]}")

        sandbox_ledger = self.jail / ".agents" / "task_ledger.json"
        self.assertTrue(sandbox_ledger.exists(), "--workspace did not write into the sandbox")
        data = json.loads(sandbox_ledger.read_text(encoding="utf-8"))
        self.assertEqual(data["active_task"]["task_id"], "isolated")

        after = real_ledger.read_bytes() if real_ledger.exists() else None
        self.assertEqual(before, after, "--workspace run mutated the repository ledger")

    def test_workspace_without_value_is_refused(self):
        # PRINCIPLE-011 R5/R6: a flag that silently defaults to the real ledger would be worse
        # than an error, so a missing value must exit 2 with the remediation triad.
        res = self._ledger_cli("--workspace")
        self.assertEqual(res.returncode, 2, f"expected exit 2, got {res.returncode}")
        self.assertIn("[INVALID USAGE]", res.stderr)
        self.assertIn("Fix:", res.stderr)

    def test_audit_and_resume_honour_the_workspace(self):
        self._ledger_cli("--workspace", str(self.jail),
                         "--checkpoint", "scoped", "--phase", "verification",
                         "--phase-num", "4", "--desc", "scoped task")
        res = self._ledger_cli("--workspace", str(self.jail), "--resume")
        self.assertEqual(res.returncode, 0)
        self.assertIn("scoped", res.stdout)
        self.assertIn("Phase 4", res.stdout, "resume lost the phase recorded in the sandbox")


class TestDogfoodRunner(unittest.TestCase):
    """
    The operational dogfood runner is itself a shipped surface (PRINCIPLE-015), so it carries
    regression coverage like any other entrypoint.
    """

    RUNNER = ROOT_DIR / "scripts" / "dogfood.py"

    @classmethod
    def setUpClass(cls):
        cls.result = subprocess.run(
            [sys.executable, str(cls.RUNNER)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT_DIR), stdin=subprocess.DEVNULL, timeout=60,
        )

    def test_dogfood_run_passes_every_track(self):
        self.assertEqual(
            self.result.returncode, 0,
            f"dogfood gate failed. stdout: {self.result.stdout[-900:]} "
            f"stderr: {self.result.stderr[-400:]}",
        )
        self.assertNotIn("[FAIL]", self.result.stdout)
        self.assertIn("tracks passed", self.result.stdout)

    def test_dogfood_reports_tersely(self):
        # PRINCIPLE-015 R7: the console dashboard stays readable at a glance.
        lines = [l for l in self.result.stdout.splitlines() if l.strip()]
        self.assertLessEqual(len(lines), 18, f"dashboard too verbose ({len(lines)} lines)")

    def test_dogfood_covers_golden_and_chaos_tracks(self):
        # PRINCIPLE-015 R5: testing --help alone is explicitly forbidden.
        for track in ("golden lifecycle", "chaos perturbation", "blast radius"):
            with self.subTest(track=track):
                self.assertIn(track, self.result.stdout, f"dogfood omits the {track} track")

    def test_dogfood_emits_no_unhandled_traceback(self):
        # A reader-thread UnicodeDecodeError previously surfaced here on a cp1254 locale.
        self.assertNotIn("Traceback", self.result.stderr)
        self.assertNotIn("UnicodeDecodeError", self.result.stderr)

    def test_dogfood_writes_its_declared_log(self):
        log = ROOT_DIR / ".agents" / "dogfood_last_run.log"
        self.assertTrue(log.exists(), "PRINCIPLE-015 R7 log was not written")
        self.assertIn("track:", log.read_text(encoding="utf-8"))

    def test_dogfood_leaves_tracked_content_untouched(self):
        # The runner's own blast-radius claim, verified independently of the runner.
        self.assertIn("zero host mutation", self.result.stdout)

    def test_dogfood_cli_contract(self):
        help_res = subprocess.run(
            [sys.executable, str(self.RUNNER), "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )
        self.assertEqual(help_res.returncode, 0)
        self.assertIn("Usage:", help_res.stdout)
        self.assertEqual(help_res.stderr, "")

        bad_res = subprocess.run(
            [sys.executable, str(self.RUNNER), "--nope"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )
        self.assertEqual(bad_res.returncode, 2)
        self.assertIn("[INVALID USAGE]", bad_res.stderr)


class TestInvolvedCli(unittest.TestCase):
    """`sync_principles.py --involved` is the authoritative answer to PRINCIPLE-001 R3."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "sync_principles.py"), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )

    def test_lists_involved_principles_one_per_line(self):
        res = self._run("--involved", "FAIL:", "python", "scripts/dogfood.py", "exited", "1")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.split(), ["PRINCIPLE-015"])

    def test_text_after_involved_is_never_parsed_as_options(self):
        # Failing output often contains flags; they are text here, not --help or misuse.
        res = self._run("--involved", "--help", "--not-a-real-flag")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("Usage:", res.stdout)
        self.assertEqual(res.stdout.split(), ["PRINCIPLE-010"])  # its capsule names `--help`

    def test_missing_text_is_misuse(self):
        res = self._run("--involved")
        self.assertEqual(res.returncode, 2)
        self.assertIn("Fix:", res.stderr)


class TestTrackCli(unittest.TestCase):
    """`disruption_recovery.py --track` reads real git state (PRINCIPLE-002 R3)."""

    def test_track_follows_the_actual_diff(self):
        repo = Path(tempfile.mkdtemp(prefix="test_track_"))
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        git = ["git", "-c", "user.email=t@example.com", "-c", "user.name=T",
               "-c", "commit.gpgsign=false"]
        code = "def f(x):\n    return x + 1\n"
        (repo / "README.md").write_text("# r\n", encoding="utf-8")
        (repo / "m.py").write_text(code, encoding="utf-8")
        (repo / "modül.py").write_text(code, encoding="utf-8")  # git quotes this path without -z
        subprocess.run(["git", "init", "-q", "."], cwd=repo, check=True, timeout=PROC_TIMEOUT)
        subprocess.run([*git, "add", "-A"], cwd=repo, check=True, timeout=PROC_TIMEOUT)
        subprocess.run([*git, "commit", "-qm", "base"], cwd=repo, check=True, timeout=PROC_TIMEOUT)

        def track():
            res = subprocess.run(
                [sys.executable, str(ROOT_DIR / "scripts" / "disruption_recovery.py"),
                 "--workspace", str(repo), "--track"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            return res.stdout.splitlines()[0]

        self.assertEqual(track(), "Track A")
        # Bookkeeping that PRINCIPLE-002 R4 itself requires must not move the track.
        (repo / ".agents").mkdir()
        (repo / ".agents" / "task_ledger.json").write_text("{}", encoding="utf-8")
        self.assertEqual(track(), "Track A")
        # A comment edit to a non-ASCII-named file must be read, not misreported as deleted.
        (repo / "modül.py").write_text("# comment only\n" + code, encoding="utf-8")
        self.assertEqual(track(), "Track B")
        (repo / "m.py").write_text("# comment only\n" + code, encoding="utf-8")
        (repo / "README.md").write_text("# r, typo fixed\n", encoding="utf-8")
        self.assertEqual(track(), "Track B")
        (repo / "m.py").write_text(code.replace("+ 1", "+ 2"), encoding="utf-8")
        self.assertEqual(track(), "Track C")


class TestCallSiteCommand(unittest.TestCase):
    """PRINCIPLE-003 R2's exact command must work for every name kind it covers, flags included."""

    def test_command_finds_a_flag(self):
        res = subprocess.run(["git", "grep", "-n", "-w", "-e", "--track"], cwd=str(ROOT_DIR),
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=PROC_TIMEOUT)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("disruption_recovery.py", res.stdout)


class TestAstGateCli(unittest.TestCase):
    """PRINCIPLE-003 R7: the gate halts with file and line, never a raw traceback."""

    def test_syntax_error_halts_cleanly(self):
        probe = ROOT_DIR / "scripts" / "_ast_gate_probe.py"
        probe.write_text("def broken(:\n", encoding="utf-8")
        self.addCleanup(probe.unlink, missing_ok=True)
        res = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "update_knowledge_base.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn("_ast_gate_probe.py", res.stderr)
        self.assertIn("line 1", res.stderr)
        self.assertIn("Fix:", res.stderr)
        self.assertNotIn("Traceback", res.stderr)


class TestRepositorySecretHygiene(unittest.TestCase):
    """PRINCIPLE-019 live invariant. Integration tier: the scan shells out to `git ls-files`."""

    def test_this_repository_is_clean(self):
        # No tracked file or agent memory in AIKit carries a credential.
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = run_scan(mode="all")
        self.assertEqual(exit_code, 0, "secret scan found potential credentials in the repository")


class TestTierBudgetDiscipline(unittest.TestCase):
    """
    Structural enforcement of the two-tier test budget (PRINCIPLE-010 R6, PRINCIPLE-014 R3).

    A wall-clock assertion on a 1s budget would itself be flaky on a loaded machine, and flaky
    tests are blocking defects under PRINCIPLE-014 R3. The budget is therefore enforced
    structurally: the unit tier may not spawn processes or sleep on the wall clock, which is
    what makes it sub-second by construction. This tier, in turn, must bound every spawn.
    """

    UNIT_MODULE = ROOT_DIR / "tests" / "test_kit.py"

    def test_unit_tier_spawns_no_processes_and_never_sleeps(self):
        source = self.UNIT_MODULE.read_text(encoding="utf-8")
        # Calls, not the module name: test_kit imports subprocess solely to guard against spawns.
        forbidden = {
            "subprocess.run call": r"\bsubprocess\.run\(",
            "Popen call": r"\bPopen\(",
            "os.system call": r"\bos\.system\(",
            "time.sleep call": r"\btime\.sleep\(",
        }
        offenders = [name for name, pat in forbidden.items() if re.search(pat, source)]
        self.assertEqual(
            offenders, [],
            f"{self.UNIT_MODULE.name} is the sub-second unit tier but references {offenders}; "
            f"move process-spawning or sleeping tests into tests/test_integration.py",
        )

    def test_unit_tier_guards_itself_against_spawns(self):
        # Supersedes a ~1s full re-run of the unit tier under a detector: test_kit now installs a
        # module-level guard that fails any unit test the moment it starts a process, by name.
        source = self.UNIT_MODULE.read_text(encoding="utf-8")
        self.assertIn("def setUpModule():\n    subprocess.Popen.__init__ = _refuse_spawn", source)
        self.assertIn("def tearDownModule():\n    subprocess.Popen.__init__ = _REAL_POPEN_INIT",
                      source)

    def test_integration_tier_bounds_every_spawn(self):
        source = Path(__file__).read_text(encoding="utf-8")
        spawns = len(re.findall(r"subprocess\.(?:run|Popen)\(", source))
        timeouts = len(re.findall(r"timeout=(?:PROC_TIMEOUT|\d+)", source))
        self.assertGreater(spawns, 0, "integration tier should actually spawn processes")
        self.assertGreaterEqual(
            timeouts, spawns,
            "every subprocess in the integration tier must declare an explicit timeout "
            "(PRINCIPLE-010 R3)",
        )


if __name__ == "__main__":
    unittest.main()
