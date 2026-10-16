#!/usr/bin/env python3
"""
Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-016)

Inspects the repository AST, extracts exported classes, functions, and docstrings,
and generates the authoritative `knowledge/codebase_map.md`. Also validates
the integrity of all knowledge base documents.
"""

import ast
import copy
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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


# Oldest Python the repository supports (README "Runtime Prerequisites", PRINCIPLE-003 R4). Parsing
# with this grammar makes the AST gate reject syntax that only newer interpreters accept, which a
# developer on a newer Python would otherwise never see fail locally.
MIN_PYTHON = (3, 10)

FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


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


def render_signature(node: Any, drop_self: bool = False) -> List[str]:
    """
    Render a complete call signature from an AST function node (PRINCIPLE-003, PRINCIPLE-016).

    The catalog is what agents consult before verifying call-sites, so a partial signature is
    an anti-hallucination failure: reading only `args.args` silently omitted `*args`, `**kwargs`,
    and every keyword-only parameter, so `f(a, *, b)` was catalogued as `f(a)`. Positional-only
    parameters are marked with a trailing `/` and keyword-only ones follow a bare `*`, matching
    Python's own signature syntax.
    """
    spec = node.args
    parts: List[str] = []

    posonly = [a.arg for a in getattr(spec, "posonlyargs", [])]
    positional = [a.arg for a in spec.args]
    if drop_self:
        if posonly and posonly[0] in ("self", "cls"):
            posonly = posonly[1:]
        elif positional and positional[0] in ("self", "cls"):
            positional = positional[1:]

    parts.extend(posonly)
    if posonly:
        parts.append("/")
    parts.extend(positional)

    if spec.vararg:
        parts.append(f"*{spec.vararg.arg}")
    elif spec.kwonlyargs:
        parts.append("*")
    parts.extend(a.arg for a in spec.kwonlyargs)

    if spec.kwarg:
        parts.append(f"**{spec.kwarg.arg}")

    return parts


# Extracted symbols keyed by (path, content): a hit can never be stale, and callers receive a deep
# copy so mutating a result cannot leak. Bounded to the files of one repository scan.
_SYMBOL_CACHE: Dict[tuple, Dict[str, Any]] = {}
_SYMBOL_CACHE_MAX = 256


def extract_python_symbols(file_path: Path, strict: bool = False) -> Dict[str, Any]:
    """Parse a python file with AST and extract docstrings, classes, and functions (PRINCIPLE-003)."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        if strict:
            raise ValueError(f"[PRINCIPLE-003 AST FAILURE] Unreadable file {file_path}: {e}") from e
        return {"error": str(e), "classes": [], "functions": [], "docstring": None}
    key = (str(file_path), content)
    if key in _SYMBOL_CACHE:
        return copy.deepcopy(_SYMBOL_CACHE[key])
    result = _extract_symbols_uncached(file_path, content, strict)
    if "error" not in result:
        if len(_SYMBOL_CACHE) >= _SYMBOL_CACHE_MAX:
            _SYMBOL_CACHE.clear()
        _SYMBOL_CACHE[key] = copy.deepcopy(result)
    return result


def _extract_symbols_uncached(file_path: Path, content: str, strict: bool) -> Dict[str, Any]:
    """AST extraction proper; see extract_python_symbols()."""
    try:
        tree = ast.parse(content, filename=str(file_path), feature_version=MIN_PYTHON)
    except Exception as e:
        if strict:
            raise ValueError(f"[PRINCIPLE-003 AST FAILURE] Syntax error in {file_path}: {e}") from e
        return {"error": str(e), "classes": [], "functions": [], "docstring": None}

    module_docstring = ast.get_docstring(tree)
    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node)
            methods = []
            for item in node.body:
                if isinstance(item, FUNCTION_NODES):
                    methods.append({
                        "name": item.name,
                        "args": render_signature(item, drop_self=True),
                        "is_async": isinstance(item, ast.AsyncFunctionDef),
                        "docstring": ast.get_docstring(item)
                    })
            classes.append({
                "name": node.name,
                "docstring": class_doc,
                "methods": methods
            })
        elif isinstance(node, FUNCTION_NODES):
            functions.append({
                "name": node.name,
                "args": render_signature(node),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
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


def generate_codebase_map(root: Optional[Path] = None, strict: bool = True) -> str:
    """Generate the markdown content for knowledge/codebase_map.md with AST validation (PRINCIPLE-003)."""
    target_root = root or ROOT_DIR
    lines = [
        "# Codebase Map & Symbol Catalog 🗺️",
        "",
        "> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**",
        "> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.",
        "",
        "---",
        ""
    ]

    files_to_scan = find_python_files(target_root)

    total_classes = 0
    total_functions = 0
    total_lines = 0

    modules_data = []
    syntax_errors = []

    for file_path in files_to_scan:
        rel_path = file_path.relative_to(target_root)
        info = extract_python_symbols(file_path, strict=False)
        if "error" in info:
            syntax_errors.append((rel_path, info["error"]))
            continue

        c_count = len(info.get("classes", []))
        f_count = len(info.get("functions", []))
        l_count = info.get("line_count", 0)

        total_classes += c_count
        total_functions += f_count
        total_lines += l_count

        modules_data.append((rel_path, info))

    if syntax_errors and strict:
        err_msg = "\n".join([f"  - {p}: {err}" for p, err in syntax_errors])
        raise ValueError(
            f"[PRINCIPLE-003 AST GATE FAILURE] Found {len(syntax_errors)} invalid Python file(s) with syntax errors:\n{err_msg}"
        )

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
                    m_kind = "async def " if m.get("is_async") else ""
                    lines.append(f"  - Method `{m_kind}.{m['name']}({args_str})`{m_doc}")
            lines.append("")

        functions = info.get("functions", [])
        if functions:
            lines.append("**Functions:**")
            for f in functions:
                args_str = ", ".join(f["args"])
                f_doc = f" - *{f['docstring'].strip().split(chr(10))[0]}*" if f.get("docstring") else ""
                f_kind = "async def" if f.get("is_async") else "def"
                lines.append(f"- `{f_kind} {f['name']}({args_str})`{f_doc}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def validate_knowledge_links(knowledge_dir: Path) -> List[str]:
    """Verify that all relative file links in knowledge/INDEX.md physically exist on disk (PRINCIPLE-016)."""
    index_path = knowledge_dir / "INDEX.md"
    if not index_path.exists():
        return [f"INDEX.md missing in {knowledge_dir}"]
    content = index_path.read_text(encoding="utf-8")
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)#]+)(?:#[^)]*)?\)')
    broken = []
    for match in link_pattern.finditer(content):
        target = match.group(2).strip()
        if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
            continue
        target_path = (knowledge_dir / target).resolve()
        if not target_path.exists():
            broken.append(f"{target} (referenced in INDEX.md)")
    return broken


def check_codebase_map_freshness(knowledge_dir: Optional[Path] = None, strict: bool = True) -> bool:
    """
    Check if codebase_map.md accurately reflects current codebase AST (PRINCIPLE-016).
    Returns True if fresh. If stale and strict=True, raises ValueError. If stale and strict=False, returns False.
    """
    k_dir = knowledge_dir or KNOWLEDGE_DIR
    map_path = k_dir / "codebase_map.md"
    if not map_path.exists():
        if strict:
            raise ValueError(f"[PRINCIPLE-016 CODEBASE MAP MISSING] {map_path} does not exist.")
        return False

    current_content = map_path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    generated_content = generate_codebase_map(strict=strict).replace("\r\n", "\n").strip()
    is_fresh = (current_content == generated_content)
    if not is_fresh and strict:
        raise ValueError(
            "[PRINCIPLE-016 CODEBASE MAP STALE] knowledge/codebase_map.md is out of sync with AST. "
            "Run 'python scripts/update_knowledge_base.py' to synchronize."
        )
    return is_fresh


def update_and_validate(knowledge_dir: Optional[Path] = None, strict: bool = True):
    k_dir = knowledge_dir or KNOWLEDGE_DIR
    k_dir.mkdir(parents=True, exist_ok=True)
    map_path = k_dir / "codebase_map.md"

    # 1. Update codebase_map.md atomically (fsync + replace) with strict AST verification (PRINCIPLE-003)
    map_content = generate_codebase_map(strict=strict)
    tmp_map = map_path.with_suffix(f".tmp_{os.getpid()}")
    with open(tmp_map, "w", encoding="utf-8") as f:
        f.write(map_content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_map, map_path)
    fsync_dir(map_path.parent)
    try:
        rel_str = str(map_path.relative_to(ROOT_DIR))
    except ValueError:
        rel_str = str(map_path)
    print(f"[UPDATED] {rel_str}")

    # 2. Validate all core knowledge base docs exist
    missing = []
    for doc in CORE_DOCS:
        p = k_dir / doc
        if not p.exists():
            missing.append(doc)

    if missing:
        msg = f"Missing knowledge base documents: {', '.join(missing)}"
        if strict:
            raise ValueError(f"[PRINCIPLE-016 KNOWLEDGE BASE GAP] {msg}")
        print(f"[WARN] {msg}")
    else:
        print(f"[OK] Verified {len(CORE_DOCS)} knowledge base documents in {k_dir.name}/")

    # 3. Validate link integrity in knowledge/INDEX.md (PRINCIPLE-016)
    broken_links = validate_knowledge_links(k_dir)
    if broken_links:
        msg = f"Broken relative links in {k_dir.name}/INDEX.md: {', '.join(broken_links)}"
        if strict:
            raise ValueError(f"[PRINCIPLE-016 LINK INTEGRITY FAILURE] {msg}")
        print(f"[WARN] {msg}")
    else:
        print(f"[OK] Verified link integrity in {k_dir.name}/INDEX.md")


README_MAX_CHARS = 20_000
README_LABELS = (
    "Cold-Start Quick Reference",
    "**Runtime Prerequisites**:",
    "**Canonical Regression Shield Gate**:",
    "What's Inside",
)
_TREE_LINE = re.compile(r"^((?:│   |    )*)(?:├── |└── )(.+)$")
_SCRIPT_COMMAND = re.compile(r"python (scripts/[\w.]+\.py)([^`\n|]*)")
_UNITTEST_COMMAND = re.compile(r"python -m unittest (tests\.\w+)")
_FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z-]*)")


def parse_readme_tree(readme: str) -> List[str]:
    """
    Paths in the first ```text block after "What's Inside" (PRINCIPLE-005 R5), relative to the
    repository root; a directory ends with '/'. The block's first line (the root) is skipped.
    """
    heading = re.search(r"^#+ .*What's Inside", readme, re.M)  # a heading, never a mention in prose
    fence = readme.find("```text\n", heading.end()) if heading else -1
    if fence < 0:
        return []
    block = readme[fence + len("```text\n"):readme.find("```", fence + len("```text\n"))]
    paths: List[str] = []
    stack: List[str] = []
    for line in block.splitlines():
        match = _TREE_LINE.match(line)
        if not match:
            continue
        name = match.group(2).split("<-")[0].strip()
        stack = stack[:len(match.group(1)) // 4] + [name.rstrip("/")]
        paths.append("/".join(stack) + ("/" if name.endswith("/") else ""))
    return paths


def audit_readme(
    readme: str,
    tracked: Optional[List[str]],
    exists: Callable[[str], bool],
    script_source: Callable[[str], Optional[str]],
) -> List[str]:
    """
    Every PRINCIPLE-005 rule a program can decide, as one error per violation. Pure: the caller
    supplies the tracked files (None when git is unavailable), a path test and a script reader.
    It replaces a test holding a fixed list of AIKit paths, which never noticed a new file
    missing from the tree, a dead path in it, or a documented flag that no script declares.
    """
    errors: List[str] = []
    if len(readme) > README_MAX_CHARS:
        errors.append(f"README.md has {len(readme):,} chars; the limit is {README_MAX_CHARS:,} (R1)")
    errors += [f"README.md lacks the label '{label}' (R1)" for label in README_LABELS if label not in readme]

    tree = parse_readme_tree(readme)
    if not tree:
        errors.append("README.md has no ```text directory tree after \"What's Inside\" (R5)")
    listed = {p.rstrip("/") for p in tree}
    errors += [f"README.md tree lists '{p}', which does not exist (R5)" for p in tree if not exists(p.rstrip("/"))]
    if tree and tracked is not None:
        required = {t.split("/")[0] for t in tracked}
        for directory in (p.rstrip("/") for p in tree if p.endswith("/") and any(q != p and q.startswith(p) for q in tree)):
            prefix = directory + "/"
            required |= {prefix + t[len(prefix):].split("/")[0] for t in tracked if t.startswith(prefix)}
        errors += [f"README.md tree omits tracked '{p}' (R5)" for p in sorted(required - listed)]

    for match in _SCRIPT_COMMAND.finditer(readme):
        script = match.group(1)
        source = script_source(script)
        if source is None:
            errors.append(f"README.md runs '{script}', which does not exist (R3)")
            continue
        errors += [f"README.md passes {flag} to {script}, which does not declare it (R3)"
                   for flag in _FLAG.findall(match.group(2)) if f'"{flag}"' not in source]
    for module in _UNITTEST_COMMAND.findall(readme):
        if not exists(module.replace(".", "/") + ".py"):
            errors.append(f"README.md runs test module '{module}', which does not exist (R3)")
    return sorted(set(errors))


def check_readme(root: Path = ROOT_DIR) -> List[str]:
    """Run `audit_readme` on `root`, listing tracked files with git (bounded, PRINCIPLE-010 R3)."""
    readme_path = root / "README.md"
    if not readme_path.is_file():
        return ["README.md does not exist (R1)"]
    tracked: Optional[List[str]] = None
    try:
        listing = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True,
                                 text=True, encoding="utf-8", timeout=10)
        if listing.returncode == 0:
            tracked = [p for p in listing.stdout.split("\0") if p]
    except (OSError, subprocess.SubprocessError):
        pass
    if tracked is None:
        print("[WARN] git is unavailable, so README tree completeness was not checked (PRINCIPLE-005 R5).")

    def script_source(rel: str) -> Optional[str]:
        path = root / rel
        return path.read_text(encoding="utf-8") if path.is_file() else None

    return audit_readme(readme_path.read_text(encoding="utf-8"), tracked,
                        lambda rel: (root / rel).exists(), script_source)


def report_readme(errors: List[str]) -> bool:
    """Print README findings with the remediation triad (PRINCIPLE-011 R6); True when clean."""
    if not errors:
        print("[OK] README.md: size, labels, directory tree and documented commands verified (PRINCIPLE-005)")
        return True
    print(f"[FAIL] README.md drift ({len(errors)}):")
    for error in errors[:20]:
        print(f"   - {error}")
    if len(errors) > 20:
        print(f"   ... and {len(errors) - 20} more")
    print("   Why: a cold-starting agent trusts README.md; a dead path or command wastes its first turn.")
    print("   Fix: edit README.md as each line says (rule numbers are PRINCIPLE-005's), then re-run.")
    return False


KNOWN_FLAGS = {"--check", "--lenient", "--help", "-h"}

HELP_TEXT = """AIKit Knowledge Base Auto-Updater (PRINCIPLE-016)

Usage:
  python scripts/update_knowledge_base.py [OPTIONS]

Options:
  --check     Verify, without writing, that codebase_map.md matches the AST and that README.md
              passes the PRINCIPLE-005 checks (size, labels, directory tree, documented
              commands); exits 1 on any drift
  --lenient   Downgrade AST syntax and link integrity failures from errors to warnings
  -h, --help  Show this help message and exit

Exit codes:
  0  success    1  stale map / validation failure    2  CLI argument misuse
"""


def _validate_argv(argv: List[str], known: set, help_text: str) -> None:
    """Short-circuit on --help and reject unknown flags with exit 2 (PRINCIPLE-011, PRINCIPLE-015)."""
    if "-h" in argv or "--help" in argv:
        print(help_text, end="")
        sys.exit(0)
    unknown = [a for a in argv if a.startswith("-") and a not in known]
    if unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Why: this tool accepts only {', '.join(sorted(known))}.", file=sys.stderr)
        print("Fix: run 'python scripts/update_knowledge_base.py --help' to list valid options.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _validate_argv(sys.argv[1:], KNOWN_FLAGS, HELP_TEXT)

    if "--check" in sys.argv:
        try:
            fresh = check_codebase_map_freshness(strict=False)
            if fresh:
                print("[OK] knowledge/codebase_map.md is fresh and synchronized with AST.")
            else:
                print("[FAIL] knowledge/codebase_map.md is stale. Run 'python scripts/update_knowledge_base.py' to update.")
            readme_ok = report_readme(check_readme())
            sys.exit(0 if fresh and readme_ok else 1)
        except Exception as e:
            print(f"[FAIL] Error checking codebase map freshness: {e}")
            sys.exit(1)

    is_lenient = "--lenient" in sys.argv
    try:
        update_and_validate(strict=not is_lenient)
    except ValueError as gate_error:
        # PRINCIPLE-003 R7 halts here; PRINCIPLE-011 R6 forbids doing it with a raw traceback.
        print(f"[AST GATE FAILED] {gate_error}", file=sys.stderr)
        print("Why: a file that does not parse cannot be catalogued or trusted (PRINCIPLE-003 R7).",
              file=sys.stderr)
        print("Fix: correct the syntax error in the file named above, then re-run this script.",
              file=sys.stderr)
        sys.exit(1)
    if not report_readme(check_readme()) and not is_lenient:
        sys.exit(1)

