"""
Project registry: the projects AIKit builds (cockpit model, ADR-119).

AIKit is the workspace; each project it builds is its own folder and git repository, normally
`projects/<name>/`, or an existing folder attached by path. Everything AIKit records about a
project lives in that project's `.aikit/` directory, so AIKit's own gates, ledger and codebase map
never mix with project code, and a project never carries AIKit's tooling.

Projects under `projects/` are found by scanning for `.aikit/project.json`; only attached folders
outside it are listed in `projects/attached.json`. Both are ignored by AIKit's git. The stack and
test command are detected from the project's files on every call, never stored, so they cannot go
stale; `project.json` holds only an explicit `test_command` override.
"""

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from scripts.disruption_recovery import ROOT_DIR, atomic_write_json, file_lock

PROJECTS_DIRNAME = "projects"
ATTACHED_FILENAME = "attached.json"
MEMORY_DIRNAME = ".aikit"
CONFIG_FILENAME = "project.json"
SCHEMA_VERSION = 1
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
GIT_TIMEOUT_SECONDS = 30

# Transient files AIKit's atomic writes and locks leave next to project state (PRINCIPLE-013).
PROJECT_GITIGNORE_LINES = (
    ".aikit/*.lock",
    ".aikit/*.bak",
    ".aikit/*.tmp_*",
    ".aikit/*.corrupt_*",
)


class ProjectError(Exception):
    """A request AIKit cannot carry out, with its reason and remedy (PRINCIPLE-011 R6)."""

    def __init__(self, message: str, why: str, fix: str, exit_code: int = 1):
        super().__init__(message)
        self.why = why
        self.fix = fix
        self.exit_code = exit_code


@dataclass(frozen=True)
class Stack:
    """A toolchain detected in a project folder and the command that runs its tests."""

    name: str
    test_command: Optional[str]


@dataclass(frozen=True)
class Project:
    """A registered project as `aikit list` reports it."""

    name: str
    path: Path
    attached: bool
    stacks: Tuple[Stack, ...]
    test_command: Optional[str]
    present: bool


def _python_test(root: Path) -> str:
    pyproject = root / "pyproject.toml"
    uses_pytest = ((root / "pytest.ini").exists() or (root / "conftest.py").exists()
                   or (pyproject.exists()
                       and "pytest" in pyproject.read_text(encoding="utf-8", errors="replace")))
    return "python -m pytest" if uses_pytest else "python -m unittest discover"


def _node_test(root: Path) -> Optional[str]:
    try:
        manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    scripts = manifest.get("scripts") if isinstance(manifest, dict) else None
    test = scripts.get("test") if isinstance(scripts, dict) else None
    # `npm init` writes a placeholder test script that only fails; it is not a test command.
    if not isinstance(test, str) or "no test specified" in test:
        return None
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm test"
    return "yarn test" if (root / "yarn.lock").exists() else "npm test"


def _gradle_test(root: Path) -> str:
    return "./gradlew test" if (root / "gradlew").exists() else "gradle test"


def _fixed(command: str) -> Callable[[Path], str]:
    return lambda root: command


# (stack, marker globs, test-command resolver), in report order. Data, not branches: a new stack
# is one row (PRINCIPLE-009).
DETECTORS: Tuple[Tuple[str, Tuple[str, ...], Callable[[Path], Optional[str]]], ...] = (
    ("python", ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"), _python_test),
    ("node", ("package.json",), _node_test),
    ("rust", ("Cargo.toml",), _fixed("cargo test")),
    ("go", ("go.mod",), _fixed("go test ./...")),
    ("java-maven", ("pom.xml",), _fixed("mvn -q test")),
    ("java-gradle", ("build.gradle", "build.gradle.kts"), _gradle_test),
    ("dotnet", ("*.sln", "*.csproj", "*.fsproj"), _fixed("dotnet test")),
)


def detect_stacks(root: Path) -> Tuple[Stack, ...]:
    """Every stack whose marker file sits in the project's top folder (polyglot repos list several)."""
    found = []
    for name, markers, resolve in DETECTORS:
        if any(next(root.glob(marker), None) is not None for marker in markers):
            found.append(Stack(name, resolve(root)))
    return tuple(found)


def validate_name(name: str) -> None:
    """Reject names that are not one portable folder name."""
    if not NAME_PATTERN.match(name):
        raise ProjectError(
            f"Invalid project name '{name}'.",
            "a project name becomes a folder and a registry key, so it must be one portable path "
            "segment.",
            "use 1-64 lowercase letters, digits, '-' or '_', starting with a letter or digit, "
            "e.g. 'my-app'.",
            exit_code=2,
        )


def projects_dir(workspace: Path = ROOT_DIR) -> Path:
    return workspace / PROJECTS_DIRNAME


def config_path(project_root: Path) -> Path:
    return project_root / MEMORY_DIRNAME / CONFIG_FILENAME


def load_config(project_root: Path) -> Dict[str, object]:
    """A project's `.aikit/project.json`; a missing, unreadable or newer file is an error."""
    path = config_path(project_root)
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProjectError(
            f"Cannot read {path}: {exc}",
            "the file is AIKit's record of this project; without it the project is not registered.",
            f"restore it from the project's git history or `{path.name}.bak`, or attach the folder "
            "again with `python aikit.py attach <path>`.",
        ) from exc
    if not isinstance(config, dict) or config.get("schema") != SCHEMA_VERSION:
        raise ProjectError(
            f"{path} has an unsupported schema.",
            f"this AIKit reads project schema {SCHEMA_VERSION} only.",
            "update AIKit, or restore the file from the project's git history.",
        )
    return config


def _ensure_gitignore(project_root: Path) -> None:
    """Append the transient-state patterns the project's `.gitignore` does not yet list."""
    path = project_root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = [line for line in PROJECT_GITIGNORE_LINES if line not in text.splitlines()]
    if not missing:
        return
    prefix = "" if not text or text.endswith("\n") else "\n"
    block = prefix + "# AIKit transient state\n" + "\n".join(missing) + "\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(block)


def write_memory(project_root: Path, name: str, test_command: Optional[str] = None) -> bool:
    """
    Create the project's `.aikit/project.json` unless it exists. Returns whether it was created:
    an existing record is the project's memory and is never overwritten.
    """
    path = config_path(project_root)
    _ensure_gitignore(project_root)
    if path.exists():
        return False
    atomic_write_json(path, {
        "schema": SCHEMA_VERSION,
        "name": name,
        "test_command": test_command,
        "created": time.strftime("%Y-%m-%d"),
    })
    return True


def _attached_path(workspace: Path) -> Path:
    return projects_dir(workspace) / ATTACHED_FILENAME


def load_attached(workspace: Path = ROOT_DIR) -> Dict[str, str]:
    """Attached project folders by name; an unreadable file is an error, not an empty list."""
    path = _attached_path(workspace)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProjectError(
            f"Cannot read {path}: {exc}",
            "it lists the attached project folders; reading it as empty would forget them.",
            f"restore `{path.name}.bak` over it, or delete it and attach the folders again.",
        ) from exc
    projects = data.get("projects") if isinstance(data, dict) else None
    if not isinstance(projects, dict):
        raise ProjectError(
            f"{path} has no 'projects' mapping.",
            "it lists the attached project folders; reading it as empty would forget them.",
            f"restore `{path.name}.bak` over it, or delete it and attach the folders again.",
        )
    return {str(k): str(v) for k, v in projects.items()}


def _registered_names(workspace: Path) -> Dict[str, Path]:
    names = {name: Path(path) for name, path in load_attached(workspace).items()}
    root = projects_dir(workspace)
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if config_path(child).is_file():
                names.setdefault(child.name, child)
    return names


def _git_init(project_root: Path) -> None:
    try:
        result = subprocess.run(["git", "init", "--quiet"], cwd=project_root, capture_output=True,
                                text=True, timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProjectError(
            f"`git init` failed in {project_root}: {exc}",
            "every project is its own git repository, separate from AIKit's.",
            "install git and put it on PATH, then run the command again.",
        ) from exc
    if result.returncode != 0:
        raise ProjectError(
            f"`git init` failed in {project_root}: {result.stderr.strip()}",
            "every project is its own git repository, separate from AIKit's.",
            "fix the git error above, then run the command again.",
        )


def create_project(name: str, test_command: Optional[str] = None, workspace: Path = ROOT_DIR,
                   git_init: Optional[Callable[[Path], None]] = None) -> Path:
    """
    Create `projects/<name>/` as a new git repository holding the project's `.aikit/` memory.
    `git_init` defaults to running `git init` (PRINCIPLE-009 R4: a test injects a double).
    """
    git_init = git_init or _git_init
    validate_name(name)
    if name in _registered_names(workspace):
        raise ProjectError(
            f"A project named '{name}' already exists.",
            "a name selects exactly one project folder.",
            "pick another name, or work on the existing project.",
        )
    project_root = projects_dir(workspace) / name
    if project_root.exists():
        raise ProjectError(
            f"{project_root} already exists.",
            "`new` creates a folder; it never adopts or overwrites one.",
            f"run `python aikit.py attach {project_root}` to register the existing folder.",
        )
    project_root.mkdir(parents=True)
    try:
        git_init(project_root)
        write_memory(project_root, name, test_command)
    except BaseException:
        # Only this call created the folder, so removing it leaves no half-made project behind.
        shutil.rmtree(project_root, ignore_errors=True)
        raise
    return project_root


def attach_project(folder: Path, name: Optional[str] = None, test_command: Optional[str] = None,
                   workspace: Path = ROOT_DIR) -> Tuple[str, Path, bool]:
    """
    Register an existing folder as a project; returns (name, folder, memory_created). The folder's
    own files and git history are left alone apart from `.aikit/` and `.gitignore` entries.
    """
    folder = folder.resolve()
    if not folder.is_dir():
        raise ProjectError(
            f"{folder} is not a directory.",
            "`attach` registers an existing project folder.",
            "pass the path of the project's top folder, or create one with `python aikit.py new <name>`.",
            exit_code=2,
        )
    kit = workspace.resolve()
    inside_projects = projects_dir(kit) in folder.parents
    if not inside_projects and (folder == kit or kit in folder.parents or folder in kit.parents):
        raise ProjectError(
            f"{folder} overlaps the AIKit folder {kit}.",
            "a project inside AIKit's own tree (or containing it) would mix AIKit's files with the "
            "project's.",
            f"move the project into {projects_dir(kit)} or outside AIKit, then attach it.",
            exit_code=2,
        )
    name = name or re.sub(r"[^a-z0-9_-]+", "-", folder.name.lower()).strip("-_")
    validate_name(name)
    registered = _registered_names(kit)
    if name in registered and registered[name].resolve() != folder:
        raise ProjectError(
            f"A different project named '{name}' already exists.",
            "a name selects exactly one project folder.",
            "pass another name with `--name`.",
        )
    created = write_memory(folder, name, test_command)
    if not inside_projects:
        path = _attached_path(kit)
        with file_lock(path):
            attached = load_attached(kit)
            attached[name] = str(folder)
            atomic_write_json(path, {"schema": SCHEMA_VERSION, "projects": attached})
    return name, folder, created


def list_projects(workspace: Path = ROOT_DIR) -> List[Project]:
    """Every registered project, sorted by name; a vanished attached folder is reported, not dropped."""
    attached = set(load_attached(workspace))
    projects = []
    for name, path in sorted(_registered_names(workspace).items()):
        present = config_path(path).is_file()
        override = load_config(path).get("test_command") if present else None
        stacks = detect_stacks(path) if present else ()
        detected = next((s.test_command for s in stacks if s.test_command), None)
        projects.append(Project(name, path, name in attached, stacks,
                                override if isinstance(override, str) else detected, present))
    return projects

