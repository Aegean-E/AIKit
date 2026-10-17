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

from scripts.disruption_recovery import (
    PROJECT_MEMORY_DIRNAME,
    ROOT_DIR,
    atomic_write_json,
    file_lock,
)
from scripts.update_knowledge_base import guideline_errors, write_generated_file

PROJECTS_DIRNAME = "projects"
ATTACHED_FILENAME = "attached.json"
CONFIG_FILENAME = "project.json"
DECISIONS_FILENAME = "decisions.md"
# The project's decision register; entries follow the same format as AIKit's knowledge/decisions.md.
GUIDELINES_FILENAME = "guidelines.md"
# The project tier of PRINCIPLE-001 R4: rules for this project only, below every principle.
GUIDELINES_TEMPLATE = (
    "# Project Guidelines\n\n"
    "Rules for this project only, written by people or AI agents. They add to AIKit's principles and\n"
    "rank below them: a guideline never overrides a principle (PRINCIPLE-000 R6, PRINCIPLE-001 R4).\n"
    "Add one with `python aikit.py guideline <name> \"<rule>\" --source <user|ADR-NNN|person>`, or by\n"
    "hand as one line below in the form `- **G-NNN** (source): rule`; IDs are never reused.\n\n"
    "## Rules\n"
)
DECISIONS_TEMPLATE = (
    "# Decisions\n\n"
    "Why this project is built the way it is, oldest first. One entry per decision that changes a\n"
    "contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.\n\n"
    "<!-- Entry format:\n"
    "### ADR-001: <decision in one line>\n"
    "- **Date**: YYYY-MM-DD\n"
    "- **Status**: Accepted\n"
    "- **Context**: <what forced the decision>\n"
    "- **Decision**: <what was decided>\n"
    "- **Consequences**: <what follows, including what it costs>\n"
    "-->\n"
)

def render_project_readme(name: str, test_command: Optional[str] = None) -> str:
    """
    A README that passes PRINCIPLE-005's audit as created: Quick Reference with a versioned
    prerequisite and a fenced test command, and a tree of every tracked top-level entry. `.aikit/`
    is listed without children, so a new memory file never makes the tree incomplete.
    """
    return (
        f"# {name}\n\n"
        "## ⚡ 30-Second Cold-Start Quick Reference\n\n"
        "- **Runtime Prerequisites**: git and Python 3.10+ (AIKit's gates); add this project's own.\n"
        "- **Canonical Regression Shield Gate**:\n"
        "  ```bash\n"
        f"  {test_command or f'python aikit.py check {name}'}\n"
        "  ```\n\n"
        "### 🛠️ AIKit Commands (run from the AIKit folder)\n"
        "| Role | Command |\n"
        "|---|---|\n"
        f"| Status, task and gates | `python aikit.py status {name}` |\n"
        f"| Phase 4: every gate | `python aikit.py check {name}` |\n"
        f"| Repair memory and map, then check | `python aikit.py fix {name}` |\n"
        f"| Resume an interrupted task | `python aikit.py resume {name}` |\n\n"
        "## 📦 What's Inside\n\n"
        "```text\n"
        f"{name}/\n"
        "├── .gitignore                <- transient AIKit state excluded\n"
        "├── README.md\n"
        "└── .aikit/                   <- this project's memory: record, ledger, decisions\n"
        "```\n"
    )


def seed_readme(project_root: Path, name: str, test_command: Optional[str] = None) -> bool:
    """
    Write the template README when the project has none; returns whether it did. `new` and `fix`
    call it, `attach` never does: attaching leaves an existing folder's files alone.
    """
    readme = project_root / "README.md"
    if readme.exists():
        return False
    write_generated_file(readme, render_project_readme(name, test_command))
    return True


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


def node_scripts(root: Path) -> Dict[str, str]:
    """The `scripts` map of the project's `package.json`; empty when absent or unreadable."""
    try:
        manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    scripts = manifest.get("scripts") if isinstance(manifest, dict) else None
    if not isinstance(scripts, dict):
        return {}
    return {str(k): v for k, v in scripts.items() if isinstance(v, str)}


def node_runner(root: Path) -> str:
    """The package manager the project's lockfile names: pnpm, yarn, or npm by default."""
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    return "yarn" if (root / "yarn.lock").exists() else "npm"


def _node_test(root: Path) -> Optional[str]:
    test = node_scripts(root).get("test")
    # `npm init` writes a placeholder test script that only fails; it is not a test command.
    if test is None or "no test specified" in test:
        return None
    return f"{node_runner(root)} test"


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
    return project_root / PROJECT_MEMORY_DIRNAME / CONFIG_FILENAME


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
    Create the project's `.aikit/project.json`, `.aikit/decisions.md` and `.aikit/task_ledger.json`
    unless they exist. Returns whether `project.json` was created: existing memory is never
    overwritten.
    """
    path = config_path(project_root)
    _ensure_gitignore(project_root)
    guidelines = project_root / PROJECT_MEMORY_DIRNAME / GUIDELINES_FILENAME
    if not guidelines.exists():
        write_generated_file(guidelines, GUIDELINES_TEMPLATE)
    decisions = project_root / PROJECT_MEMORY_DIRNAME / DECISIONS_FILENAME
    if not decisions.exists():
        decisions.parent.mkdir(parents=True, exist_ok=True)
        decisions.write_text(DECISIONS_TEMPLATE, encoding="utf-8")
    ledger_path = project_root / PROJECT_MEMORY_DIRNAME / "task_ledger.json"
    if not ledger_path.exists():
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(ledger_path, {"version": 1, "active_task": None, "checkpoints": []})
    if path.exists():
        return False
    atomic_write_json(path, {
        "schema": SCHEMA_VERSION,
        "name": name,
        "test_command": test_command,
        # Gate name -> command, or null to disable a detected gate (project_gates, ADR-122).
        "gates": {},
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


def _registered_names(workspace: Path, attached: Optional[Dict[str, str]] = None) -> Dict[str, Path]:
    """Name to folder for every project; `attached` spares a second read of `attached.json`."""
    attached = load_attached(workspace) if attached is None else attached
    names = {name: Path(path) for name, path in attached.items()}
    root = projects_dir(workspace)
    if root.is_dir():
        for child in sorted(root.iterdir()):
            if config_path(child).is_file():
                names.setdefault(child.name, child)
    return names


def _run_git(project_root: Path, *args: str) -> "subprocess.CompletedProcess[str]":
    try:
        return subprocess.run(["git", *args], cwd=project_root, capture_output=True, text=True,
                              timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProjectError(
            f"`git {args[0]}` failed in {project_root}: {exc}",
            "every project is its own git repository, separate from AIKit's.",
            "install git and put it on PATH, then run the command again.",
        ) from exc


def _git_start(project_root: Path) -> Optional[str]:
    """
    `git init`, then commit the project's memory and instructions so a new project starts clean. Returns
    a warning when the commit could not be made (typically no git identity): the project is
    still usable, and AIKit never invents an author.
    """
    result = _run_git(project_root, "init", "--quiet")
    if result.returncode != 0:
        raise ProjectError(
            f"`git init` failed in {project_root}: {result.stderr.strip()}",
            "every project is its own git repository, separate from AIKit's.",
            "fix the git error above, then run the command again.",
        )
    stage_items = [".gitignore", "README.md", PROJECT_MEMORY_DIRNAME]
    _run_git(project_root, "add", "--", *stage_items)
    result = _run_git(project_root, "commit", "--quiet", "-m", "chore: start project with AIKit memory")
    if result.returncode != 0:
        # git's last stderr line is the cause; the lines before it are generic advice.
        cause = (result.stderr.strip().splitlines() or ["git commit failed"])[-1]
        return (f"initial commit not made ({cause}); "
                "set `git config user.name` and `user.email`, then commit `.aikit/` and `.gitignore`.")
    return None


def create_project(name: str, test_command: Optional[str] = None, workspace: Path = ROOT_DIR,
                   git_start: Optional[Callable[[Path], Optional[str]]] = None
                   ) -> Tuple[Path, Optional[str]]:
    """
    Create `projects/<name>/` as a new git repository whose first commit holds the project's
    `.aikit/` memory; returns the folder and a warning, if any. `git_start` defaults to the real
    git calls (PRINCIPLE-009 R4: a test injects a double).
    """
    git_start = git_start or _git_start
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
        write_memory(project_root, name, test_command)
        seed_readme(project_root, name, test_command)
        warning = git_start(project_root)
    except BaseException:
        # Only this call created the folder, so removing it leaves no half-made project behind.
        shutil.rmtree(project_root, ignore_errors=True)
        raise
    return project_root, warning


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


def _build_project(name: str, path: Path, attached: bool) -> Project:
    present = config_path(path).is_file()
    override = load_config(path).get("test_command") if present else None
    stacks = detect_stacks(path) if present else ()
    detected = next((s.test_command for s in stacks if s.test_command), None)
    return Project(name, path, attached, stacks,
                   override if isinstance(override, str) else detected, present)


def list_projects(workspace: Path = ROOT_DIR) -> List[Project]:
    """Every registered project, sorted by name; a vanished attached folder is reported, not dropped."""
    attached = load_attached(workspace)
    return [_build_project(name, path, name in attached)
            for name, path in sorted(_registered_names(workspace, attached).items())]


def find_project(name: str, workspace: Path = ROOT_DIR) -> Project:
    """The registered project called `name`; only that project's folder is inspected."""
    attached = load_attached(workspace)
    path = _registered_names(workspace, attached).get(name)
    if path is not None:
        return _build_project(name, path, name in attached)
    raise ProjectError(
        f"No project named '{name}'.",
        "commands act on a registered project only.",
        "run `python aikit.py list` to see the names, or `python aikit.py new <name>`.",
        exit_code=2,
    )



def project_guidelines(project_root: Path) -> List[str]:
    """The project's rule lines (`- **G-NNN** (source): rule`), oldest first; [] when it has none."""
    path = project_root / PROJECT_MEMORY_DIRNAME / GUIDELINES_FILENAME
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if re.match(r"^- \*\*G-\d{3}\*\* \(", line.strip())]


def add_guideline(project_root: Path, rule: str, source: str) -> str:
    """
    Append one rule to the project's guidelines and return its new ID. Whatever the guidelines
    gate would reject, an override of a principle above all, is refused before anything is written.
    """
    rule, source = rule.strip(), source.strip()
    if not rule or "\n" in rule or not source or any(c in source for c in "()\n"):
        raise ProjectError(
            "A guideline needs a one-line rule and a source.",
            "each rule is one identifiable line that says where it came from (PRINCIPLE-001 R4).",
            'pass the rule as one quoted line and --source user, ADR-NNN or a person\'s name.',
            exit_code=2,
        )
    path = project_root / PROJECT_MEMORY_DIRNAME / GUIDELINES_FILENAME
    with file_lock(path):
        text = path.read_text(encoding="utf-8") if path.is_file() else GUIDELINES_TEMPLATE
        used = [int(n) for n in re.findall(r"^- \*\*G-(\d{3})\*\*", text, re.M)]
        gid = f"G-{max(used, default=0) + 1:03d}"
        updated = text.rstrip("\n") + f"\n- **{gid}** ({source}): {rule}\n"
        errors = guideline_errors(updated)
        if errors:
            raise ProjectError(
                f"The guideline was not added: {'; '.join(errors)}.",
                "project guidelines add rules below AIKit's principles and can never override one "
                "(PRINCIPLE-000 R6).",
                "state the rule as a constraint the principles allow, or ask the user whether a "
                "principle itself should change.",
            )
        write_generated_file(path, updated)
    return gid


def latest_decision(project_root: Path) -> Optional[str]:
    """The last `### ADR-NNN: ...` heading in the project's decision register, if any."""
    path = project_root / PROJECT_MEMORY_DIRNAME / DECISIONS_FILENAME
    if not path.is_file():
        return None
    # The template's entry-format example sits in an HTML comment; it is not a decision.
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S)
    headings = re.findall(r"^### (ADR-\d+: .+)$", text, flags=re.M)
    return headings[-1] if headings else None
