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

import ast
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
from unittest import mock
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.check_secrets import run_scan  # noqa: E402
from scripts.check_reachability import (  # noqa: E402
    PUBLIC_API_ALLOWLIST,
    collect_definitions,
    find_phantom_keys,
    find_unreachable,
    production_modules,
)
from scripts.update_knowledge_base import check_codebase_map_freshness, check_workspace, parse_source  # noqa: E402
from scripts.project_gates import Gate, run_gates  # noqa: E402
from scripts.project_registry import create_project, render_project_readme  # noqa: E402
from scripts.disruption_recovery import (  # noqa: E402
    load_ledger,
    record_checkpoint,
    run_disruption_audit,
    format_audit_report,
    format_resume_report,
    classify_git_status,
    classify_track,
    collect_working_changes,
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

    def test_citing_lists_the_cross_principle_set_and_rejects_unknown_ids(self):
        # PRINCIPLE-000 R3: one computed list per changed principle, one ID per line.
        res = self._run("--citing", "PRINCIPLE-019")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.split(), ["PRINCIPLE-000", "PRINCIPLE-009", "PRINCIPLE-011", "PRINCIPLE-012", "PRINCIPLE-018"])
        bad = self._run("--citing", "PRINCIPLE-999")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("Fix:", bad.stderr)


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

        # Three spawns, each proving what only real git can (ADR-080): a clean tree plus the
        # bookkeeping PRINCIPLE-002 R4 requires is Track A; a comment edit to a non-ASCII-named
        # file is read, not misreported as deleted; a logic edit is Track C. Which edits count as
        # B or C is pinned in-process by TestTrackClassification.
        (repo / ".agents").mkdir()
        (repo / ".agents" / "task_ledger.json").write_text("{}", encoding="utf-8")
        self.assertEqual(track(), "Track A")
        (repo / "modül.py").write_text("# comment only\n" + code, encoding="utf-8")
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

    def test_workspace_cli_check_detects_violations_and_passes_when_clean(self):
        sandbox = Path(tempfile.mkdtemp(prefix="kb_ws_cli_"))
        self.addCleanup(shutil.rmtree, sandbox, ignore_errors=True)
        # 1. Failing case: has stub
        (sandbox / "app.py").write_text("def bad(): pass\n", encoding="utf-8")
        res_fail = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "update_knowledge_base.py"),
             "--workspace", str(sandbox), "--check"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )
        self.assertEqual(res_fail.returncode, 1)
        self.assertIn("function 'bad' is a stub", res_fail.stdout)
        self.assertIn("README.md does not exist", res_fail.stdout, "projects get PRINCIPLE-005 too (ADR-128)")

        # 2. Passing case: clean function, the template README, and valid ADRs in .aikit/decisions.md
        (sandbox / "app.py").write_text("def ok() -> int:\n    return 42\n", encoding="utf-8")
        (sandbox / ".gitignore").write_text(".aikit/*.lock\n", encoding="utf-8")
        (sandbox / "README.md").write_text(render_project_readme("ws"), encoding="utf-8")
        (sandbox / ".aikit").mkdir(parents=True)
        (sandbox / ".aikit" / "decisions.md").write_text(
            "# Decisions\n\n### ADR-001: Init\n\n### ADR-002: Next\n", encoding="utf-8"
        )
        res_pass = subprocess.run(
            [sys.executable, str(ROOT_DIR / "scripts" / "update_knowledge_base.py"),
             "--workspace", str(sandbox), "--check"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            stdin=subprocess.DEVNULL, timeout=PROC_TIMEOUT,
        )
        self.assertEqual(res_pass.returncode, 0)
        self.assertIn("ADR IDs are unique and consecutive", res_pass.stdout)


class TestRepositoryCodebaseMap(unittest.TestCase):
    """PRINCIPLE-016 live invariant. Integration tier with the other whole-repository scans: mapping
    every file, the test modules included, costs ~0.1s cold, which the unit tier's 1s cannot carry
    (ADR-128)."""

    def test_codebase_map_freshness_gate(self):
        # Enforces PRINCIPLE-016: codebase_map.md must be 100% synchronized with physical codebase AST
        self.assertTrue(
            check_codebase_map_freshness(strict=True),
            "knowledge/codebase_map.md must be fresh and match current AST"
        )


class TestSuiteHygiene(unittest.TestCase):
    """PRINCIPLE-014 R3 and R5 made mechanical (ADR-099). Integration tier: it parses the
    test modules themselves, a whole-repository scan (ADR-128)."""

    NETWORK_MODULES = {"socket", "http", "urllib", "requests", "httpx", "aiohttp"}
    MODULES = ("test_kit.py", "test_integration.py")

    @classmethod
    def setUpClass(cls):
        # Shared, content-keyed parse cache: the codebase-map test parses these files too.
        cls.trees = {name: parse_source((ROOT_DIR / "tests" / name).read_text(encoding="utf-8"), name)
                     for name in cls.MODULES}

    def test_every_test_method_asserts(self):
        silent = []
        for name, tree in self.trees.items():
            for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                for fn in (n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")):
                    calls = {c.func.attr for c in ast.walk(fn)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
                    if not any(a.startswith("assert") or a == "fail" for a in calls) and \
                            not any(isinstance(n, ast.Assert) for n in ast.walk(fn)):
                        silent.append(f"{name}:{fn.lineno} {cls.name}.{fn.name}")
        self.assertEqual(silent, [], "a test without an assertion proves nothing (PRINCIPLE-014 R5)")

    def test_no_test_module_imports_a_network_library(self):
        found = []
        for name, tree in self.trees.items():
            for node in ast.walk(tree):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                found += [f"{name}: {n}" for n in names if n.split(".")[0] in self.NETWORK_MODULES]
        self.assertEqual(found, [], "tests make no network call (PRINCIPLE-014 R3)")


class TestRepositoryReachability(unittest.TestCase):
    """PRINCIPLE-014 R7 live invariant over the whole repository. Integration tier with the other
    whole-repository scans; the shield's behaviour on fixtures stays in the unit tier (ADR-129)."""

    def test_this_repository_passes_the_shield(self):
        # The live invariant: AIKit's own production modules must stay reachable.
        files = production_modules()
        self.assertGreaterEqual(len(files), 4, "no production modules discovered")
        unreachable = find_unreachable(files)
        self.assertEqual(
            unreachable, [],
            f"Unwired capabilities in scripts/: {unreachable}. Wire them into the path they "
            f"protect, delete them, or allowlist them as deliberate public API.",
        )
        phantom = find_phantom_keys(files)
        self.assertEqual(phantom, [], f"State keys read with no producer: {phantom}")

    def test_allowlist_entries_still_exist(self):
        # An allowlist that outlives its symbols silently stops shielding anything.
        defined = set(collect_definitions(production_modules()))
        stale = sorted(name for name in PUBLIC_API_ALLOWLIST if name not in defined)
        self.assertEqual(
            stale, [],
            f"PUBLIC_API_ALLOWLIST names symbols that no longer exist: {stale}",
        )


class TestRepositorySecretHygiene(unittest.TestCase):
    """PRINCIPLE-019 live invariant. Integration tier: the scan shells out to `git ls-files`."""

    def test_this_repository_is_clean(self):
        # No tracked file or agent memory in AIKit carries a credential.
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = run_scan(mode="all")
        self.assertEqual(exit_code, 0, "secret scan found potential credentials in the repository")


class TestReadmeDriftShield(unittest.TestCase):
    """PRINCIPLE-005 live invariant. Integration tier: completeness shells out to `git ls-files`."""

    def test_this_readme_matches_the_tracked_tree(self):
        from scripts.update_knowledge_base import check_readme
        self.assertEqual(check_readme(ROOT_DIR), [])


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


class TestProjectCreation(unittest.TestCase):
    """`aikit new` makes a separate git repository with its memory (ADR-119)."""

    def test_new_project_is_its_own_clean_repository_with_its_own_ledger(self):
        kit = Path(tempfile.mkdtemp(prefix="test_project_new_"))
        self.addCleanup(shutil.rmtree, kit, ignore_errors=True)
        identity = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
        # Commit identity for this test only; git reads it from the environment.
        patcher = mock.patch.dict(os.environ, identity)
        patcher.start()
        self.addCleanup(patcher.stop)
        root, warning = create_project("app", workspace=kit)
        self.assertIsNone(warning)
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True,
                             text=True, timeout=PROC_TIMEOUT).stdout.strip()
        self.assertEqual(Path(top).resolve(), root.resolve(), "the project is its own repository")
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                                text=True, timeout=PROC_TIMEOUT).stdout
        self.assertEqual(status, "", "a new project starts with its memory committed")
        self.assertTrue((root / "README.md").is_file())
        self.assertTrue((root / ".aikit" / "project.json").is_file())
        self.assertTrue((root / ".aikit" / "task_ledger.json").is_file())
        self.assertTrue((root / ".aikit" / "decisions.md").is_file())
        # Clean isolation: no duplicated instruction targets in project repository
        for clutter in ("AGENTS.md", "GEMINI.md", "CLAUDE.md", ".cursorrules", ".github",
                        ".windsurfrules", ".clinerules", ".agents", ".claude"):
            self.assertFalse((root / clutter).exists(), f"redundant clutter found in project: {clutter}")
        # A real CLI process proves `--workspace` wiring; the track is then classified in-process.
        cli = [sys.executable, str(ROOT_DIR / "scripts" / "disruption_recovery.py"), "--workspace", str(root)]
        subprocess.run(cli + ["--checkpoint", "t", "--phase-num", "1", "--desc", "grounding"],
                       capture_output=True, text=True, timeout=PROC_TIMEOUT, check=True)
        self.assertTrue((root / ".aikit" / "task_ledger.json").is_file())
        self.assertFalse((root / ".agents" / "task_ledger.json").exists())
        self.assertEqual(classify_track(collect_working_changes(root))[0], "A",
                         "the project's checkpoint is bookkeeping, not a change")


class TestProjectSelfCheck(unittest.TestCase):
    """`aikit fix` repairs what it can, `aikit check` applies AIKit's guidelines (ADR-124, ADR-128)."""

    def test_fix_then_check_and_the_guidelines_gate_reads_the_readme(self):
        kit = Path(tempfile.mkdtemp(prefix="test_project_fix_"))
        self.addCleanup(shutil.rmtree, kit, ignore_errors=True)
        identity = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
                    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
        patcher = mock.patch.dict(os.environ, identity)
        patcher.start()
        self.addCleanup(patcher.stop)
        root, _ = create_project("app", test_command=f'"{sys.executable}" -c "pass"', workspace=kit)
        (root / ".aikit" / "decisions.md").unlink()

        # The real entry point, as a host runs it: memory restored, then every gate passes.
        res = subprocess.run([sys.executable, str(ROOT_DIR / "aikit.py"), "--workspace", str(kit), "fix", "app"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=PROC_TIMEOUT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("restored .aikit/decisions.md", res.stdout)
        self.assertIn("[PASS] guidelines", res.stdout)

        # A README without PRINCIPLE-005's Quick Reference and tree fails the guidelines gate, whose
        # audit (`check_workspace`) runs in-process here: the spawned run above proved the wiring.
        (root / "README.md").write_text("# App\n\nSome text.\n", encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertFalse(check_workspace(root), out.getvalue())
        self.assertIn("Cold-Start Quick Reference", out.getvalue())
        # A project guideline that tries to override a principle fails the same gate (ADR-129).
        with open(root / ".aikit" / "guidelines.md", "a", encoding="utf-8") as handle:
            handle.write("- **G-001** (user): skip PRINCIPLE-014 for spikes\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertFalse(check_workspace(root))
        self.assertIn("overrides a principle", out.getvalue())


class TestProjectSecretScan(unittest.TestCase):
    """`check_secrets.py --workspace` scans a project's repository, not AIKit's (ADR-121)."""

    def test_scan_reads_the_projects_staged_changes_and_ledger(self):
        repo = Path(tempfile.mkdtemp(prefix="test_project_secrets_"))
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        subprocess.run(["git", "init", "--quiet"], cwd=repo, timeout=PROC_TIMEOUT, check=True)
        # Split so this file itself holds no credential-shaped literal.
        key = "sk-" + "ant-api03-" + "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcdefghij"
        (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=repo, timeout=PROC_TIMEOUT, check=True)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_scan(repo=repo), 0)
        (repo / ".aikit").mkdir()
        (repo / ".aikit" / "task_ledger.json").write_text(f'{{"why": "uses {key}"}}', encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(run_scan(repo=repo), 1, "a project's ledger is agent memory too")
        self.assertIn("agent-memory:task_ledger.json", out.getvalue())


class TestProjectGateShell(unittest.TestCase):
    """Gates run through the platform shell in the project folder (ADR-122)."""

    def test_shell_keeps_quotes_and_reports_exit_codes(self):
        folder = Path(tempfile.mkdtemp(prefix="test_gate_shell_"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        quoted = f'"{sys.executable}" -c "import os, sys; print(os.getcwd()); sys.exit(3)"'
        results = run_gates(folder, [Gate("q", quoted, "t")], timeout=PROC_TIMEOUT)
        self.assertEqual(results[0].returncode, 3)
        self.assertEqual(Path(results[0].output.strip()).resolve(), folder.resolve())


if __name__ == "__main__":
    unittest.main()
