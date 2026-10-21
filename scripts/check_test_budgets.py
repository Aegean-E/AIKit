#!/usr/bin/env python3
"""
Test Tier Budget Gate (PRINCIPLE-010 Rule 6, PRINCIPLE-014 Rule 3)

The two test tiers carry speed budgets because a slow tier stops being run. For months those
budgets were absolute wall-clock numbers that nothing measured:

  - the unit tier was budgeted under 1s and ran 1.21-1.45s for 317 tests;
  - the integration tier was budgeted under 5s and ran 7.63-7.94s for 45 tests.

Both drifted in unnoticed, because every Phase 4 command reported the tiers as green without
reporting how long they took. An absolute per-suite cap also cannot survive a growing suite:
adding a correct, fast test eventually breaks it, which pressures the agent to delete coverage.

This gate replaces the assumption with a measurement. It runs each tier exactly once, reads the
count and duration unittest itself prints, and compares the per-test average against the tier's
ceiling. It is the single way Phase 4 runs the tiers, so it adds no second run of its own.

Zero external dependencies (standard library only).

Usage:
  python scripts/check_test_budgets.py [--verbose]
Exit codes:
  0 every tier passed and stayed inside budget   1 a tier failed, exceeded budget or was unreadable   2 CLI argument misuse
"""

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

# The ceiling each tier's average test may reach, in milliseconds. Measured over three runs
# including a cold filesystem cache: unit 3.59-5.84ms, integration 169.58-176.49ms (ADR-144).
TIER_BUDGETS_MS: Dict[str, float] = {
    "tests.test_kit": 8.0,
    "tests.test_integration": 250.0,
}

# A tier that hangs must fail the gate rather than block delivery for ever.
TIER_TIMEOUT = 300

_SUMMARY = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s", re.M)


@dataclass(frozen=True)
class TierResult:
    """One tier's measured outcome; frozen so a report cannot edit what was measured."""

    module: str
    tests: int
    seconds: float
    passed: bool

    @property
    def per_test_ms(self) -> float:
        return (self.seconds / self.tests * 1000.0) if self.tests else 0.0

    @property
    def budget_ms(self) -> float:
        return TIER_BUDGETS_MS[self.module]

    @property
    def inside_budget(self) -> bool:
        return self.per_test_ms <= self.budget_ms


def parse_tier_output(output: str) -> Optional[Tuple[int, float]]:
    """The count and duration unittest prints, or None when it never got that far."""
    match = _SUMMARY.search(output)
    if not match:
        return None
    return int(match.group(1)), float(match.group(2))


def default_runner(module: str, timeout: int) -> Tuple[int, str]:
    """Run one tier the way the runbook documents it, so the gate measures the real command."""
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", module],
        cwd=str(ROOT_DIR), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def run_tier(module: str, runner: Optional[Callable[[str, int], Tuple[int, str]]] = None) -> Optional[TierResult]:
    """Measure one tier, or None when its output carried no summary to measure."""
    code, output = (runner or default_runner)(module, TIER_TIMEOUT)
    summary = parse_tier_output(output)
    if summary is None:
        return None
    tests, seconds = summary
    return TierResult(module=module, tests=tests, seconds=seconds, passed=(code == 0))


def budget_errors(results: List[TierResult]) -> List[str]:
    """One line per tier that is over its ceiling; empty when every tier fits."""
    return [
        f"{r.module}: {r.per_test_ms:.2f}ms per test exceeds the {r.budget_ms:.2f}ms ceiling "
        f"({r.tests} tests in {r.seconds:.3f}s)"
        for r in results
        if not r.inside_budget
    ]


def run_check(runner: Optional[Callable[[str, int], Tuple[int, str]]] = None, verbose: bool = False) -> int:
    print("=" * 58)
    print("TEST TIER BUDGET GATE (PRINCIPLE-010 R6)")
    print("=" * 58)

    results: List[TierResult] = []
    failures: List[str] = []
    for module in TIER_BUDGETS_MS:
        result = run_tier(module, runner=runner)
        if result is None:
            failures.append(f"{module}: produced no test summary, so it could not be measured")
            print(f"[FAIL] {module}: no 'Ran N tests in Xs' summary; the tier did not run")
            continue
        results.append(result)
        if not result.passed:
            failures.append(f"{module}: the tier failed")
        verdict = "FAIL" if not result.passed else ("OVER" if not result.inside_budget else "PASS")
        print(f"[{verdict}] {module}: {result.tests} tests in {result.seconds:.3f}s "
              f"= {result.per_test_ms:.2f}ms per test (ceiling {result.budget_ms:.2f}ms)")

    over = budget_errors(results)
    for line in over:
        print(f"Why: {line}")
    if over:
        print("Fix: profile the tier and return the slowest tests to budget, or raise the ceiling "
              "in PRINCIPLE-010 R6 with an ADR and the user's approval (PRINCIPLE-014 R3).")
    if failures:
        for line in failures:
            print(f"Why: {line}")
        print("Fix: run the tier directly to see which test failed, then repair it before delivery.")

    if verbose:
        for r in results:
            print(f"   {r.module}: budget {r.budget_ms:.2f}ms, headroom "
                  f"{r.budget_ms - r.per_test_ms:.2f}ms per test")

    if not failures and not over:
        print(f"[OK] {len(results)} tier(s) passed and stayed inside budget.")
    print("=" * 58)
    return 1 if (failures or over) else 0


KNOWN_FLAGS = {"--verbose", "-v", "--help", "-h"}

HELP_TEXT = """AIKit Test Tier Budget Gate (PRINCIPLE-010 Rule 6)

Usage:
  python scripts/check_test_budgets.py [OPTIONS]

Runs every test tier once and fails when a tier fails, when its output carries no summary, or
when its average test exceeds the tier's ceiling. This is Phase 4's way of running the tiers, so
it replaces running them by hand rather than adding a second run.

Options:
  --verbose, -v   Print each tier's ceiling and remaining headroom
  -h, --help      Show this help message and exit

Exit codes:
  0  inside budget    1  tier failed, over budget or unreadable    2  CLI argument misuse
"""


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(HELP_TEXT, end="")
        sys.exit(0)

    unknown = [a for a in argv if a.startswith("-") and a not in KNOWN_FLAGS]
    if unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Why: this gate accepts only {', '.join(sorted(KNOWN_FLAGS))}.", file=sys.stderr)
        print("Fix: run 'python scripts/check_test_budgets.py --help' to list valid options.",
              file=sys.stderr)
        sys.exit(2)

    sys.exit(run_check(verbose=("--verbose" in argv or "-v" in argv)))
