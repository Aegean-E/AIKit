"""Materialize Reforge as its own Git repository and synchronize both directions."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reforge.errors import ReforgeError
from reforge.git_history import run_git
from reforge.version import __version__

MARKER = ".reforge-repo.json"
SYNC_FILE = "reforge-sync.json"
DEFAULT_TARGET = Path("projects") / "aegean-reforge"


def source_root() -> Path:
    return Path(__file__).resolve().parent.parent


def sync_config(root: Optional[Path] = None) -> Dict[str, str]:
    """Read the AIKit-side sync file; defaults keep an older checkout working."""
    root = Path(root) if root else source_root()
    defaults = {"package": "reforge", "entrypoint": "reforge.py",
                "standalone": DEFAULT_TARGET.as_posix(), "marker": MARKER}
    path = root / SYNC_FILE
    if not path.is_file():
        return defaults
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReforgeError(
            f"Cannot read {path}.",
            f"the Reforge sync file is not valid JSON: {exc}",
            "fix the JSON, or delete it to use the documented defaults.",
        ) from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ReforgeError(
            f"{path} uses an unsupported sync schema.",
            "this Reforge reads reforge-sync.json schema 1 only.",
            "update Reforge, or restore the file from git.",
        )
    for key in ("package", "entrypoint", "standalone", "marker"):
        value = data.get(key, defaults[key])
        if not isinstance(value, str) or not value or value.startswith(("/", "\\")) \
                or ".." in Path(value).parts:
            raise ReforgeError(
                f"Invalid '{key}' in {path}.",
                "sync paths are relative to the AIKit checkout and may not escape it.",
                "use a relative path without '..'.",
            )
        defaults[key] = value
    return defaults


def manifest(root: Path, config: Optional[Dict[str, str]] = None) -> List[str]:
    """The shipped Reforge source: its package and standalone shim, never generated docs."""
    root = Path(root)
    config = config or sync_config(root)
    paths: List[str] = []
    shim = root / config["entrypoint"]
    if shim.is_file():
        paths.append(config["entrypoint"])
    package = root / config["package"]
    if package.is_dir():
        for path in sorted(package.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            paths.append(path.relative_to(root).as_posix())
    return paths


def _digest(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> None:
    """Atomic generated-file write: temp, fsync, replace (PRINCIPLE-013)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp_{os.getpid()}_{int(time.time() * 1000)}")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:  # hygiene: allow temp cleanup cannot fail the completed write
                pass


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def _marker(target: Path, marker_name: str = MARKER) -> Dict[str, object]:
    path = target / marker_name
    if not path.is_file():
        raise ReforgeError(
            f"{target} is not a Reforge standalone repository.",
            f"its {MARKER} marker is missing, so Reforge cannot tell its own source from a user's.",
            "run `reforge repo init` to create it, or point the command at the right folder.",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReforgeError(
            f"Cannot read {path}.",
            f"the synchronization marker is not valid JSON: {exc}",
            "restore it from the repository's git history; nothing was changed.",
        ) from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ReforgeError(
            f"{path} has an unsupported schema.",
            "this Reforge reads synchronization marker schema 1 only.",
            "update Reforge, or recreate the standalone repository with `repo init`.",
        )
    return data


README = """# Aegean Reforge

> Progressive, evidence-backed Git history auditing and autonomous safe repair.

Aegean Reforge walks a repository's history in independent runs. A run starts at `--start`, grows
by `--step` per stage and stops at `--stop` (defaults 3/3, unlimited): 3, 6, 9, ... or 4, 6, 8, 10.
After a repair is accepted the next stage re-examines the overlap, so a new commit is judged
against the changes already analysed. Runs can be stopped, resumed, reconfigured and started again
later with different settings; each keeps its own history. Each project has its own run lock, so
several projects audit concurrently and a second operation on one project is refused.

## Quick Start

- **Runtime Prerequisites**: Python 3.10+ and `git` (standard library only).
- **Canonical Regression Shield Gate**:

```bash
python -m unittest discover tests
```

## Why It Is Safe

- Findings must carry evidence: the exact commit, path, line and source text.
- Only small, mechanical repairs are automatic (bare `except`, mutable defaults, unsafe
  `yaml.load`, disabled TLS verification, `shell=True` with an argument list).
- Every repair is re-detected, the actual `git diff` is reviewed, and the project's tests run.
  A red gate rolls the patch back before it is recorded.
- Repairs are committed explicitly and pushed without force only when `--push` is passed.

## Commands

```bash
python reforge.py start <repo> --start 3 --step 3 --stop 15  # one independent run
python reforge.py run <repo>              # audit, repair, add regression tests, verify
python reforge.py run <repo> --push       # commit explicit paths, push without force
python reforge.py audit <repo>            # analyse the next window; no edits
python reforge.py fix <repo>              # repair the active run's safe findings
python reforge.py stop <repo> --run run-1
python reforge.py resume <repo> --run run-1
python reforge.py settings <repo> --step 4 --stop 20
python reforge.py runs <repo> --json
python reforge.py status <repo>
python reforge.py report <repo>
python reforge.py repo init [--path <dir>]
python reforge.py repo sync [--direction push|pull] [--force]
```

The audit state lives in `.aikit/reforge.json` and records each independent run: its settings,
stage windows, audited commits, findings, repairs, test results and gate results. A per-project
lock (`.aikit/reforge.run.lock`) prevents a second operation on the same project; different
projects use different locks and states and run concurrently.

## License

Free for personal use under the Aegean License 1.1 (AL-1.1); see [LICENSE](LICENSE). Commercial
use needs the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).
"""

CHANGELOG = f"""# Changelog

All notable changes to Aegean Reforge are recorded here.

## [0.2.1] - 2026-10-27

- `reforge-sync.json` names the shipped package, shim, standalone target and marker.
- Synchronization refuses a two-sided edit and records the last synced hashes.
- README/CHANGELOG regeneration keeps the standalone lifecycle current.

## [0.2.0] - 2026-10-27

- Independent, configurable audit runs: `--start`, `--step`, `--stop`, `stop`, `resume`,
  `settings` and `runs`, with per-run history.
- Per-project run lock: different projects audit concurrently; a second operation on one project
  is refused.
- Schema-2 state with schema-1 migration and compact run summaries.

## [0.1.0] - 2026-10-27

- Initial shipped source: progressive commit-window auditing, evidence-backed findings, safe
  repairs, generated regression tests, patch review, bounded test execution and bidirectional
  synchronization with AIKit.
"""

CONTRIBUTING = """# Contributing

1. Keep the standard-library-only baseline (`Python 3.10+`, `git`).
2. Run `python -m unittest discover tests` before a commit.
3. Repair defects with the smallest safe patch and add a regression test.
4. Use Conventional Commits and never force-push.
5. Edit the shipped source in AIKit first, then `python aikit.py reforge repo sync --direction push`
   to publish it here; use `--direction pull` for a fix made in this repository.
"""

SECURITY = """# Security

Report a vulnerability privately through GitHub's security advisory feature. Do not open a public
issue for an unfixed vulnerability. Reforge never executes audited code as part of the audit; the
only commands it runs are the project's declared test command and Git operations, both bounded by
a timeout.
"""

CI = """name: CI

on: [push, pull_request]

permissions:
  contents: read

jobs:
  verify:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.10', '3.13']
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Tests
        run: python -m unittest discover tests
      - name: CLI help
        run: python -m reforge --help
"""

ISSUE_BUG = """---
name: Bug report
about: Report a reproducible audit or repair defect
---

**What happened**

**Repository shape (language, test command)**

**Command and exit code**

**Evidence (finding code, path, commit)**
"""

ISSUE_FEATURE = """---
name: Feature request
about: Suggest a detector, repair or workflow
---

**Problem**

**Proposed evidence or safe repair**

**Why it cannot be automated safely**
"""

PR_TEMPLATE = """## What changed

## Evidence

## Verification

- [ ] `python -m unittest discover tests`
- [ ] `python -m reforge --help`
"""

GITIGNORE = """__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
*.corrupt_*
*.tmp*
*.bak
*.lock
"""

REUSE = """version = 1
SPDX-PackageName = "Aegean Reforge"
SPDX-PackageSupplier = "Aegean Works"
SPDX-PackageDownloadLocation = "NOASSERTION"
SPDX-PackageComment = "Free personal use under AL-1.1; commercial use under ACL-1.0."

[[annotations]]
path = "."
precedence = "aggregate"
SPDX-FileCopyrightText = "2026 Aegean Works"
SPDX-License-Identifier = "LicenseRef-AL-1.1"
"""

TEST_FILE = '''"""Smoke and regression tests for a standalone Aegean Reforge repository."""

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reforge.detectors import detect_source
from reforge.repair import repair_findings

PROC_TIMEOUT = 30


class ReforgeSmokeTests(unittest.TestCase):
    def test_detector_finds_a_bare_except(self):
        findings = detect_source("fixture.py", "try:\\n    pass\\nexcept:\\n    pass\\n", "abc")
        self.assertIn("bare-except", {finding.code for finding in findings})

    def test_repair_removes_a_bare_except_and_writes_a_test(self):
        root = Path(tempfile.mkdtemp(prefix="reforge_smoke_"))
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        (root / "fixture.py").write_text("try:\\n    pass\\nexcept:\\n    pass\\n", encoding="utf-8")
        findings = detect_source("fixture.py", (root / "fixture.py").read_text(encoding="utf-8"), "abc")
        repairs = repair_findings(root, findings)
        self.assertTrue(any(repair.applied for repair in repairs))
        tree = ast.parse((root / "fixture.py").read_text(encoding="utf-8"))
        self.assertEqual([n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and n.type is None], [])

    def test_cli_help_exits_zero(self):
        done = subprocess.run([sys.executable, "-m", "reforge", "--help"], capture_output=True,
                              text=True, timeout=PROC_TIMEOUT)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("usage:", done.stdout.lower())
'''

PYPROJECT = f"""[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "aegean-reforge"
version = "{__version__}"
description = "Progressive Git history auditing and autonomous safe repair"
requires-python = ">=3.10"
license = {{text = "AL-1.1"}}

[project.scripts]
reforge = "reforge.cli:main"

[tool.setuptools.packages.find]
include = ["reforge*"]
"""


def _generated_files(source: Path) -> Dict[str, str]:
    files = {
        "README.md": README,
        "CHANGELOG.md": CHANGELOG,
        "CONTRIBUTING.md": CONTRIBUTING,
        "SECURITY.md": SECURITY,
        "pyproject.toml": PYPROJECT,
        ".gitignore": GITIGNORE,
        "REUSE.toml": REUSE,
        ".github/workflows/ci.yml": CI,
        ".github/ISSUE_TEMPLATE/bug_report.md": ISSUE_BUG,
        ".github/ISSUE_TEMPLATE/feature_request.md": ISSUE_FEATURE,
        ".github/pull_request_template.md": PR_TEMPLATE,
        "tests/test_reforge.py": TEST_FILE,
    }
    for name in ("LICENSE", "COMMERCIAL.md"):
        path = source / name
        if path.is_file():
            files[name] = path.read_text(encoding="utf-8")
    license_text = files.get("LICENSE")
    if license_text:
        files["LICENSES/LicenseRef-AL-1.1.txt"] = license_text
    return files


def _git(root: Path, *args: str, timeout: int = 60) -> Tuple[int, str]:
    return run_git(root, *args, timeout=timeout)


def init_repo(source: Optional[Path] = None, target: Optional[Path] = None,
              force: bool = False) -> Dict[str, object]:
    """Create the standalone repository with source, docs, CI, issue templates and a first commit."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = Path(target) if target else source / config["standalone"]
    if target.exists() and any(target.iterdir()) and not force:
        raise ReforgeError(
            f"{target} already exists and is not empty.",
            "`repo init` creates a new standalone repository; it never adopts a folder.",
            "choose an empty --path, or pass --force to overwrite only Reforge's own source.",
        )
    target.mkdir(parents=True, exist_ok=True)
    shipped = manifest(source, config)
    if not shipped:
        raise ReforgeError(
            f"No Reforge source under {source}.",
            "the AIKit checkout is missing its reforge package.",
            "restore reforge/ and reforge.py, then run `repo init` again.",
        )
    written = []
    for relative in shipped:
        _copy(source / relative, target / relative)
        written.append(relative)
    for relative, text in _generated_files(source).items():
        _write(target / relative, text)
        written.append(relative)
    synced = {relative: _digest(target / relative) for relative in shipped}
    marker_name = config["marker"]
    _write(target / marker_name, json.dumps({
        "schema": 1,
        "name": "Aegean Reforge",
        "source": str(source),
        "version": __version__,
        "synced": synced,
    }, indent=2) + "\n")
    written.append(marker_name)
    code, output = _git(target, "init", "--quiet")
    if code != 0:
        raise ReforgeError(
            f"`git init` failed in {target}.",
            output[-400:] or "git returned a nonzero exit code.",
            "install git and put it on PATH, then retry.",
        )
    code, output = _git(target, "add", "--", *sorted(written))
    if code == 0:
        code, output = _git(target, "commit", "--quiet", "-m",
                            "chore: import Aegean Reforge from AIKit")
    if code != 0:
        cause = (output.strip().splitlines() or ["git commit failed"])[-1]
        raise ReforgeError(
            f"The initial Reforge commit failed: {cause}",
            "a standalone repository needs a committed baseline and lifecycle.",
            "set `git config user.name` and `git config user.email`, then retry `repo init`.",
        )
    return {"path": str(target), "files": len(written),
            "commit": _git(target, "rev-parse", "--short", "HEAD")[1].strip()}


def sync_repo(source: Optional[Path] = None, target: Optional[Path] = None,
              direction: str = "push", force: bool = False) -> Dict[str, object]:
    """Copy changed shipped files one way, refusing a file both sides changed since the last sync."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = Path(target) if target else source / config["standalone"]
    if direction not in {"push", "pull"}:
        raise ReforgeError(
            f"Unknown sync direction '{direction}'.",
            "synchronization moves shipped source one way at a time.",
            "pass --direction push (AIKit to the standalone repo) or pull (the reverse).",
            exit_code=2,
        )
    marker_name = config["marker"]
    marker = _marker(target, marker_name)
    synced = marker.get("synced") if isinstance(marker.get("synced"), dict) else {}
    shipped = manifest(source, config)
    copied: List[str] = []
    conflicts: List[str] = []
    ahead: List[str] = []
    for relative in shipped:
        a = _digest(source / relative)
        b = _digest(target / relative)
        s = synced.get(relative)
        if a == b:
            continue
        if direction == "push":
            if a is None:
                continue
            if b is None or b == s or force:
                _copy(source / relative, target / relative)
                copied.append(relative)
            elif a == s:
                ahead.append(relative)
            else:
                conflicts.append(relative)
        else:
            if b is None:
                continue
            if a is None or a == s or force:
                _copy(target / relative, source / relative)
                copied.append(relative)
            elif b == s:
                ahead.append(relative)
            else:
                conflicts.append(relative)
    if conflicts:
        raise ReforgeError(
            f"{len(conflicts)} file(s) changed on both sides since the last sync.",
            "overwriting either copy would silently lose work: " + ", ".join(conflicts[:8]),
            "merge the two copies by hand, then run the sync again; --force discards one side.",
        )
    marker["synced"] = {relative: _digest(target / relative) for relative in shipped}
    marker["source"] = str(source)
    marker["version"] = __version__
    _write(target / marker_name, json.dumps(marker, indent=2) + "\n")
    return {"direction": direction, "copied": copied, "ahead": ahead, "conflicts": conflicts,
            "path": str(target), "config": str(source / SYNC_FILE)}


def repo_status(source: Optional[Path] = None, target: Optional[Path] = None) -> Dict[str, object]:
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = Path(target) if target else source / config["standalone"]
    marker = _marker(target, config["marker"])
    synced = marker.get("synced") if isinstance(marker.get("synced"), dict) else {}
    differing = [relative for relative in manifest(source, config)
                 if _digest(source / relative) != _digest(target / relative)]
    stale = [relative for relative, digest in synced.items()
             if _digest(target / relative) != digest]
    code, output = run_git(target, "status", "--porcelain")
    return {"path": str(target), "version": marker.get("version"), "differing": differing,
            "stale_marker": stale, "dirty": bool(output) if code == 0 else True,
            "config": str(source / SYNC_FILE)}


def create_release(target: Path, tag: str, message: str = "") -> Dict[str, object]:
    """Create a local annotated release tag; publishing it stays a deliberate GitHub step."""
    target = Path(target)
    _marker(target)
    if not tag or any(char.isspace() for char in tag):
        raise ReforgeError(
            "A release needs a tag without whitespace.",
            "the tag names the released commit.",
            "pass --tag v0.2.0 and an optional --message.",
            exit_code=2,
        )
    code, output = run_git(target, "status", "--porcelain")
    if code == 0 and output:
        raise ReforgeError(
            "The standalone repository has uncommitted work.",
            "a release tag must point at a reviewed commit.",
            "commit or stash the work, then create the release.",
        )
    code, output = run_git(target, "tag", "-a", tag, "-m", message or f"Aegean Reforge {tag}")
    if code != 0:
        raise ReforgeError(
            f"Could not create tag {tag}.",
            output[-400:] or "the tag may already exist.",
            "choose a new tag, then retry.",
        )
    return {"tag": tag, "publish": f"git push origin {tag} && gh release create {tag} --notes-from-tag"}
