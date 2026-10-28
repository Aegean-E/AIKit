"""Materialize Idea Catcher's shipped tool source and synchronize both directions."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

SYNC_FILE = "idea-catcher-sync.json"
DEFAULT_PACKAGE = "idea_catcher"
DEFAULT_ENTRYPOINT = "idea_catcher.py"
DEFAULT_STANDALONE = (Path("projects") / "idea-catcher").as_posix()
DEFAULT_MARKER = ".idea-catcher-repo.json"
GIT_TIMEOUT = 60


class SyncError(RuntimeError):
    """A repository sync request was refused; carries the AIKit What/Why/Fix triad."""

    def __init__(self, message: str, why: str, fix: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.why = why
        self.fix = fix
        self.exit_code = exit_code

    def triad(self) -> str:
        return f"{self.message}\nWhy: {self.why}\nFix: {self.fix}"


def source_root() -> Path:
    """The AIKit checkout that owns this package, found by its sync file."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / SYNC_FILE).is_file():
            return parent
    return here.parent.parent


def sync_config(root: Optional[Path] = None) -> Dict[str, str]:
    """Read the AIKit-side sync file; every path is relative to the checkout."""
    root = Path(root) if root else source_root()
    path = root / SYNC_FILE
    if not path.is_file():
        raise SyncError(
            f"{root} is not an AIKit checkout with Idea Catcher source.",
            f"the synchronization file {SYNC_FILE} is missing, so the two copies cannot be told apart.",
            "run the command from the AIKit checkout, or restore the file from git.",
            exit_code=2,
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncError(
            f"Cannot read {path}.",
            f"the Idea Catcher sync file is not valid JSON: {exc}",
            "fix the JSON, or restore the file from git.",
        ) from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise SyncError(
            f"{path} uses an unsupported sync schema.",
            "this Idea Catcher reads idea-catcher-sync.json schema 1 only.",
            "restore the file from git.",
        )
    config = {
        "package": DEFAULT_PACKAGE,
        "entrypoint": DEFAULT_ENTRYPOINT,
        "standalone": DEFAULT_STANDALONE,
        "marker": DEFAULT_MARKER,
    }
    for key in config:
        value = data.get(key, config[key])
        if not isinstance(value, str) or not value or value.startswith(("/", "\\")) \
                or ".." in Path(value).parts:
            raise SyncError(
                f"Invalid '{key}' in {path}.",
                "sync paths are relative to the AIKit checkout and may not escape it.",
                "use a relative path without '..'.",
                exit_code=2,
            )
        config[key] = value
    return config


def manifest(root: Path, config: Dict[str, str]) -> List[str]:
    """The shipped Idea Catcher source: the package and its standalone shim."""
    root = Path(root)
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


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, timeout=GIT_TIMEOUT
    )


def _marker(target: Path, marker_name: str) -> Dict[str, object]:
    path = target / marker_name
    if not path.is_file():
        raise SyncError(
            f"{target} is not an Idea Catcher standalone repository.",
            f"its {marker_name} marker is missing, so the two copies cannot be told apart.",
            "run `repo adopt` for the existing register, or `repo init` for an empty one.",
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SyncError(
            f"Cannot read {path}.",
            f"the synchronization marker is not valid JSON: {exc}",
            "restore it from the repository's git history; nothing was changed.",
        ) from exc
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise SyncError(
            f"{path} has an unsupported schema.",
            "this Idea Catcher reads marker schema 1 only.",
            "recreate the marker with `repo adopt`.",
        )
    return data


def _target(root: Path, config: Dict[str, str], target: Optional[Path]) -> Path:
    return Path(target) if target else root / config["standalone"]


def init_repo(source: Optional[Path] = None, target: Optional[Path] = None,
              force: bool = False) -> Dict[str, object]:
    """Create an empty standalone repository with the shipped source and a first commit."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = _target(source, config, target)
    if target.exists() and any(target.iterdir()) and not force:
        raise SyncError(
            f"{target} already exists and is not empty.",
            "`repo init` creates a new standalone repository; it never adopts a register.",
            "pass --force to overwrite only Idea Catcher's own source, or use `repo adopt`.",
        )
    target.mkdir(parents=True, exist_ok=True)
    shipped = manifest(source, config)
    if not shipped:
        raise SyncError(
            f"No Idea Catcher source under {source}.",
            "the AIKit checkout is missing its idea_catcher package.",
            "restore idea_catcher/ and idea_catcher.py, then retry.",
        )
    for relative in shipped:
        _copy(source / relative, target / relative)
    synced = {relative: _digest(target / relative) for relative in shipped}
    _write(target / config["marker"], json.dumps({
        "schema": 1,
        "name": "Idea Catcher",
        "source": str(source),
        "version": _version(),
        "synced": synced,
    }, indent=2) + "\n")
    if not (target / ".git").exists():
        done = _git(target, "init", "--quiet")
        if done.returncode != 0:
            raise SyncError(
                f"`git init` failed in {target}.",
                done.stderr[-400:] or "git returned a nonzero exit code.",
                "install git and put it on PATH, then retry.",
            )
    done = _git(target, "add", "--", *sorted(shipped), config["marker"])
    if done.returncode == 0:
        _git(target, "commit", "--quiet", "-m", "chore: import Idea Catcher from AIKit")
    return {"path": str(target), "files": len(shipped), "marker": config["marker"]}


def adopt_repo(source: Optional[Path] = None, target: Optional[Path] = None) -> Dict[str, object]:
    """Attach the shipped source to an existing register and record the sync baseline."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = _target(source, config, target)
    if not (target / "targets.json").is_file():
        raise SyncError(
            f"{target} has no targets.json.",
            "adoption expects an existing Idea Catcher register, not an empty folder.",
            "point --path at the register, or use `repo init` for a new empty repository.",
        )
    shipped = manifest(source, config)
    copied: List[str] = []
    for relative in shipped:
        a = _digest(source / relative)
        b = _digest(target / relative)
        if a != b:
            _copy(source / relative, target / relative)
            copied.append(relative)
    synced = {relative: _digest(target / relative) for relative in shipped}
    _write(target / config["marker"], json.dumps({
        "schema": 1,
        "name": "Idea Catcher",
        "source": str(source),
        "version": _version(),
        "synced": synced,
    }, indent=2) + "\n")
    return {"path": str(target), "copied": copied, "marker": config["marker"]}


def sync_repo(source: Optional[Path] = None, target: Optional[Path] = None,
              direction: str = "push", force: bool = False) -> Dict[str, object]:
    """Copy changed shipped files one way, refusing a file both sides changed since the last sync."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = _target(source, config, target)
    if direction not in {"push", "pull"}:
        raise SyncError(
            f"Unknown sync direction '{direction}'.",
            "synchronization moves shipped source one way at a time.",
            "pass --direction push (AIKit to the standalone repo) or pull (the reverse).",
            exit_code=2,
        )
    marker = _marker(target, config["marker"])
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
        raise SyncError(
            f"{len(conflicts)} file(s) changed on both sides since the last sync.",
            "overwriting either copy would silently lose work: " + ", ".join(conflicts[:8]),
            "merge the two copies by hand, then run the sync again; --force discards one side.",
        )
    marker["synced"] = {relative: _digest(target / relative) for relative in shipped}
    marker["source"] = str(source)
    marker["version"] = _version()
    _write(target / config["marker"], json.dumps(marker, indent=2) + "\n")
    return {"direction": direction, "copied": copied, "ahead": ahead, "conflicts": conflicts,
            "path": str(target), "config": str(source / SYNC_FILE)}


def repo_status(source: Optional[Path] = None, target: Optional[Path] = None) -> Dict[str, object]:
    """Compare both copies and the last synced baseline without changing anything."""
    source = Path(source) if source else source_root()
    config = sync_config(source)
    target = _target(source, config, target)
    marker = _marker(target, config["marker"])
    synced = marker.get("synced") if isinstance(marker.get("synced"), dict) else {}
    differing = [relative for relative in manifest(source, config)
                 if _digest(source / relative) != _digest(target / relative)]
    stale = [relative for relative, digest in synced.items()
             if _digest(target / relative) != digest]
    done = _git(target, "status", "--porcelain")
    return {"path": str(target), "version": marker.get("version"), "differing": differing,
            "stale_marker": stale, "dirty": bool(done.stdout) if done.returncode == 0 else True,
            "config": str(source / SYNC_FILE)}


def _version() -> str:
    try:
        from .version import __version__
    except ImportError:  # pragma: no cover - only a broken checkout reaches this
        return "0"
    return __version__
