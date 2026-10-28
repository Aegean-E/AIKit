"""Explicit staging, conventional commit and never-forced push for accepted repairs."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from reforge.errors import ReforgeError
from reforge.git_history import (
    commit_paths,
    dirty_paths,
    push,
    run_git,
    stage_and_commit,
    status_paths,
)
from reforge.state import is_reforge_artifact

CONVENTIONAL = re.compile(r"^(?:feat|fix|chore|docs|refactor|test|perf|build|ci)(?:\([^)]+\))?: \S")


def validate_message(message: str) -> None:
    try:
        from scripts.disruption_recovery import validate_conventional_commit
    except ImportError:
        validate_conventional_commit = None
    if validate_conventional_commit is not None:
        ok, reason = validate_conventional_commit(message)
        if not ok:
            raise ReforgeError(
                f"Invalid commit message: {reason}",
                "Reforge commits follow Conventional Commits.",
                "pass a message like 'fix(reforge): repair stage 1 findings'.",
            )
        return
    if not CONVENTIONAL.match(message):
        raise ReforgeError(
            f"Invalid commit message: {message}",
            "Reforge commits follow Conventional Commits.",
            "pass a message like 'fix(reforge): repair stage 1 findings'.",
        )


def _paths_to_commit(root: Path) -> List[str]:
    changed = set(status_paths(root))
    changed.update(path for path in dirty_paths(root) if path not in changed)
    return sorted(path.replace("\\", "/") for path in changed
                  if not is_reforge_artifact(path))


def commit_repairs(root: Path, message: str, paths: Optional[Sequence[str]] = None) -> Dict[str, object]:
    """Stage exactly the repair paths, commit, and verify the commit holds them."""
    validate_message(message)
    selected = [path.replace("\\", "/") for path in (paths or _paths_to_commit(root))]
    if not selected:
        raise ReforgeError(
            "There is nothing to commit.",
            "the audit and its repairs left no tracked change.",
            "run `audit` or `run` first; nothing was committed.",
        )
    missing = [path for path in selected if not (root / path).exists() and
               run_git(root, "ls-files", "--error-unmatch", path)[0] != 0]
    if missing:
        raise ReforgeError(
            f"Cannot stage missing path(s): {', '.join(missing)}",
            "an explicit commit stages only files that exist or were tracked.",
            "re-run the repair; nothing was committed.",
        )
    code, output = stage_and_commit(root, selected, message)
    if code != 0:
        raise ReforgeError(
            "The repair commit failed.",
            output[-500:] or "git commit returned a nonzero exit code.",
            "fix the git error above, then run the command again.",
        )
    committed = set(commit_paths(root, "HEAD"))
    missing = [path for path in selected if path not in committed]
    if missing:
        raise ReforgeError(
            "The commit does not hold every repaired path.",
            f"missing from HEAD: {', '.join(missing)}",
            "stage and commit the missing paths deliberately; do not push this commit yet.",
        )
    return {"commit": run_git(root, "rev-parse", "--short", "HEAD")[1].strip(),
            "message": message, "paths": selected}


def deliver(root: Path, message: str, do_push: bool) -> Tuple[Dict[str, object], List[str]]:
    report = commit_repairs(root, message)
    lines = [f"[OK] Committed {report['commit']}: {message}"]
    if not do_push:
        lines.append("     Not pushed: pass --push to publish the repair commits.")
        return report, lines
    code, output = push(root)
    if code != 0:
        raise ReforgeError(
            "The commit is local, but the push failed.",
            output[-500:] or "git push returned a nonzero exit code.",
            "check the remote and credentials, then run `git push` yourself; never force.",
        )
    report["pushed"] = True
    lines.append("[OK] Pushed without force.")
    return report, lines
