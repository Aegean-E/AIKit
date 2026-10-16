#!/usr/bin/env python3
"""
Principles Auto-Sync Tool (PRINCIPLE-017)
Generates every always-injected Tier 1 target - including AGENTS.md - from the single Tier 2
source of truth in GUIDELINES.md, enforces principle schema completeness and the Tier 1 context
budget, rejects duplicate principle IDs, checks README parity, injects optional Tier 1B domain
rules, and refuses to overwrite any target it did not generate.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_MD = ROOT_DIR / "AGENTS.md"
GUIDELINES_MD = ROOT_DIR / "GUIDELINES.md"
README_MD = ROOT_DIR / "README.md"
DOMAIN_RULES_PATH = ROOT_DIR / ".agents" / "rules" / "domain.md"

# Tier 1 budget model (PRINCIPLE-001 R4/R6). One unit - estimated tokens - with no dominated
# thresholds: a former 7,200-char "warn" branch sat ahead of the token check in an if/elif
# chain and let ~1,860-token targets through with only a warning.
TARGET_TOKEN_BUDGET = 1500  # per target, INCLUDING any Tier 1B block
WARN_TOKEN_RATIO = 0.9  # advisory early warning, checked only after every violation
MAX_DOMAIN_CHARS = 1200  # Tier 1B allowance (~300 tokens) that universal rules must leave free
# Floor that catches a truncated or mis-parsed SSOT; raise it whenever a principle is added.
MIN_PRINCIPLES = 19

# Single source of truth for the principle corpus; every Tier 1 target is generated from it.
# AGENTS.md used to be this file, but tools following the AGENTS.md convention auto-load it, which
# put ~15.6k real tokens of Tier 2 into always-on context. It is now a generated Tier 1 target.
SSOT_MD = GUIDELINES_MD

# Markers proving a file was written by this tool (current, then legacy pre-ADR-048 headers).
# Anything else is hand-authored and must never be overwritten by a sync.
GENERATED_MARKERS = ("Generated from `", "(Tier 1 Invariants)")


def is_generated_target(text: str) -> bool:
    """True when `text` carries this tool's generated-file header (current or legacy)."""
    return any(marker in text for marker in GENERATED_MARKERS)


def estimate_tokens(text: str) -> int:
    """
    Estimate tokens as chars // 4.

    Calibrated rather than assumed: against OpenAI's cl100k_base and o200k_base tokenizers this
    corpus measures ~4.2 chars/token, so the estimate over-counts by ~6% and errs conservative.
    Other vendors' tokenizers vary; the margin is the reason a simple ratio is acceptable.
    """
    return len(text) // 4


def fsync_dir(dir_path: Path) -> None:
    """Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).

    No-op on win32, which exposes no directory handle to sync. Kept local to preserve this
    script's standalone clone-and-run execution (PRINCIPLE-011) with zero cross-script imports.
    """
    if sys.platform == "win32":
        return
    fd = None
    try:
        fd = os.open(str(dir_path), os.O_RDONLY)
        os.fsync(fd)
    except OSError as e:
        sys.stderr.write(f"[WARN] Could not fsync directory {dir_path}: {e}\n")
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def load_tier_1b_domain_rules(domain_path: Optional[Path] = None) -> str:
    """Load project-specific domain rules from .agents/rules/domain.md if present (PRINCIPLE-001, PRINCIPLE-017)."""
    path = domain_path or DOMAIN_RULES_PATH
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return ""
    if len(content) > MAX_DOMAIN_CHARS:
        raise ValueError(
            f"[PRINCIPLE-001 BUDGET EXCEEDED] Tier 1B domain rules in {path} "
            f"({len(content)} chars) exceed {MAX_DOMAIN_CHARS} char ceiling (~300 tokens)."
        )
    return content


def append_domain_rules(lines: List[str], domain_rules: str):
    """Helper to append Tier 1B domain rules to prompt targets."""
    if not domain_rules:
        return
    lines.append("---")
    lines.append("")
    lines.append("## Project Domain Invariants (Tier 1B):")
    lines.append(domain_rules)
    lines.append("")


def parse_principles(agents_file: Path, strict: bool = True) -> List[Dict]:
    """Parse the principle SSOT, enforce strict schema validation, reject duplicate IDs, and verify monotonic lifecycle progression."""
    content = agents_file.read_text(encoding="utf-8")
    # Level-2 headings (phase sections, checklists, appendices) end a principle's block. Without
    # this bound the last principle swallowed everything after it, so text in a trailing
    # checklist could be misread as part of PRINCIPLE-019.
    section_starts = [m.start() for m in re.finditer(r"^## ", content, re.M)]
    phase_pattern = r"##\s*([^\n]*Phase\s*(\d+)[:\s]*([^\n]*))"
    phase_matches = list(re.finditer(phase_pattern, content))

    pattern = r"### (PRINCIPLE-\d+):\s*([^\n]+)"
    matches = list(re.finditer(pattern, content))
    principles = []
    seen_pids = set()

    for i, match in enumerate(matches):
        pid = match.group(1).strip()
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        later_sections = [s for s in section_starts if start < s < end]
        if later_sections:
            end = later_sections[0]
        block = content[start:end]

        concept_match = re.search(r"- \*\*Concept\*\*:\s*([^\n]+)", block)
        invariant_match = re.search(r"- \*\*Invariant\*\*:\s*([^\n]+)", block)
        rules_match = re.search(r"- \*\*Rules\*\*:\s*\n\s*1\.", block)

        if strict:
            if pid in seen_pids:
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] Duplicate principle ID detected: {pid}")
            seen_pids.add(pid)
            if not title:
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} has an empty title.")
            if not concept_match or not concept_match.group(1).strip():
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Concept**:' section.")
            if not invariant_match or not invariant_match.group(1).strip():
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Invariant**:' capsule.")
            if not rules_match:
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Rules**:' section with numbered rules.")
        else:
            seen_pids.add(pid)

        concept = concept_match.group(1).strip() if concept_match else ""
        invariant = invariant_match.group(1).strip() if invariant_match else concept

        # Determine phase based on preceding phase header
        principle_phase_num = 0
        principle_phase_name = ""
        for pm in phase_matches:
            if pm.start() < match.start():
                principle_phase_num = int(pm.group(2))
                principle_phase_name = pm.group(1).strip()
            else:
                break

        principles.append({
            "id": pid,
            "title": title,
            "concept": concept,
            "invariant": invariant,
            "phase_num": principle_phase_num,
            "phase_name": principle_phase_name,
        })

    # Continuous Sequence Audit: validate monotonic lifecycle progression (PRINCIPLE-002)
    if strict:
        if len(principles) < MIN_PRINCIPLES:
            raise ValueError(f"[PRINCIPLE-002 VIOLATION] Expected at least {MIN_PRINCIPLES} principles, found {len(principles)}.")

        current_phase = 1
        for p in principles:
            phase = p.get("phase_num", 0)
            if phase < current_phase:
                raise ValueError(
                    f"[PRINCIPLE-002 VIOLATION] Phase inversion detected at {p['id']}: "
                    f"assigned to Phase {phase}, but prior principles already reached Phase {current_phase}."
                )
            current_phase = phase

        if current_phase != 5:
            raise ValueError(f"[PRINCIPLE-002 VIOLATION] Principles progression did not reach Phase 5 (ended at Phase {current_phase}).")

    return principles


def validate_triad_consistency(
    principles: List[Dict],
    readme_file: Path = README_MD,
) -> List[str]:
    """
    Verify the documentation triad's public leg: README.md lists every principle (PRINCIPLE-017).

    This once also compared titles between AGENTS.md and GUIDELINES.md, because the rules lived in
    two hand-maintained copies. That check could only ever catch heading drift, never body drift,
    and ~6 rules had already diverged between the copies. With a single SSOT there is no second
    copy to compare; generated targets are covered by the freshness gate instead.
    """
    errors = []
    if not readme_file.exists():
        errors.append(f"README.md missing at {readme_file}")
        return errors

    r_content = readme_file.read_text(encoding="utf-8")
    listed = [p["id"] for p in principles if p["id"] in r_content]
    # A README that documents no principles at all is an adopter's product README, not drift:
    # forcing every adopting project to list AIKit's principle IDs blocked their first sync.
    # A README that documents SOME principles must document all of them.
    if listed:
        errors.extend(f"{p['id']} missing from README.md" for p in principles if p["id"] not in listed)
    return errors


# Every always-injected Tier 1 target: repo-relative path -> heading. One renderer keeps all
# targets in lock-step; five near-identical generators previously had to be edited in parallel,
# and the header text they shared had drifted into contradicting PRINCIPLE-001.
TIER1_TARGETS: Dict[str, str] = {
    # Auto-loaded by tools following the AGENTS.md convention (e.g. OpenAI Codex, GitHub Copilot's
    # coding agent), so it must be a budgeted Tier 1 file, never the full specification.
    "AGENTS.md": "# Agent Instructions (Tier 1)",
    "GEMINI.md": "# Gemini Instructions (Tier 1)",
    ".agents/rules/principles.md": "# Workspace Agent Rules (Tier 1)",
    "CLAUDE.md": "# Claude Instructions (Tier 1)",
    ".cursorrules": "# Cursor Rules (Tier 1)",
    ".github/copilot-instructions.md": "# Copilot Instructions (Tier 1)",
}


def tier1_title(title: str) -> str:
    """Drop a trailing parenthetical subtitle in Tier 1; the full title stays in Tier 2."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()


def render_tier1_target(heading: str, principles: List[Dict], domain_rules: str = "") -> str:
    """
    Render one always-injected Tier 1 target (PRINCIPLE-001 R1/R3, PRINCIPLE-017 R2).

    The header deliberately says *when* to read Tier 2, not merely *that* it exists. The former
    "Strictly follow all principles defined in AGENTS.md and GUIDELINES.md" invited agents to
    load ~27k tokens of Tier 2 up front - the exact bloat PRINCIPLE-001 exists to prevent. It also
    marks the file as generated, so a hand edit is not silently overwritten by the next sync.
    """
    lines = [
        heading,
        "",
        f"> Generated from `{SSOT_MD.name}` by `scripts/sync_principles.py`; edit the source, not this file.",
        "> Capsules are binding. On a boundary, failure or ambiguity, slice-view `GUIDELINES.md` "
        "(grep `### PRINCIPLE-XXX:`); never load it whole.",
        "",
        "## Core Principles",
    ]
    for p in principles:
        label = f"{p['id']} {tier1_title(p['title'])}"
        summary = p.get("invariant") or p.get("concept")
        # Plain labels: bold markers are decoration (PRINCIPLE-001 R7), ~4 chars x every line.
        lines.append(f"- {label}: {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def audit_tier1_budget(principles: List[Dict], domain_rules: str = "") -> int:
    """
    Enforce the Tier 1 context budget on every target (PRINCIPLE-001 R4/R6/R9).

    Two blocking checks, evaluated BEFORE the advisory warning so a warning can never shadow a
    violation:
      1. Total: the rendered target, including any Tier 1B block, must fit TARGET_TOKEN_BUDGET.
      2. Tier 1B headroom: with no domain rules loaded, the universal rules must still leave room
         for a FULL MAX_DOMAIN_CHARS block. Without this, the kit can grow until an adopter who
         follows PRINCIPLE-017 R6 and copies the shipped template is blocked by AIKit's own
         footprint - which is exactly what happened once the token target became enforced.

    Returns the number of violations; each carries a What/Why/Fix diagnostic.
    """
    violations = 0
    warn_at = int(TARGET_TOKEN_BUDGET * WARN_TOKEN_RATIO)
    full_tier1b = "x" * MAX_DOMAIN_CHARS
    print("\n--- Context Budget Audit (PRINCIPLE-001) ---")
    for rel, heading in TIER1_TARGETS.items():
        name = Path(rel).name
        tokens = estimate_tokens(render_tier1_target(heading, principles, domain_rules))
        reserved = estimate_tokens(render_tier1_target(heading, principles, full_tier1b))
        # Tokens a Tier 1B block could still use once the universal rules are in place.
        tier1b_room = TARGET_TOKEN_BUDGET - reserved + MAX_DOMAIN_CHARS // 4
        if tokens > TARGET_TOKEN_BUDGET:
            violations += 1
            print(f"[TOKEN EXCEEDED] {name}: ~{tokens} tokens > {TARGET_TOKEN_BUDGET}-token Tier 1 budget")
        elif not domain_rules and reserved > TARGET_TOKEN_BUDGET:
            violations += 1
            print(f"[TIER 1B HEADROOM] {name}: ~{tokens} tokens leaves room for only "
                  f"~{max(tier1b_room, 0)} of the promised ~{MAX_DOMAIN_CHARS // 4} Tier 1B tokens")
        elif tokens >= warn_at:
            print(f"[BUDGET WARN] {name}: ~{tokens} tokens >= {warn_at} ({int(WARN_TOKEN_RATIO * 100)}% of budget)")
        else:
            print(f"[BUDGET PASS] {name}: ~{tokens} tokens (Tier 1B room: ~{tier1b_room} tokens)")

    if violations:
        sys.stderr.write(
            f"\n[ERROR] {violations} target(s) breach the Tier 1 context budget (PRINCIPLE-001).\n"
            f"Why: always-injected rules cost context on every turn in every IDE, and universal "
            f"rules must leave the full ~{MAX_DOMAIN_CHARS // 4}-token Tier 1B allowance free.\n"
            f"Fix: condense capsule narrative (never mechanisms, numbers or tool names) until each "
            f"target is <= {TARGET_TOKEN_BUDGET} est. tokens including a full Tier 1B block.\n"
        )
    return violations


def sync_all(
    check_only: bool = False,
    exit_on_mismatch: bool = True,
    domain_path: Optional[Path] = None,
    readme_file: Path = README_MD,
) -> int:
    """
    Generate every always-injected Tier 1 target from the principle SSOT.

    Returns the number of problems found - 0 means success in both write and check modes. With
    `exit_on_mismatch=True` (the CLI) any problem exits 1 instead of returning.
    """
    if not SSOT_MD.exists():
        print(f"Error: Master file {SSOT_MD} not found.")
        if exit_on_mismatch:
            sys.exit(1)
        return 1

    try:
        principles = parse_principles(SSOT_MD, strict=True)
    except ValueError as schema_error:
        # Distinguish an unmigrated pre-ADR-048 layout (rules still in AGENTS.md) from a genuine
        # schema defect, and never surface either as a raw traceback (PRINCIPLE-011 R6).
        legacy = False
        if AGENTS_MD.exists() and not is_generated_target(AGENTS_MD.read_text(encoding="utf-8")):
            try:
                legacy = bool(parse_principles(AGENTS_MD, strict=True))
            except ValueError:
                legacy = False
        if legacy:
            sys.stderr.write(
                f"[MIGRATION REQUIRED] The principles still live in AGENTS.md (pre-ADR-048 layout).\n"
                f"Why: {SSOT_MD.name} is now the single source of truth and AGENTS.md is generated, "
                f"because AGENTS.md-convention agents auto-load it as always-on context.\n"
                f"Fix: move each '### PRINCIPLE-XXX:' section (Concept/Invariant/Rules) from AGENTS.md "
                f"into {SSOT_MD.name}, delete AGENTS.md, then re-run this script to regenerate it.\n"
            )
        else:
            sys.stderr.write(
                f"[SCHEMA ERROR] {schema_error}\n"
                f"Why: every principle in {SSOT_MD.name} needs '### PRINCIPLE-XXX:', Concept, Invariant "
                f"and numbered Rules (PRINCIPLE-017 R1).\n"
                f"Fix: complete the section named above, then re-run.\n"
            )
        if exit_on_mismatch:
            sys.exit(1)
        return 1
    print(f"Parsed {len(principles)} active principles from {SSOT_MD.name}:")
    for p in principles:
        print(f" - {p['id']}: {p['title']}")

    # Documentation triad, public leg: README.md must list every principle in the SSOT.
    triad_errors = validate_triad_consistency(principles, readme_file=readme_file)
    if triad_errors:
        # ASCII bullets: this CLI does not reconfigure stdout, and '•' printed as garbage on cp1254.
        err_msg = "\n".join([f"  - {e}" for e in triad_errors])
        print(f"\n[TRIAD DRIFT DETECTED]:\n{err_msg}")
        if exit_on_mismatch:
            sys.exit(1)
        return len(triad_errors)
    else:
        readme_text = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""
        if any(p["id"] in readme_text for p in principles):
            print(f"[OK] Verified README.md lists every principle in {SSOT_MD.name}")
        else:
            # Mode transparency (PRINCIPLE-011 R3): say why the check did not apply.
            print("[INFO] README.md documents no principles (adopter README); parity check not applicable")

    domain_rules = load_tier_1b_domain_rules(domain_path)
    if domain_rules:
        print(f"[LOADED] Injected Tier 1B domain rules ({len(domain_rules)} chars)")

    targets = {
        ROOT_DIR / rel: render_tier1_target(heading, principles, domain_rules)
        for rel, heading in TIER1_TARGETS.items()
    }

    budget_violations = audit_tier1_budget(principles, domain_rules)
    if budget_violations > 0:
        if exit_on_mismatch:
            sys.exit(1)
        return budget_violations

    # Never overwrite a file this tool did not generate, and decide that for EVERY target before
    # writing ANY, so a protected file cannot leave a half-synced tree (PRINCIPLE-013 R6). This
    # protects an adopter's own CLAUDE.md, and a pre-ADR-048 AGENTS.md that still holds the rules.
    foreign = []
    for target_path, expected_content in targets.items():
        if target_path.exists():
            current = target_path.read_text(encoding="utf-8")
            if current.strip() != expected_content.strip() and not is_generated_target(current):
                foreign.append(str(target_path.relative_to(ROOT_DIR)))
    if foreign:
        sys.stderr.write(
            f"\n[PROTECTED] Refusing to overwrite hand-authored file(s): {', '.join(foreign)}\n"
            f"Why: sync only overwrites files it generated, so your own instructions are never lost. "
            f"Older AIKit layouts kept the full rules in AGENTS.md; AGENTS.md is now generated from "
            f"{SSOT_MD.name}.\n"
            f"Fix: move project-specific instructions into .agents/rules/domain.md (Tier 1B, "
            f"<={MAX_DOMAIN_CHARS} chars) and principle changes into {SSOT_MD.name}, then delete or "
            f"rename the file(s) above and re-run.\n"
        )
        if exit_on_mismatch:
            sys.exit(1)
        return len(foreign)

    mismatches = 0
    for target_path, expected_content in targets.items():
        if not check_only:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            current_content = target_path.read_text(encoding="utf-8")
            if current_content.strip() == expected_content.strip():
                print(f"[OK] Synced: {target_path.relative_to(ROOT_DIR)}")
                continue

        mismatches += 1
        if check_only:
            print(f"[OUT OF SYNC]: {target_path.relative_to(ROOT_DIR)}")
        else:
            # Atomic fsync write (PRINCIPLE-006, PRINCIPLE-013)
            tmp_target = target_path.with_suffix(target_path.suffix + f".tmp_{os.getpid()}")
            with open(tmp_target, "w", encoding="utf-8") as f:
                f.write(expected_content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_target, target_path)
            fsync_dir(target_path.parent)
            print(f"[UPDATED]: {target_path.relative_to(ROOT_DIR)}")

    if check_only and mismatches > 0:
        print(f"\n{mismatches} file(s) out of sync with {SSOT_MD.name}.")
        if exit_on_mismatch:
            sys.exit(1)
        return mismatches

    print(f"\nAll {len(targets)} AI guideline targets are synchronized successfully "
          f"({mismatches} updated).")
    # The return value always counts PROBLEMS, so 0 means success in every mode. It previously
    # returned the number of files updated in write mode, making a successful sync look like a
    # failure to any programmatic caller.
    return 0


def print_help():
    """Print command line usage for sync_principles.py."""
    print("""AIKit Principles Auto-Sync Tool (PRINCIPLE-017)

Usage:
  py scripts/sync_principles.py [OPTIONS]

Options:
  --check          Verify that all guideline targets are fresh without modifying files (exits 1 on drift)
  --domain <path>  Specify custom path to Tier 1B domain rules file (default: .agents/rules/domain.md)
  -h, --help       Show this help message and exit
""")


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print_help()
        sys.exit(0)

    _known = {"--check", "--domain", "--help", "-h"}
    _argv = sys.argv[1:]
    _unknown = []
    _i = 0
    while _i < len(_argv):
        _tok = _argv[_i]
        if _tok.startswith("-"):
            if _tok not in _known:
                _unknown.append(_tok)
            elif _tok == "--domain":
                _i += 1  # consume the path value
        _i += 1
    if _unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(_unknown)}", file=sys.stderr)
        print("Why: unrecognized flags would otherwise trigger an unintended full rule rewrite.", file=sys.stderr)
        print("Fix: run 'py scripts/sync_principles.py --help' to list valid options.", file=sys.stderr)
        sys.exit(2)

    check_mode = "--check" in sys.argv
    custom_domain = None
    if "--domain" in sys.argv:
        try:
            idx = sys.argv.index("--domain")
            custom_domain = Path(sys.argv[idx + 1])
        except (IndexError, ValueError):
            sys.stderr.write("Error: --domain requires a file path argument.\n")
            sys.exit(1)

    sync_all(check_only=check_mode, exit_on_mismatch=True, domain_path=custom_domain)
