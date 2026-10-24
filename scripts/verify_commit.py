#!/usr/bin/env python3
"""
Post-Commit Verification (PRINCIPLE-018 Rule 7)

The pre-commit triad (R3) runs against the working tree, so it proves the *tree* is green, not
the *commit*. Those differ whenever staging is a subset of the tree, which is the normal case
under R2's explicit staging. Both failure modes happened on 2026-10-19: ADR-145 was committed
while its implementation sat unstaged, and a regenerated codebase map was committed twice while
stale in the commit itself.

This gate checks out the commit into a throwaway worktree in the system temp directory and runs
the whole gate set there, so a commit that cannot stand alone is caught while it is still local,
where PRINCIPLE-018 R5 undoes it with `git reset --soft HEAD^` instead of a revert.

Zero external dependencies (standard library only).

Usage:
  python scripts/verify_commit.py [--ref <commit>] [--verbose]
Exit codes:
  0 the commit is green    1 a gate failed or the worktree could not be made    2 CLI argument misuse
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
# A whole gate set runs inside the worktree; past this the run is hung, not slow.
GATE_TIMEOUT_SECONDS = 600
GIT_TIMEOUT_SECONDS = 120
# Lines of a failing gate's output shown (PRINCIPLE-012 R4, PRINCIPLE-015 R7).
FAILURE_TAIL_LINES = 12

Runner = Callable[[List[str], Path], Tuple[int, str]]


def run_command(argv: List[str], cwd: Path) -> Tuple[int, str]:
    """A command's exit code and combined output; -1 when it could not start or timed out."""
    try:
        done = subprocess.run(argv, cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=GATE_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)
    return done.returncode, (done.stdout + done.stderr).strip()


def gate_commands(secret_range: str) -> List[Tuple[str, List[str]]]:
    """
    The gates PRINCIPLE-018 R3 names, as they run inside the worktree. The secret scan reads the
    commit range rather than the tree, so it reports what the push would upload (ADR-145).
    """
    return [
        ("tiers", [sys.executable, "scripts/check_test_budgets.py"]),
        ("rules", [sys.executable, "scripts/sync_principles.py", "--check"]),
        ("knowledge", [sys.executable, "scripts/update_knowledge_base.py", "--check"]),
        ("reachability", [sys.executable, "scripts/check_reachability.py"]),
        ("secrets", [sys.executable, "scripts/check_secrets.py", "--commits", secret_range]),
        ("dogfood", [sys.executable, "scripts/dogfood.py"]),
    ]


def scanned_range(repo: Path, ref: str, run: Runner) -> str:
    """
    The commits this verification covers, as resolved SHAs: everything past the upstream when one
    resolves and is behind, otherwise this commit alone. Resolved, because the worktree is
    detached, where `@{u}` and `HEAD` mean something else or nothing.

    A bare SHA is returned only for a root commit, because `git log -p <sha>` walks every commit
    reachable from it: handing one back whenever no upstream resolved scanned the whole history,
    which stays red forever over a key already revoked (ADR-133, ADR-149).
    """
    head = run(["git", "rev-parse", ref], repo)[1].strip()
    code, upstream = run(["git", "rev-parse", f"{ref}@{{u}}"], repo)
    upstream = upstream.strip() if code == 0 else ""
    if upstream and upstream != head:
        return f"{upstream}..{head}"
    code, parent = run(["git", "rev-parse", f"{ref}^"], repo)
    parent = parent.strip() if code == 0 else ""
    return f"{parent}..{head}" if parent else head


def recovery_fix(ref: str, resolved: str, repo: Path, run: Runner) -> str:
    """
    The Fix line for a commit that fails on its own, chosen by where that commit is.

    The undo PRINCIPLE-018 R5 names, `git reset --soft HEAD^`, fits only an unpushed HEAD. It used
    to be printed for every failing commit, so verifying an older one with --ref, or one already on
    the remote, told the user to undo a different commit or rewrite published history (ADR-186).
    """
    target = run(["git", "rev-parse", ref], repo)[1].strip()
    if run(["git", "merge-base", "--is-ancestor", target, "HEAD@{u}"], repo)[0] == 0:
        return (f"Fix: {resolved} is already on the remote, so do not rewrite it: add what is "
                "missing in a new commit (PRINCIPLE-018 R5).")
    if target != run(["git", "rev-parse", "HEAD"], repo)[1].strip():
        return (f"Fix: {resolved} is not HEAD, so undoing HEAD would remove a different commit: "
                "add what is missing in a new commit (PRINCIPLE-018 R5).")
    return ("Fix: while the commit is unpushed, `git reset --soft HEAD^` (PRINCIPLE-018 R5), add "
            "what is missing, and commit again.")


def verify_commit(ref: str = "HEAD", repo: Path = ROOT_DIR,
                  runner: Optional[Runner] = None) -> Tuple[int, List[str]]:
    """
    Run every gate against `ref` checked out on its own; returns (exit code, report lines).
    `runner` defaults to real subprocesses (PRINCIPLE-009 R4: the tests inject a double).
    """
    run = runner or run_command
    report: List[str] = []
    code, resolved = run(["git", "rev-parse", "--short", ref], repo)
    if code != 0:
        return 1, ["Error: no commit to verify.",
                   f"Why: '{ref}' does not name a commit in {repo}.",
                   "Fix: commit first, or pass --ref <commit>."]
    resolved = resolved.strip()
    secret_range = scanned_range(repo, ref, run)

    tree = Path(tempfile.mkdtemp(prefix="aikit_verify_"))
    worktree = tree / "commit"
    worktree_added = False
    try:
        code, output = run(["git", "worktree", "add", "--detach", str(worktree), ref], repo)
        if code != 0:
            return 1, [f"Error: the commit {resolved} could not be checked out on its own.",
                       f"Why: `git worktree add` failed: {output[-300:]}",
                       "Fix: fix the git error above, then run this gate again."]
        worktree_added = True
        failures = []
        for name, argv in gate_commands(secret_range):
            code, output = run(argv, worktree)
            report.append(f"[{'PASS' if code == 0 else 'FAIL'}] {name}")
            if code != 0:
                failures.append(name)
                report += [f"       {line}" for line in
                           [l for l in output.splitlines() if l.strip()][-FAILURE_TAIL_LINES:]]
    finally:
        # The worktree is removed whether or not a gate failed, and its registration with it.
        if worktree_added:
            run(["git", "worktree", "remove", "--force", str(worktree)], repo)
        shutil.rmtree(tree, ignore_errors=True)

    if failures:
        return 1, report + [
            f"Error: commit {resolved} does not pass on its own: {', '.join(failures)}.",
            "Why: the pre-commit gates ran on the working tree, so the commit can hold less than "
            "what was tested (PRINCIPLE-018 R3, R7).",
            recovery_fix(ref, resolved, repo, run),
        ]
    return 0, report + [f"[OK] Commit {resolved} passes every gate on its own."]


KNOWN_FLAGS = {"--ref", "--verbose", "-v", "--help", "-h"}

HELP_TEXT = """AIKit Post-Commit Verification (PRINCIPLE-018 R7)

Usage:
  python scripts/verify_commit.py [OPTIONS]

Checks out a commit into a throwaway worktree and runs the whole gate set there, so a commit
that holds less than the tree it was tested in is caught while it is still local.

Options:
  --ref <commit>   The commit to verify (default: HEAD)
  --verbose, -v    Print the resolved commit range scanned for secrets
  -h, --help       Show this help message and exit

Exit codes:
  0  the commit is green    1  a gate failed, or the commit could not be checked out    2  CLI argument misuse
"""


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(HELP_TEXT, end="")
        sys.exit(0)
    unknown = [a for i, a in enumerate(argv) if a.startswith("-") and a not in KNOWN_FLAGS
               and (i == 0 or argv[i - 1] != "--ref")]
    if unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Why: this gate accepts only {', '.join(sorted(KNOWN_FLAGS))}.", file=sys.stderr)
        print("Fix: run 'python scripts/verify_commit.py --help' to list valid options.", file=sys.stderr)
        sys.exit(2)
    target = "HEAD"
    if "--ref" in argv:
        index = argv.index("--ref")
        if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
            print("[INVALID USAGE] --ref requires a commit.", file=sys.stderr)
            print("Why: there is no sensible default other than HEAD, which is already the default.",
                  file=sys.stderr)
            print("Fix: pass '--ref <commit>', or omit it to verify HEAD.", file=sys.stderr)
            sys.exit(2)
        target = argv[index + 1]

    print("=" * 58)
    print("POST-COMMIT VERIFICATION (PRINCIPLE-018 R7)")
    print("=" * 58)
    if "--verbose" in argv or "-v" in argv:
        print(f"Secret scan range: {scanned_range(ROOT_DIR, target, run_command)}")
    exit_code, lines = verify_commit(target)
    stream = sys.stdout if exit_code == 0 else sys.stderr
    for line in lines:
        print(line, file=stream)
    print("=" * 58, file=stream)
    sys.exit(exit_code)
