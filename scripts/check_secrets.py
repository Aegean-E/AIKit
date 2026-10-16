#!/usr/bin/env python3
"""
Secret & Sensitive Data Hygiene Scanner (PRINCIPLE-019)

Secret leakage is the one defect class with no clean rollback: once a credential is pushed,
logged, or sent to a third party, it must be rotated, not reverted. This scanner is therefore a
*pre*-commit gate, the fourth leg of the PRINCIPLE-018 Rule 3 delivery triad.

It scans two surfaces that AI agents leak through in practice:

  1. Staged content (`git diff --cached`), or named files, or the whole tracked tree.
  2. Agent working memory - `.agents/task_ledger.json` free-text fields and the dogfood log.
     This repository's own PRINCIPLE-007 workflow persists `--why` / `--benefits` / `--risks` /
     `--mitigation` straight into a git-tracked ledger, so an agent that quotes a key while
     explaining its reasoning commits that key to history permanently.

Detection is pattern-first (known credential shapes have near-zero false-positive rates) with a
conservative high-entropy fallback for assignment-shaped lines only. Deliberate exceptions use an
inline `# aikit:allow-secret` pragma or the ALLOWLIST_SUBSTRINGS set - never a silenced scanner.

Zero external dependencies (standard library only).

Usage:
  python scripts/check_secrets.py [--staged | --all | --file <path>] [--verbose]
Exit codes:
  0 clean    1 potential secret found    2 CLI argument misuse
"""

import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
LEDGER_PATH = ROOT_DIR / ".agents" / "task_ledger.json"
DOGFOOD_LOG = ROOT_DIR / ".agents" / "dogfood_last_run.log"

PRAGMA = "aikit:allow-secret"
PROC_TIMEOUT = 15

# Known credential shapes. Pattern-first detection keeps false positives near zero, which is what
# keeps the gate trusted; an untrusted gate gets bypassed and protects nothing.
SECRET_PATTERNS: Tuple[Tuple[str, str], ...] = (
    ("AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    ("GitHub fine-grained token", r"\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
    ("Slack token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    ("Google API key", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("Stripe secret key", r"\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{20,}\b"),
    ("OpenAI-style API key", r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}\b"),
    ("Anthropic-style API key", r"\bsk-ant-[A-Za-z0-9_\-]{32,}\b"),
    ("JSON Web Token", r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    ("Private key block", r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----"),
    ("Password in URL", r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^/\s:@]+:[^/\s:@]+@"),
    ("Authorization header value", r"\bAuthorization\s*[:=]\s*[\"']?(?:Bearer|Basic)\s+[A-Za-z0-9._\-=/+]{16,}"),
    ("Hardcoded password assignment", r"\b(?:password|passwd|secret|api_key|apikey|access_token|auth_token|private_key)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"),
)

# A value that is wholly an interpolation or a template placeholder is an indirection, not a
# literal credential. This must be honoured by the pattern detectors too, not only the entropy
# fallback: `password = "${DB_PASS}"` is correct code, and a scanner that blocks correct code
# gets bypassed, which protects nothing.
INTERPOLATION_ONLY_RE = re.compile(
    r"""[:=]\s*["']?\s*(?:\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*|\{\{[^}]*\}\}|"""
    r"""\{[A-Za-z_][A-Za-z0-9_]*\}|%\([^)]*\)s|<[^>]*>)\s*["']?\s*$"""
)

# Assignment-shaped lines whose value may be a raw secret; entropy is only applied here.
ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH)[A-Z0-9_]*)\s*[:=]\s*[\"']?([^\s\"',;]{16,})[\"']?"
)

# Allowlisting is risk-tiered, because a weak word must never veto a high-confidence match.
# A red-check caught this: "AKIAIOSFODNN7EXAMPLE" was missed purely because the line contained
# the word "example", which would equally have hidden a live key on an "# example usage" line.
#
# STRONG markers are unambiguous placeholders and the explicit pragma: they suppress everything.
# WEAK markers suppress only the low-confidence entropy fallback, never a pattern match.
STRONG_ALLOWLIST = frozenset({
    PRAGMA, "your-key-here", "your_key_here", "<your", "placeholder", "changeme",
    "redacted", "<redacted>", "xxxxxxxx", "0000000000",
})
WEAK_ALLOWLIST = frozenset({"example", "sample", "dummy", "fake", "test-token"})

# Retained for callers and tests that want the full token set.
ALLOWLIST_SUBSTRINGS = STRONG_ALLOWLIST | WEAK_ALLOWLIST

# Paths whose content is documentation *about* secrets rather than secrets.
SKIP_PATH_PARTS = ("knowledge/decisions.md", "AGENTS.md", "GUIDELINES.md", "README.md",
                   "CLAUDE.md", "GEMINI.md", ".cursorrules", "copilot-instructions.md",
                   "principles.md", "check_secrets.py", "domain.md.template")

TEXT_SUFFIXES = frozenset({
    ".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".env",
    ".sh", ".ps1", ".js", ".ts", ".rs", ".go", ".java", ".rb", ".log", "",
})


def shannon_entropy(value: str) -> float:
    """Bits of entropy per character; random credentials score high, English prose low."""
    if not value:
        return 0.0
    counts: Dict[str, int] = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())


def is_strongly_allowlisted(line: str) -> bool:
    """An explicit pragma or an unambiguous placeholder suppresses every detector."""
    lowered = line.lower()
    return any(token in lowered for token in STRONG_ALLOWLIST)


def is_weakly_allowlisted(line: str) -> bool:
    """A hint like "example" suppresses only the low-confidence entropy fallback."""
    lowered = line.lower()
    return any(token in lowered for token in WEAK_ALLOWLIST)


def scan_text(label: str, text: str) -> List[Tuple[str, int, str, str]]:
    """Return (label, line_no, detector, excerpt) for every finding in a blob of text."""
    findings: List[Tuple[str, int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if is_strongly_allowlisted(line):
            continue
        stripped = line.strip()
        if not stripped:
            continue

        if INTERPOLATION_ONLY_RE.search(line):
            continue  # the value is an indirection, not a credential

        matched = False
        for detector, pattern in SECRET_PATTERNS:
            if re.search(pattern, line):
                findings.append((label, lineno, detector, stripped[:88]))
                matched = True
                break
        if matched:
            continue

        # Conservative entropy fallback: only on assignment-shaped lines, so prose and hashes
        # committed as data do not trip the gate.
        if is_weakly_allowlisted(line):
            continue  # pattern detectors already ran; skip only the entropy fallback
        match = ASSIGNMENT_RE.search(line)
        if match:
            name, value = match.group(1), match.group(2)
            if value.startswith(("$", "{", "%", "<")) or "os.getenv" in line or "os.environ" in line:
                continue  # an indirection, not a literal
            if len(value) >= 20 and shannon_entropy(value) >= 3.8:
                findings.append((label, lineno, f"high-entropy value for {name}", stripped[:88]))
    return findings


def should_skip(path_str: str) -> bool:
    normalized = path_str.replace("\\", "/")
    return any(part in normalized for part in SKIP_PATH_PARTS)


def git_output(args: List[str]) -> Optional[str]:
    try:
        res = subprocess.run(
            ["git", *args], cwd=str(ROOT_DIR), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=PROC_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout if res.returncode == 0 else None


def scan_staged(gaps: Optional[List[str]] = None) -> List[Tuple[str, int, str, str]]:
    """Scan staged content only - the surface about to become permanent history."""
    diff = git_output(["diff", "--cached", "--unified=0"])
    if diff is None:
        if gaps is not None:
            gaps.append("git diff --cached failed, so the staged changes were not scanned")
        return []
    findings = []
    current = "<staged>"
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:].strip()
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if should_skip(current):
                continue
            findings.extend(scan_text(current, line[1:]))
    return findings


def iter_tracked_files(gaps: Optional[List[str]] = None) -> Iterable[Path]:
    listing = git_output(["ls-files"])
    if listing is None:
        if gaps is not None:
            gaps.append("git ls-files failed, so no tracked file was scanned")
        return []
    for rel in listing.splitlines():
        rel = rel.strip()
        if not rel or should_skip(rel):
            continue
        path = ROOT_DIR / rel
        if path.suffix.lower() in TEXT_SUFFIXES and path.is_file():
            yield path


def scan_all(gaps: Optional[List[str]] = None) -> List[Tuple[str, int, str, str]]:
    findings = []
    for path in iter_tracked_files(gaps):
        try:
            findings.extend(scan_text(str(path.relative_to(ROOT_DIR)),
                                      path.read_text(encoding="utf-8", errors="replace")))
        except OSError as e:
            if gaps is not None:
                gaps.append(f"{path.relative_to(ROOT_DIR)} could not be read: {e}")
    return findings


def scan_agent_memory(gaps: Optional[List[str]] = None) -> List[Tuple[str, int, str, str]]:
    """
    PRINCIPLE-019 Rule 3: agent working memory is tracked output. The ledger's free-text impact
    fields are committed, so a credential quoted while explaining reasoning becomes permanent.
    """
    findings = []
    for path in (LEDGER_PATH, DOGFOOD_LOG):
        if not path.exists():
            continue
        try:
            findings.extend(scan_text(f"agent-memory:{path.name}",
                                      path.read_text(encoding="utf-8", errors="replace")))
        except OSError as e:
            if gaps is not None:
                gaps.append(f"agent memory {path.name} could not be read: {e}")
    return findings


def run_scan(mode: str = "staged", target: Optional[Path] = None,
             verbose: bool = False) -> int:
    """Scan the requested surface plus agent memory, reporting tersely (PRINCIPLE-012 R4)."""
    print("=" * 58)
    print("SECRET & SENSITIVE DATA SCAN (PRINCIPLE-019)")
    print("=" * 58)

    gaps: List[str] = []
    if mode == "file" and target is not None:
        if not target.exists():
            print(f"[FAIL] No such file: {target}", file=sys.stderr)
            return 1
        try:
            label = str(target.resolve().relative_to(ROOT_DIR))
        except ValueError:
            label = target.name
        try:
            findings = scan_text(label, target.read_text(encoding="utf-8", errors="replace"))
        except OSError as e:
            findings, gaps = [], [f"{label} could not be read: {e}"]
        scope = label
    elif mode == "all":
        findings = scan_all(gaps)
        scope = "all tracked text files"
    else:
        findings = scan_staged(gaps)
        scope = "staged changes"

    findings.extend(scan_agent_memory(gaps))
    print(f"Scope: {scope} + agent working memory")

    # PRINCIPLE-000 R5: a scan that skipped a surface must not report clean. It used to warn,
    # print [OK] and exit 0 when git failed, so the pre-commit gate passed having scanned nothing.
    if gaps:
        print(f"[FAIL] Scan incomplete: {len(gaps)} surface(s) not scanned:")
        for gap in gaps[:12]:
            print(f"   - {gap}")
        print("   Why: an unscanned surface can hold a credential; 'clean' would be unproven.")
        print("   Fix: run inside the git worktree with `git` on PATH, or fix the file's permissions.")
        print("=" * 58)
        return 1

    if not findings:
        print("[OK] No credential patterns or high-entropy literals detected.")
        if verbose:
            print(f"      {len(SECRET_PATTERNS)} detectors active; "
                  f"{len(ALLOWLIST_SUBSTRINGS)} allowlist tokens.")
        print("=" * 58)
        return 0

    print(f"\n[FAIL] {len(findings)} potential secret(s) detected:")
    for label, lineno, detector, excerpt in findings[:12]:
        print(f"   - {label}:{lineno} [{detector}]")
        print(f"       {excerpt}")
    if len(findings) > 12:
        print(f"   ... and {len(findings) - 12} more")
    print("\n   Why: a committed credential cannot be reverted, only rotated"
          " (PRINCIPLE-019 R6).")
    print("   Fix: remove the value, supply it via an environment variable or secret store,")
    print(f"        rotate it if it was ever pushed, or mark a false positive with a"
          f" '# {PRAGMA}' pragma.")
    print("=" * 58)
    return 1


KNOWN_FLAGS = {"--staged", "--all", "--file", "--verbose", "-v", "--help", "-h"}
VALUE_FLAGS = {"--file"}

HELP_TEXT = """AIKit Secret & Sensitive Data Scanner (PRINCIPLE-019)

Usage:
  python scripts/check_secrets.py [OPTIONS]

Scans for credential patterns and high-entropy literals, plus agent working memory
(.agents/task_ledger.json free-text and the dogfood log), which is committed like any other
file and is a real leak path for agent-authored rationale.

Options:
  --staged         Scan staged changes only (default) - the surface about to become history
  --all            Scan every tracked text file
  --file <path>    Scan a single file
  --verbose, -v    Print detector and allowlist counts
  -h, --help       Show this help message and exit

False positives:
  Add a '# aikit:allow-secret' pragma on the line, or extend ALLOWLIST_SUBSTRINGS.

Exit codes:
  0  clean    1  potential secret found    2  CLI argument misuse
"""


if __name__ == "__main__":
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(HELP_TEXT, end="")
        sys.exit(0)

    unknown: List[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            if token not in KNOWN_FLAGS:
                unknown.append(token)
            elif token in VALUE_FLAGS:
                i += 1
        i += 1
    if unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Why: this scanner accepts only {', '.join(sorted(KNOWN_FLAGS))}.", file=sys.stderr)
        print("Fix: run 'python scripts/check_secrets.py --help' to list valid options.",
              file=sys.stderr)
        sys.exit(2)

    scan_mode = "all" if "--all" in argv else "staged"
    scan_target: Optional[Path] = None
    if "--file" in argv:
        idx = argv.index("--file")
        if idx + 1 >= len(argv) or argv[idx + 1].startswith("-"):
            print("[INVALID USAGE] --file requires a path argument.", file=sys.stderr)
            print("Why: there is no sensible default file to scan.", file=sys.stderr)
            print("Fix: pass '--file <path>'.", file=sys.stderr)
            sys.exit(2)
        scan_mode, scan_target = "file", Path(argv[idx + 1])

    sys.exit(run_scan(mode=scan_mode, target=scan_target,
                      verbose=("--verbose" in argv or "-v" in argv)))
