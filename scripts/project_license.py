"""
Project license tiers (ADR-214).

A project `aikit new` creates is in the personal tier: free for personal use under the Aegean
License 1.0 (AL-1.0), with commercial use sold under the Aegean Commercial License 1.0 (ACL-1.0)
in COMMERCIAL.md. A project whose value outgrows free distribution moves to the restricted tier:
its LICENSE becomes the canonical All Rights Reserved notice (`licenses/RESTRICTED-NOTICE.md`)
naming the cutoff commit, COMMERCIAL.md (a public offer) is removed, and
`.aikit/project.json` records the cutoff. A license already granted cannot be revoked, so the
cutoff only looks forward: every version up to that commit stays under the license it carried.
"""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from scripts.disruption_recovery import atomic_write_json, file_lock
from scripts.project_publish import run_command
from scripts.project_registry import (
    LICENSE_HEADING,
    LICENSES_DIR,
    PERSONAL_LICENSE_HEADER,
    ProjectError,
    _run_git,
    config_path,
    load_config,
)
from scripts.update_knowledge_base import write_generated_file

TIER_PERSONAL = "personal"
TIER_RESTRICTED = "restricted"
# An attached project keeps whatever license it came with; AIKit does not interpret it.
TIER_UNRECORDED = "unrecorded"
RESTRICTED_NOTICE_PATH = LICENSES_DIR / "RESTRICTED-NOTICE.md"
RESTRICTED_LICENSE_HEADER = "AEGEAN RESTRICTED SOFTWARE NOTICE"
RESTRICTED_TREE_LINE = "├── LICENSE                   <- All Rights Reserved (restricted tier)"
RESTRICTED_LICENSE_SECTION = (
    f"{LICENSE_HEADING}\n\n"
    "All Rights Reserved. This project is in the Aegean restricted tier and is not licensed for "
    "use, copying or distribution; see [LICENSE](LICENSE) for the cutoff commit. Versions released "
    "before the cutoff stay under the license they were released with.\n"
)


@dataclass(frozen=True)
class LicenseState:
    tier: str
    since: Optional[str] = None
    since_commit: Optional[str] = None


def render_restricted_license(name: str, since: str, since_commit: str) -> str:
    """The canonical All Rights Reserved notice, filled for a project restricted from its cutoff on."""
    try:
        template = RESTRICTED_NOTICE_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProjectError(
            f"Cannot read {RESTRICTED_NOTICE_PATH}: {exc}",
            "the restricted tier writes the canonical Aegean notice, pinned in AIKit's licenses/.",
            "restore it from git (`git checkout -- licenses/RESTRICTED-NOTICE.md`), then retry.",
        ) from exc
    if not template.startswith(RESTRICTED_LICENSE_HEADER):
        raise ProjectError(
            f"{RESTRICTED_NOTICE_PATH} is not the Aegean restricted notice.",
            "the restricted tier writes the canonical Aegean notice, pinned in AIKit's licenses/.",
            "restore it from git (`git checkout -- licenses/RESTRICTED-NOTICE.md`), then retry.",
        )
    return template.format(project=name, since=since, commit=since_commit)


def license_state(project_root: Path) -> LicenseState:
    """The project's tier: the recorded restriction, else what its LICENSE file says."""
    recorded = load_config(project_root).get("license")
    if isinstance(recorded, dict) and recorded.get("tier") == TIER_RESTRICTED:
        return LicenseState(TIER_RESTRICTED, recorded.get("since"), recorded.get("since_commit"))
    try:
        first = (project_root / "LICENSE").read_text(encoding="utf-8").lstrip().split("\n", 1)[0]
    except OSError:
        return LicenseState(TIER_UNRECORDED)
    return LicenseState(TIER_PERSONAL if first.strip() == PERSONAL_LICENSE_HEADER else TIER_UNRECORDED)


def public_remote_refusal(project_root: Path, name: str,
                          runner: Optional[Callable] = None) -> Optional[ProjectError]:
    """
    The error that stops a push of a restricted project, or None. Only a remote GitHub reports as
    PRIVATE may receive one: a public, internal or unknown visibility is refused, because a
    restricted project must not be handed to the public (ADR-214).
    """
    if license_state(project_root).tier != TIER_RESTRICTED:
        return None
    code, output = (runner or run_command)(
        ["gh", "repo", "view", "--json", "visibility", "--jq", ".visibility"], project_root)
    visibility = output.strip().upper() if code == 0 else "UNKNOWN"
    if visibility == "PRIVATE":
        return None
    return ProjectError(
        f"'{name}' is in the restricted tier and its GitHub repository is {visibility.lower()}; "
        "the push is refused.",
        "a restricted project is All Rights Reserved and may be pushed only to a private repository.",
        "make the repository private (`gh repo edit --visibility private "
        "--accept-visibility-change-consequences`), or log in with `gh auth login` so AIKit can "
        "confirm it is private, then push again.",
        exit_code=2,
    )


def _restricted_readme(text: str, newline: str) -> str:
    """`text` with its tree's licensing lines and its License section switched to the restricted tier."""
    lines = [RESTRICTED_TREE_LINE if line.startswith("├── LICENSE ") else line
             for line in text.split(newline) if not line.startswith("├── COMMERCIAL.md")]
    text = "\n".join(lines)
    section = re.search(rf"^{re.escape(LICENSE_HEADING)}\n.*?(?=^## |\Z)", text, re.M | re.S)
    if section is None:
        text = text.rstrip("\n") + "\n\n" + RESTRICTED_LICENSE_SECTION
    else:
        tail = "\n" if section.end() < len(text) else ""
        text = text[:section.start()] + RESTRICTED_LICENSE_SECTION + tail + text[section.end():]
    return text.replace("\n", newline)


def restrict_project(project_root: Path, name: str, today: Optional[str] = None,
                     runner: Optional[Callable] = None) -> LicenseState:
    """
    Move a project to the restricted tier at its current commit; returns the recorded state. A
    project already restricted keeps its first cutoff. Nothing is committed: the change is left in
    the working tree for review. A project without a commit has nothing to cut off, so it is refused
    before any file changes.
    """
    current = license_state(project_root)
    if current.tier == TIER_RESTRICTED:
        return current
    head = (runner or _run_git)(project_root, "rev-parse", "--verify", "HEAD")
    commit = (head.stdout or "").strip()
    if head.returncode != 0 or not commit:
        raise ProjectError(
            f"'{name}' has no commit to record as the cutoff.",
            "the restricted tier names the last commit released under the earlier license, so it "
            "is clear which versions keep that license.",
            "commit the project's current state, then run the command again.",
        )
    state = LicenseState(TIER_RESTRICTED, today or time.strftime("%Y-%m-%d"), commit)
    write_generated_file(project_root / "LICENSE",
                         render_restricted_license(name, state.since, state.since_commit))
    (project_root / "COMMERCIAL.md").unlink(missing_ok=True)
    readme = project_root / "README.md"
    if readme.is_file():
        with open(readme, encoding="utf-8", newline="") as handle:
            text = handle.read()
        newline = "\r\n" if "\r\n" in text else "\n"
        write_generated_file(readme, _restricted_readme(text, newline), newline="")
    path = config_path(project_root)
    with file_lock(path):
        config = load_config(project_root)
        config["license"] = {"tier": state.tier, "since": state.since,
                             "since_commit": state.since_commit}
        atomic_write_json(path, config)
    return state
