"""
Publish a project to its own GitHub repository (ADR-134).

`python aikit.py publish <name>` creates a private repository named after the project with the
GitHub CLI and pushes the project's committed history to it; a project that already has an
`origin` is pushed there instead. Nothing is uploaded unless the project has a commit, `gh` is
logged in, and a secret scan of every file the project tracks is clean (PRINCIPLE-019). Pushes are
never forced (PRINCIPLE-018 R4).
"""

import re
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


def _clean_markdown_line(raw: str) -> str:
    """Strip markdown formatting, badges, and html tags from a single line."""
    line = re.sub(r"<!--.*?-->", "", raw)
    line = re.sub(r"<[^>]+>", "", line)
    # Strip clickable badges/images: [![alt](img_url)](link_url)
    line = re.sub(r"\[\s*!\[.*?\](?:\(.*?\)|\[.*?\])\s*\](?:\(.*?\)|\[.*?\])", "", line)
    # Strip standalone images and badges: ![alt](url) or ![alt][ref]
    line = re.sub(r"!\[.*?\](?:\(.*?\)|\[.*?\])", "", line)
    # Strip any empty links: [](url)
    line = re.sub(r"\[\s*\](?:\(.*?\)|\[.*?\])", "", line)
    # Replace markdown links [text](url) with text
    line = re.sub(r"\[([^\]]+)\](?:\(.*?\)|\[.*?\])", r"\1", line)
    # Remove markdown formatting characters
    line = line.replace("**", "").replace("*", "").replace("`", "").replace("~~", "")
    return line.lstrip(">*- \t").strip()


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
    has_header = any(line.strip().startswith("#") for line in content.splitlines())
    past_header = not has_header
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
        clean = _clean_markdown_line(stripped)
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
        lines = config_file.read_text(encoding="utf-8", errors="replace").splitlines()
        in_origin = False
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith(("#", ";")):
                continue
            if line.startswith("[") and line.endswith("]"):
                header = line[1:-1].strip()
                normalized_header = re.sub(r"\s+", " ", header)
                in_origin = (normalized_header == 'remote "origin"')
                continue
            if in_origin and "=" in line:
                key, val = line.split("=", 1)
                if key.strip() == "url":
                    return val.strip()
    except OSError:
        return None

    return None


def push_range(project_root: Path, run: Runner) -> str:
    """The commits a push uploads: those past the upstream, or the whole history without one."""
    return "@{u}..HEAD" if run(["git", "rev-parse", "--verify", "@{u}"], project_root)[0] == 0 else "HEAD"


def scan_refusal(project_root: Path, rev_range: str, run: Runner) -> Optional[str]:
    """
    Scan every line the commits in `rev_range` add, the exact content a push uploads; returns the
    refusal triad when the scan does not pass. Scanning the working tree let a key that was
    committed and then deleted in an uncommitted edit through (ADR-145).
    """
    code, output = run([sys.executable, str(SECRETS_CLI), "--workspace", str(project_root),
                        "--commits", rev_range], project_root)
    if code == 0:
        return None
    return _triad(f"the secret scan of the commits to upload ({rev_range}) did not pass; nothing was "
                  f"pushed.\n{output[-800:]}",
                  "a credential pushed to GitHub must be revoked, not just deleted (PRINCIPLE-019 R6).",
                  "revoke any real credential, rewrite the commits that add it (the scan names each line), "
                  "or mark a false positive with an 'aikit:allow-secret' comment, then push again.")


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

    # If HEAD cannot be resolved (no commits made yet), nothing to push
    if run(["git", "rev-parse", "--verify", "HEAD"], project_root)[0] != 0:
        return 0, ""

    # Check whether unpushed commits exist ahead of upstream
    code_up, _ = run(["git", "rev-parse", "--verify", "@{u}"], project_root)
    if code_up == 0:
        code_diff, diff_out = run(["git", "log", "@{u}..HEAD", "--oneline"], project_root)
        if code_diff == 0 and not diff_out.strip():
            return 0, ""
        push_cmd, rev_range = ["git", "push", "origin", "HEAD"], "@{u}..HEAD"
    else:
        push_cmd, rev_range = ["git", "push", "-u", "origin", "HEAD"], "HEAD"

    refusal = scan_refusal(project_root, rev_range, run)
    if refusal:
        return 1, refusal
    code_push, push_out = run(push_cmd, project_root)
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
    code, origin = run(["git", "remote", "get-url", "origin"], project_root)
    has_origin = code == 0 and bool(origin.strip())
    refusal = scan_refusal(project_root, push_range(project_root, run) if has_origin else "HEAD", run)
    if refusal:
        return 1, refusal
    notes = []
    if run(["git", "status", "--porcelain"], project_root)[1].strip():
        notes.append("Note: uncommitted changes stay local; commit them and publish again to upload them.")

    desc = extract_readme_description(project_root)

    if has_origin:
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

