"""
Mechanical UI proofs for the opt-in UI guard (ADR-159).

The snapshot layer turns a project-declared inventory command's output into sorted,
deduplicated lines, so a lost control or handler is a removed line; the style layer
flags hardcoded color and font literals in added surface lines outside the theme
paths the contract declares. Both are pure and deterministic: no I/O, no framework.

PRINCIPLE-003, PRINCIPLE-006, PRINCIPLE-014.
"""

import fnmatch
import os
import re
from typing import List, Sequence, Tuple

MAX_REPORTED_ENTRIES = 8
STYLE_PATTERNS = (
    re.compile(r"#[0-9a-fA-F]{6}\b"),
    re.compile(r"#[0-9a-fA-F]{3}\b"),
    re.compile(r"\brgba?\("),
    re.compile(r"\b(font(?:_size|_name|_family)?)\s*="),
)


def matches_pattern(path: str, patterns: Sequence[str]) -> bool:
    """One relative path against contract patterns; `dir/**` covers the tree."""
    candidate = path.replace("\\", "/")
    if os.name == "nt":
        candidate = candidate.casefold()
    for pattern in patterns:
        normalized = pattern.replace("\\", "/")
        if os.name == "nt":
            normalized = normalized.casefold()
        if normalized.endswith("/**"):
            base = normalized[:-3]
            if candidate == base or candidate.startswith(base + "/"):
                return True
        elif fnmatch.fnmatchcase(candidate, normalized):
            return True
    return False


def snapshot_lines(output: str) -> List[str]:
    """Sorted, deduplicated non-empty lines of a UI inventory dump."""
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def inventory_findings(baseline: Sequence[str], current: Sequence[str],
                       allowed: Sequence[str]) -> List[str]:
    """Removed inventory entries are findings unless an allowed pattern matches."""
    present = set(current)
    removed = [line for line in baseline
               if line not in present
               and not any(fnmatch.fnmatchcase(line, pattern) for pattern in allowed)]
    if not removed:
        return []
    shown = "; ".join(removed[:MAX_REPORTED_ENTRIES])
    entries = "entry" if len(removed) == 1 else "entries"
    return [f"UI snapshot proof lost {len(removed)} {entries}: {shown}"]


def style_findings(added: Sequence[Tuple[str, int, str]],
                   theme_paths: Sequence[str]) -> List[str]:
    """Hardcoded color and font literals in added surface lines are findings.

    Without declared theme paths the lint is off: nothing is outside a theme.
    """
    if not theme_paths:
        return []
    findings: List[str] = []
    for path, number, text in added:
        if matches_pattern(path, theme_paths):
            continue
        for pattern in STYLE_PATTERNS:
            match = pattern.search(text)
            if match:
                literal = match.group(1) if match.lastindex else match.group(0)
                findings.append(f"style literal '{literal}' outside theme paths: "
                                f"{path}:{number}")
                break
    return findings
