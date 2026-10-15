#!/usr/bin/env python3
"""
Principles Auto-Sync Tool (PRINCIPLE-017)
Ensures all AI assistant guideline documents remain in 100% synchronization
with the master specification in AGENTS.md, enforces principle schema completeness,
validates triad consistency across documentation, and injects optional Tier 1B domain rules.
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

MAX_TARGET_CHARS = 8000  # ~1,500-2,000 tokens per target file (PRINCIPLE-001)
MAX_DOMAIN_CHARS = 1200  # ~300 tokens for Tier 1B domain rules (PRINCIPLE-001 Rule 4)


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
    """Parse AGENTS.md, enforce strict schema validation, and verify monotonic lifecycle progression."""
    content = agents_file.read_text(encoding="utf-8")
    phase_pattern = r"##\s*([^\n]*Phase\s*(\d+)[:\s]*([^\n]*))"
    phase_matches = list(re.finditer(phase_pattern, content))

    pattern = r"### (PRINCIPLE-\d+):\s*([^\n]+)"
    matches = list(re.finditer(pattern, content))
    principles = []
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
            if not title:
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} has an empty title.")
            if not concept_match or not concept_match.group(1).strip():
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Concept**:' section.")
            if not invariant_match or not invariant_match.group(1).strip():
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Invariant**:' capsule.")
            if not rules_match:
                raise ValueError(f"[PRINCIPLE-017 SCHEMA VIOLATION] {pid} is missing required '- **Rules**:' section with numbered rules.")

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
    """Verify that all principles in AGENTS.md also exist in GUIDELINES.md and README.md (PRINCIPLE-017)."""
    errors = []
    if not guidelines_file.exists():
        errors.append(f"GUIDELINES.md missing at {guidelines_file}")
    else:
        g_content = guidelines_file.read_text(encoding="utf-8")
        for p in principles:
            pid = p["id"]
            if f"### {pid}:" not in g_content and f"### {pid} " not in g_content and f"**[{pid}]" not in g_content:
                errors.append(f"{pid} missing from GUIDELINES.md")

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
        anchor = f"[GUIDELINES.md#{p['id'].lower()}]"
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary} {anchor}")
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
        anchor = f"[GUIDELINES.md](../../GUIDELINES.md#{p['id'].lower()})"
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary} {anchor}")
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
        anchor = f"[GUIDELINES.md#{p['id'].lower()}]"
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary} {anchor}")
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
        anchor = f"[GUIDELINES.md#{p['id'].lower()}]"
        lines.append(f"{i}. {p['id']}: {p['title']}")
        lines.append(f"   - {summary} {anchor}")
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
        anchor = f"[GUIDELINES.md#{p['id'].lower()}]"
        lines.append(f"{i}. **{p['id']}: {p['title']}**:")
        lines.append(f"   - {summary} {anchor}")
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
        status = "PASS" if char_len <= MAX_TARGET_CHARS else "EXCEEDED"
        if status == "EXCEEDED":
            budget_violations += 1
            print(f"[BUDGET {status}] {target_path.name}: {char_len} chars (~{est_tokens} tokens) > {MAX_TARGET_CHARS} cap")
        else:
            print(f"[BUDGET {status}] {target_path.name}: {char_len} chars (~{est_tokens} tokens)")

    if budget_violations > 0:
        sys.stderr.write(f"\n[ERROR] {budget_violations} target file(s) exceed prompt context budget! (PRINCIPLE-001)\n")
        if exit_on_mismatch:
            sys.exit(1)
        return budget_violations

    mismatches = 0
    for target_path, expected_content in targets.items():
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
            print(f"[UPDATED]: {target_path.relative_to(ROOT_DIR)}")

    if check_only and mismatches > 0:
        print(f"\n{mismatches} file(s) out of sync with AGENTS.md.")
        if exit_on_mismatch:
            sys.exit(1)
        return mismatches

    print(f"\nAll {len(targets)} AI guideline targets are synchronized successfully.")
    return mismatches


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    sync_all(check_only=check_mode, exit_on_mismatch=True)
