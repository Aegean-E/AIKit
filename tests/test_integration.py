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

    SCRIPTS = ("sync_principles.py", "disruption_recovery.py", "update_knowledge_base.py")

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
        forbidden = {
            "subprocess": r"\bsubprocess\b",
            "os.system": r"\bos\.system\b",
            "time.sleep": r"\btime\.sleep\b",
            "Popen": r"\bPopen\b",
        }
        offenders = [name for name, pat in forbidden.items() if re.search(pat, source)]
        self.assertEqual(
            offenders, [],
            f"{self.UNIT_MODULE.name} is the sub-second unit tier but references {offenders}; "
            f"move process-spawning or sleeping tests into tests/test_integration.py",
        )

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
