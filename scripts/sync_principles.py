#!/usr/bin/env python3
"""
Principles Auto-Sync Tool (PRINCIPLE-017)
Ensures all AI assistant guideline documents remain in 100% synchronization
with the master specification in AGENTS.md, enforces principle schema completeness,
prevents duplicate principle IDs, validates exact title parity across documentation,
and injects optional Tier 1B domain rules.
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

MAX_TARGET_CHARS = 8000  # Hard ceiling per target file (PRINCIPLE-001)
WARN_TARGET_CHARS = 7200  # 90% of MAX_TARGET_CHARS (early warning threshold)
TARGET_TOKEN_BUDGET = 1500  # Tier 1 token target (PRINCIPLE-001); ~4 chars/token estimate
MAX_DOMAIN_CHARS = 1200  # ~300 tokens for Tier 1B domain rules (PRINCIPLE-001 Rule 4)


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
    """Parse AGENTS.md, enforce strict schema validation, reject duplicate IDs, and verify monotonic lifecycle progression."""
    content = agents_file.read_text(encoding="utf-8")
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
        if len(principles) < 18:
            raise ValueError(f"[PRINCIPLE-002 VIOLATION] Expected at least 18 principles, found {len(principles)}.")

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
    guidelines_file: Path = GUIDELINES_MD,
    readme_file: Path = README_MD,
) -> List[str]:
    """Verify that all principles in AGENTS.md also exist in GUIDELINES.md and README.md with matching titles (PRINCIPLE-017)."""
    errors = []
    if not guidelines_file.exists():
        errors.append(f"GUIDELINES.md missing at {guidelines_file}")
    else:
        g_content = guidelines_file.read_text(encoding="utf-8")
        for p in principles:
            pid = p["id"]
            expected_header = f"### {pid}: {p['title']}"
            if expected_header not in g_content:
                errors.append(f"{pid} heading in GUIDELINES.md does not match AGENTS.md ('{expected_header}')")

    if not readme_file.exists():
        errors.append(f"README.md missing at {readme_file}")
    else:
        r_content = readme_file.read_text(encoding="utf-8")
        for p in principles:
            pid = p["id"]
            if pid not in r_content:
                errors.append(f"{pid} missing from README.md")

    return errors


def generate_gemini_content(principles: List[Dict], domain_rules: str = "") -> str:
    lines = [
        "# AI Guidelines & Project Principles",
        "",
        "See full specification in [AGENTS.md](AGENTS.md) and [GUIDELINES.md](GUIDELINES.md).",
        "Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.",
        "",
        "## Core Principles Summary (Tier 1 Invariants):"
    ]
    for i, p in enumerate(principles, 1):
        summary = p.get("invariant") or p.get("concept")
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def generate_agents_rule_content(principles: List[Dict], domain_rules: str = "") -> str:
    lines = [
        "# Workspace AI Principles & Guidelines",
        "",
        "This rule is automatically loaded from the workspace customizations root (`.agents/rules/`).",
        "",
        "> **MANDATORY FOR ALL AI AGENTS:**",
        "> Strictly follow the core principles defined in [AGENTS.md](../../AGENTS.md) and [GUIDELINES.md](../../GUIDELINES.md).",
        "> Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.",
        "",
        "## Core Principles (Tier 1 Invariants):"
    ]
    for i, p in enumerate(principles, 1):
        summary = p.get("invariant") or p.get("concept")
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def generate_claude_content(principles: List[Dict], domain_rules: str = "") -> str:
    lines = [
        "# Claude AI Assistant Guidelines",
        "",
        "> **MANDATORY FOR CLAUDE CODE & CLAUDE ASSISTANTS:**",
        "> Strictly follow all principles and guidelines defined in [AGENTS.md](AGENTS.md) and [GUIDELINES.md](GUIDELINES.md).",
        "> Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.",
        "",
        "## Core Principles (Tier 1 Invariants):"
    ]
    for i, p in enumerate(principles, 1):
        summary = p.get("invariant") or p.get("concept")
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def generate_cursorrules_content(principles: List[Dict], domain_rules: str = "") -> str:
    lines = [
        "# Cursor AI Assistant Guidelines",
        "",
        "Strictly read, respect, and enforce all principles defined in AGENTS.md and GUIDELINES.md.",
        "Deterministic Grep Anchor: Query='### PRINCIPLE-XXX:' in GUIDELINES.md.",
        "",
        "## Core Principles Summary (Tier 1 Invariants):"
    ]
    for i, p in enumerate(principles, 1):
        summary = p.get("invariant") or p.get("concept")
        lines.append(f"{i}. {p['id']}: {p['title']}")
        lines.append(f"   - {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def generate_copilot_content(principles: List[Dict], domain_rules: str = "") -> str:
    lines = [
        "# GitHub Copilot Instructions",
        "",
        "All GitHub Copilot interactions in this repository must align with the architectural rules in `AGENTS.md` and `GUIDELINES.md`.",
        "Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.",
        "",
        "## Core Principles Summary (Tier 1 Invariants):"
    ]
    for i, p in enumerate(principles, 1):
        summary = p.get("invariant") or p.get("concept")
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary}")
    lines.append("")
    append_domain_rules(lines, domain_rules)
    return "\n".join(lines)


def sync_all(
    check_only: bool = False,
    exit_on_mismatch: bool = True,
    domain_path: Optional[Path] = None,
    guidelines_file: Path = GUIDELINES_MD,
    readme_file: Path = README_MD,
) -> int:
    """Synchronize master specification from AGENTS.md across all IDE prompt targets."""
    if not AGENTS_MD.exists():
        print(f"Error: Master file {AGENTS_MD} not found.")
        if exit_on_mismatch:
            sys.exit(1)
        return 1

    principles = parse_principles(AGENTS_MD, strict=True)
    print(f"Parsed {len(principles)} active principles from AGENTS.md:")
    for p in principles:
        print(f" - {p['id']}: {p['title']}")

    # Validate triad consistency (AGENTS.md <-> GUIDELINES.md <-> README.md)
    triad_errors = validate_triad_consistency(principles, guidelines_file=guidelines_file, readme_file=readme_file)
    if triad_errors:
        err_msg = "\n".join([f"  • {e}" for e in triad_errors])
        print(f"\n[TRIAD DRIFT DETECTED]:\n{err_msg}")
        if exit_on_mismatch:
            sys.exit(1)
        return len(triad_errors)
    else:
        print("[OK] Verified principle triad consistency across AGENTS.md, GUIDELINES.md, and README.md")

    domain_rules = load_tier_1b_domain_rules(domain_path)
    if domain_rules:
        print(f"[LOADED] Injected Tier 1B domain rules ({len(domain_rules)} chars)")

    targets = {
        ROOT_DIR / "GEMINI.md": generate_gemini_content(principles, domain_rules),
        ROOT_DIR / ".agents" / "rules" / "principles.md": generate_agents_rule_content(principles, domain_rules),
        ROOT_DIR / "CLAUDE.md": generate_claude_content(principles, domain_rules),
        ROOT_DIR / ".cursorrules": generate_cursorrules_content(principles, domain_rules),
        ROOT_DIR / ".github" / "copilot-instructions.md": generate_copilot_content(principles, domain_rules),
    }

    # Governance Frugality & Context Budget Check (PRINCIPLE-001)
    budget_violations = 0
    print("\n--- Context Budget Audit (PRINCIPLE-001) ---")
    for target_path, expected_content in targets.items():
        char_len = len(expected_content)
        est_tokens = char_len // 4
        if char_len > MAX_TARGET_CHARS:
            budget_violations += 1
            print(f"[BUDGET EXCEEDED] {target_path.name}: {char_len} chars (~{est_tokens} tokens) > {MAX_TARGET_CHARS} cap")
        elif char_len >= WARN_TARGET_CHARS:
            print(f"[BUDGET WARN] {target_path.name}: {char_len} chars (~{est_tokens} tokens) >= {WARN_TARGET_CHARS} (90% capacity)")
        elif est_tokens > TARGET_TOKEN_BUDGET:
            # Enforced, not advisory. PRINCIPLE-001 R9 requires that adding a principle be paid
            # for by condensing existing capsules, so overage must block rather than warn: an
            # advisory warning is exactly how this target came to be silently breached.
            budget_violations += 1
            print(f"[TOKEN EXCEEDED] {target_path.name}: {char_len} chars (~{est_tokens} tokens) > {TARGET_TOKEN_BUDGET}-token Tier 1 target")
        else:
            print(f"[BUDGET PASS] {target_path.name}: {char_len} chars (~{est_tokens} tokens)")

    if budget_violations > 0:
        sys.stderr.write(
            f"\n[ERROR] {budget_violations} target file(s) exceed the Tier 1 context budget "
            f"(PRINCIPLE-001).\n"
            f"Why: always-injected rules consume context on every turn in every IDE.\n"
            f"Fix: condense invariant capsules (narrative only - never mechanisms, numbers or "
            f"tool names) until every target is under {TARGET_TOKEN_BUDGET} tokens / "
            f"{MAX_TARGET_CHARS} chars.\n"
        )
        if exit_on_mismatch:
            sys.exit(1)
        return budget_violations

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
        print(f"\n{mismatches} file(s) out of sync with AGENTS.md.")
        if exit_on_mismatch:
            sys.exit(1)
        return mismatches

    print(f"\nAll {len(targets)} AI guideline targets are synchronized successfully.")
    return mismatches


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
