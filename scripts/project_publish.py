"""
Publish a project to its own GitHub repository (ADR-134).

`python aikit.py publish <name>` creates a private repository named after the project with the
GitHub CLI and pushes the project's committed history to it; a project that already has an
`origin` is pushed there instead. Nothing is uploaded unless the project has a commit, `gh` is
logged in, and a secret scan of every file the project tracks is clean (PRINCIPLE-019). Pushes are
never forced (PRINCIPLE-018 R4).
"""

import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from scripts.disruption_recovery import ROOT_DIR

SECRETS_CLI = ROOT_DIR / "scripts" / "check_secrets.py"
# Creating a repository and pushing a large history can take a while; past this, it is hung.
PUBLISH_TIMEOUT_SECONDS = 300

Runner = Callable[[List[str], Path], Tuple[int, str]]


def run_command(argv: List[str], cwd: Path) -> Tuple[int, str]:
    """Default runner: the command's exit code and combined output; -1 when it cannot start."""
    try:
        done = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=PUBLISH_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)
    return done.returncode, (done.stdout + done.stderr).strip()


def _triad(what: str, why: str, fix: str) -> str:
    return f"Error: {what}\nWhy: {why}\nFix: {fix}"


def extract_readme_description(project_root: Path) -> str:
    """Extract a single-line summary from the project's README.md for the GitHub description."""
    readme = project_root / "README.md"
    if not readme.is_file():
        return ""
    try:
        content = readme.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    desc_lines: List[str] = []
    past_header = False
    for line in content.splitlines():
        stripped = line.strip()
        if not past_header:
            if stripped.startswith("#"):
                past_header = True
            continue
        if not stripped:
            if desc_lines:
                break
            continue
        if stripped.startswith("#"):
            break
        clean = stripped.lstrip(">*- ").strip().replace("**", "").replace("*", "").replace("`", "")
        if clean:
            desc_lines.append(clean)
    text = " ".join(desc_lines).strip()
    return (text[:197].rstrip() + "...") if len(text) > 200 else text


def get_project_repo_url(project_root: Path, runner: Optional[Runner] = None) -> Optional[str]:
    """Return the URL of the project's 'origin' remote, or None if not configured."""
    if runner is not None:
        code, output = runner(["git", "remote", "get-url", "origin"], project_root)
        if code == 0 and output.strip():
            return output.strip()
        return None

    # Read .git/config directly: zero process spawns, pure stdlib speed (PRINCIPLE-010, PRINCIPLE-014 R3)
    git_dir = project_root / ".git"
    if not git_dir.exists():
        return None

    if git_dir.is_file():
        try:
            line = git_dir.read_text(encoding="utf-8").strip()
            if line.startswith("gitdir:"):
                target = Path(line.split(":", 1)[1].strip())
                git_dir = target if target.is_absolute() else (project_root / target).resolve()
        except OSError:
            return None

    config_file = git_dir / "config"
    if not config_file.is_file():
        return None

    try:
        import configparser
        cp = configparser.ConfigParser()
        cp.read(config_file, encoding="utf-8")
        for section in cp.sections():
            if section.strip() == 'remote "origin"' and "url" in cp[section]:
                return cp[section]["url"].strip()
    except (OSError, configparser.Error):
        return None

    return None




def auto_push_project(project_root: Path, name: str, runner: Optional[Runner] = None) -> Tuple[int, str]:
    """
    Push unpushed commits of a published project to its remote origin (PRINCIPLE-018: adaptive push).
    Returns (0, message) on success or when no push was needed; (1, triad) if push failed.
    Never forces (PRINCIPLE-018 R4).
    """
    run = runner or run_command
    url = get_project_repo_url(project_root, runner=run)
    if not url:
        return 0, ""

    # Check whether unpushed commits exist ahead of upstream
    code_up, _ = run(["git", "rev-parse", "--verify", "@{u}"], project_root)
    if code_up == 0:
        code_diff, diff_out = run(["git", "log", "@{u}..HEAD", "--oneline"], project_root)
        if code_diff == 0 and not diff_out.strip():
            return 0, ""

    code_push, push_out = run(["git", "push", "origin", "HEAD"], project_root)
    if code_push != 0:
        return 1, _triad(
            f"auto-pushing '{name}' to {url} failed.\n{push_out[-400:]}",
            "the remote refused the push or could not be reached; nothing was forced.",
            "pull remote changes or check network/credentials, then run `python aikit.py publish`."
        )
    return 0, f"[OK] Pushed '{name}' commits to {url}."


def publish_project(project_root: Path, name: str, public: bool = False,
                    runner: Optional[Runner] = None) -> Tuple[int, str]:
    """
    Upload the project's commits to its own GitHub repository; returns (exit code, report).
    `runner` defaults to real git, gh and Python calls (PRINCIPLE-009 R4: tests inject a fake).
    """
    run = runner or run_command
    if run(["git", "rev-parse", "--verify", "HEAD"], project_root)[0] != 0:
        return 1, _triad(f"project '{name}' has no commit to publish.",
                         "only committed history is uploaded.",
                         f"commit the project's work first (its gates: `python aikit.py check {name}`).")
    code, output = run([sys.executable, str(SECRETS_CLI), "--workspace", str(project_root), "--all"],
                       project_root)
    if code != 0:
        return 1, _triad(f"the secret scan of '{name}' did not pass; nothing was uploaded.\n{output[-800:]}",
                         "a credential pushed to GitHub must be revoked, not just deleted (PRINCIPLE-019 R6).",
                         "remove each finding from the files and their history, or mark a false positive "
                         "with an 'aikit:allow-secret' comment, then publish again.")
    notes = []
    if run(["git", "status", "--porcelain"], project_root)[1].strip():
        notes.append("Note: uncommitted changes stay local; commit them and publish again to upload them.")

    desc = extract_readme_description(project_root)

    code, origin = run(["git", "remote", "get-url", "origin"], project_root)
    if code == 0 and origin.strip():
        code, output = run(["git", "push", "-u", "origin", "HEAD"], project_root)
        if code != 0:
            return 1, _triad(f"pushing '{name}' to {origin.strip()} failed.\n{output[-800:]}",
                             "the remote refused the push or could not be reached; nothing is forced.",
                             "pull or fix the cause shown, then publish again.")
        if desc and run(["gh", "auth", "status"], project_root)[0] == 0:
            run(["gh", "repo", "edit", "--description", desc], project_root)
        return 0, "\n".join([f"[OK] Pushed '{name}' to {origin.strip()}.", *notes])

    if run(["gh", "auth", "status"], project_root)[0] != 0:
        return 1, _triad("the GitHub CLI is not installed or not logged in.",
                         "AIKit creates the project's repository with `gh`.",
                         "install GitHub CLI, run `gh auth login`, then publish again.")
    visibility = "--public" if public else "--private"
    desc_args = ["--description", desc] if desc else []
    code, output = run(["gh", "repo", "create", name, visibility, "--source", str(project_root),
                        "--remote", "origin", "--push", *desc_args], project_root)
    if code != 0:
        return 1, _triad(f"creating the GitHub repository '{name}' failed.\n{output[-800:]}",
                         "GitHub refused the repository, for example because the name is taken.",
                         "rename or delete the existing repository on GitHub, or add a remote yourself with "
                         "`git remote add origin <url>` in the project, then publish again.")
    url = run(["git", "remote", "get-url", "origin"], project_root)[1].strip() or output
    kind = "public" if public else "private"
    desc_note = f" with description '{desc}'" if desc else ""
    return 0, "\n".join([f"[OK] Created the {kind} repository {url}{desc_note} and pushed '{name}'.", *notes])

