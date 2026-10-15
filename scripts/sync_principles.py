#!/usr/bin/env python3
"""
Principles Auto-Sync Tool (PRINCIPLE-017)
Ensures all AI assistant guideline documents remain in 100% synchronization
with the master specification in AGENTS.md.
"""

import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_MD = ROOT_DIR / "AGENTS.md"


def parse_principles(agents_file: Path):
    content = agents_file.read_text(encoding="utf-8")
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

        concept = concept_match.group(1).strip() if concept_match else ""
        invariant = invariant_match.group(1).strip() if invariant_match else concept

        principles.append({
            "id": pid,
            "title": title,
            "concept": concept,
            "invariant": invariant,
        })
    return principles


def generate_gemini_content(principles):
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
    return "\n".join(lines)


def generate_agents_rule_content(principles):
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
    return "\n".join(lines)


def generate_claude_content(principles):
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
    return "\n".join(lines)


def generate_cursorrules_content(principles):
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
    return "\n".join(lines)


def generate_copilot_content(principles):
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
    return "\n".join(lines)


def sync_all(check_only: bool = False):
    if not AGENTS_MD.exists():
        print(f"Error: Master file {AGENTS_MD} not found.")
        sys.exit(1)

    principles = parse_principles(AGENTS_MD)
    print(f"Parsed {len(principles)} active principles from AGENTS.md:")
    for p in principles:
        print(f" - {p['id']}: {p['title']}")

    targets = {
        ROOT_DIR / "GEMINI.md": generate_gemini_content(principles),
        ROOT_DIR / ".agents" / "rules" / "principles.md": generate_agents_rule_content(principles),
        ROOT_DIR / "CLAUDE.md": generate_claude_content(principles),
        ROOT_DIR / ".cursorrules": generate_cursorrules_content(principles),
        ROOT_DIR / ".github" / "copilot-instructions.md": generate_copilot_content(principles),
    }

    # Governance Frugality & Context Budget Check (PRINCIPLE-001)
    MAX_TARGET_CHARS = 8000  # ~1,500-2,000 tokens per target file
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
        sys.exit(1)

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
        sys.exit(1)

    print(f"\nAll {len(targets)} AI guideline targets are synchronized successfully.")


if __name__ == "__main__":
    check_mode = "--check" in sys.argv
    sync_all(check_only=check_mode)

