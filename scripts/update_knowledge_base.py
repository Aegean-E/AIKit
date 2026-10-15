#!/usr/bin/env python3
"""
Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-016)

Inspects the repository AST, extracts exported classes, functions, and docstrings,
and generates the authoritative `knowledge/codebase_map.md`. Also validates
the integrity of all knowledge base documents.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CODEBASE_MAP_PATH = KNOWLEDGE_DIR / "codebase_map.md"

CORE_DOCS = [
    "INDEX.md",
    "architecture.md",
    "services.md",
    "data_models.md",
    "state_and_ui.md",
    "decisions.md",
    "codebase_map.md",
]

IGNORE_DIRS = {
    ".git",
    ".github",
    ".agents",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
}


def extract_python_symbols(file_path: Path) -> Dict[str, Any]:
    """Parse a python file with AST and extract docstrings, classes, and functions."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as e:
        return {"error": str(e), "classes": [], "functions": [], "docstring": None}

    module_docstring = ast.get_docstring(tree)
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    args = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    methods.append({
                        "name": item.name,
                        "args": args,
                        "docstring": ast.get_docstring(item)
                    })
            classes.append({
                "name": node.name,
                "docstring": class_doc,
                "methods": methods
            })
        elif isinstance(node, ast.FunctionDef):
            args = [arg.arg for arg in node.args.args]
            functions.append({
                "name": node.name,
                "args": args,
                "docstring": ast.get_docstring(node)
            })

    line_count = len(content.splitlines())
    return {
        "docstring": module_docstring,
        "classes": classes,
        "functions": functions,
        "line_count": line_count,
        "size_bytes": len(content.encode("utf-8"))
    }


def find_python_files(root: Path) -> List[Path]:
    """Dynamically discover all source python files across the repository."""
    py_files = []
    for path in root.rglob("*.py"):
        # Ignore excluded directories
        parts = set(path.parts)
        if any(ignored in parts for ignored in IGNORE_DIRS):
            continue
        py_files.append(path)
    return sorted(py_files)


def generate_codebase_map() -> str:
    """Generate the markdown content for knowledge/codebase_map.md."""
    lines = [
        "# Codebase Map & Symbol Catalog 🗺️",
        "",
        "> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**",
        "> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.",
        "",
        "---",
        ""
    ]

    files_to_scan = find_python_files(ROOT_DIR)

    total_classes = 0
    total_functions = 0
    total_lines = 0

    modules_data = []

    for file_path in files_to_scan:
        rel_path = file_path.relative_to(ROOT_DIR)
        info = extract_python_symbols(file_path)
        if "error" in info and not info.get("classes") and not info.get("functions"):
            continue

        c_count = len(info.get("classes", []))
        f_count = len(info.get("functions", []))
        l_count = info.get("line_count", 0)

        total_classes += c_count
        total_functions += f_count
        total_lines += l_count

        modules_data.append((rel_path, info))

    lines.append(f"## 📊 Codebase Metrics")
    lines.append(f"- **Total Python Modules**: `{len(modules_data)}`")
    lines.append(f"- **Total Classes**: `{total_classes}`")
    lines.append(f"- **Total Functions / Methods**: `{total_functions}`")
    lines.append(f"- **Total Source Lines**: `{total_lines}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📦 Modules & Exported Symbols")
    lines.append("")

    for rel_path, info in modules_data:
        str_path = str(rel_path).replace("\\", "/")
        lines.append(f"### [`{str_path}`]({str_path})")
        if info.get("docstring"):
            clean_doc = info["docstring"].strip().split("\n")[0]
            lines.append(f"> *{clean_doc}*")
            lines.append("")

        lines.append(f"**Size**: `{info.get('line_count', 0)}` lines (`{info.get('size_bytes', 0)}` bytes)")
        lines.append("")

        classes = info.get("classes", [])
        if classes:
            lines.append("**Classes:**")
            for c in classes:
                c_name = c["name"]
                c_doc = f" - *{c['docstring'].strip().split(chr(10))[0]}*" if c.get("docstring") else ""
                lines.append(f"- `class {c_name}`{c_doc}")
                for m in c.get("methods", []):
                    args_str = ", ".join(m["args"])
                    m_doc = f" - *{m['docstring'].strip().split(chr(10))[0]}*" if m.get("docstring") else ""
                    lines.append(f"  - Method `.{m['name']}({args_str})`{m_doc}")
            lines.append("")

        functions = info.get("functions", [])
        if functions:
            lines.append("**Functions:**")
            for f in functions:
                args_str = ", ".join(f["args"])
                f_doc = f" - *{f['docstring'].strip().split(chr(10))[0]}*" if f.get("docstring") else ""
                lines.append(f"- `def {f['name']}({args_str})`{f_doc}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def update_and_validate():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Update codebase_map.md atomically (fsync + replace)
    map_content = generate_codebase_map()
    tmp_map = CODEBASE_MAP_PATH.with_suffix(f".tmp_{os.getpid()}")
    with open(tmp_map, "w", encoding="utf-8") as f:
        f.write(map_content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_map, CODEBASE_MAP_PATH)
    print(f"[UPDATED] {CODEBASE_MAP_PATH.relative_to(ROOT_DIR)}")

    # 2. Validate all core knowledge base docs exist
    missing = []
    for doc in CORE_DOCS:
        p = KNOWLEDGE_DIR / doc
        if not p.exists():
            missing.append(doc)

    if missing:
        print(f"[WARN] Missing knowledge base documents: {', '.join(missing)}")
    else:
        print(f"[OK] Verified {len(CORE_DOCS)} knowledge base documents in knowledge/")


if __name__ == "__main__":
    update_and_validate()
