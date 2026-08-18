#!/usr/bin/env python3
"""
Generate Markdown API documentation from Python docstrings.

Dynamically discovers all public symbols exported via __all__ in each
submodule of ROOT_PACKAGE, then generates per-symbol markdown files
and a top-level index — no hardcoded class lists or section headers.

Signatures are rendered with filesystem-neutral defaults: any absolute
filesystem path (e.g. a ``PosixPath('/home/user/.../_data/...')`` default
value) is rewritten as a portable ``Path('tinytot/_data/...')`` so the
generated docs don't embed build-machine paths and remain stable when
regenerated on other systems.

ROOT_PACKAGE is derived from docs/source/conf.py so there is no
configuration to maintain in this script.

Run from the repo root:
    generate-api-docs
"""

from __future__ import annotations

import ast
import importlib
import inspect
import os
import pkgutil
import sys
from enum import EnumMeta
from functools import lru_cache
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap: derive ROOT_PACKAGE from docs/source/conf.py
# ---------------------------------------------------------------------------

_REPO_ROOT = Path.cwd()
_CONF_PY = _REPO_ROOT / "docs" / "source" / "conf.py"
_API_DIR = _REPO_ROOT / "docs" / "source" / "api"


def _parseRootPackage() -> str:
    """Read docs/source/conf.py and return the importable root package name."""
    if not _CONF_PY.exists():
        raise RuntimeError(
            f"docs/source/conf.py not found at {_CONF_PY}\nRun generate-api-docs from the repository root."
        )

    source = _CONF_PY.read_text(encoding="utf-8")
    tree = ast.parse(source)

    inserted_path: Optional[str] = None
    dist_name: Optional[str] = None

    for node in ast.walk(tree):
        # Strategy 1: sys.path.insert(0, os.path.abspath("..."))
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "path"
            and isinstance(node.func.value.value, ast.Name)
            and node.func.value.value.id == "sys"
            and node.func.attr == "insert"
            and len(node.args) == 2
        ):
            abspath_call = node.args[1]
            if (
                isinstance(abspath_call, ast.Call)
                and isinstance(abspath_call.func, ast.Attribute)
                and abspath_call.func.attr == "abspath"
                and abspath_call.args
                and isinstance(abspath_call.args[0], ast.Constant)
            ):
                inserted_path = abspath_call.args[0].value
                break

        # Strategy 2: _pkg_version("dist-name") or version("dist-name")
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("_pkg_version", "version")
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            dist_name = node.args[0].value

    if inserted_path is not None:
        abs_inserted = (_CONF_PY.parent / inserted_path).resolve()
        sys.path.insert(0, str(abs_inserted))
    elif dist_name is not None:
        # pip install -e .[dev] — package lives at repo root
        sys.path.insert(0, str(_REPO_ROOT))
    else:
        raise RuntimeError(
            f"Could not determine root package from {_CONF_PY}.\n"
            "Expected one of:\n"
            "  _pkg_version('dist-name')                # importlib.metadata style\n"
            "  sys.path.insert(0, os.path.abspath(…))  # legacy sys.path style"
        )

    def _findRootPackage(base: Path, hint: str = "") -> str:
        """Walk base to find the shallowest single-branch importable package.

        When multiple packages exist at the same level, prefer the one whose
        name matches hint (typically the distribution name).  Falls back to
        skipping packages named 'data' or 'tests' which are data/test roots.
        """
        from collections import deque

        _SKIP = {"data", "tests", "test", "docs", "examples", "cli"}

        queue = deque([base])
        while queue:
            current = queue.popleft()
            children = sorted(
                p
                for p in current.iterdir()
                if p.is_dir() and (p / "__init__.py").exists() and not p.name.startswith("_") and p.name not in _SKIP
            )
            if children:
                # Prefer hint match; fall back to first child
                match = next((p for p in children if p.name == hint), None)
                pkg = match or (children[0] if len(children) == 1 else None)
                if pkg is None:
                    # Multiple candidates — still no hint match; try the first
                    pkg = children[0]
                # Walk down single-branch sub-packages
                while True:
                    next_children = sorted(
                        p
                        for p in pkg.iterdir()
                        if p.is_dir()
                        and (p / "__init__.py").exists()
                        and not p.name.startswith("_")
                        and p.name not in _SKIP
                    )
                    if len(next_children) == 1:
                        pkg = next_children[0]
                    else:
                        break
                result = ".".join(pkg.relative_to(base).parts)
                if result:
                    return result
            for child in sorted(p for p in current.iterdir() if p.is_dir() and not p.name.startswith("_")):
                queue.append(child)
        raise RuntimeError(f"No importable packages found under {base}")

    if inserted_path is not None:
        return _findRootPackage((_CONF_PY.parent / inserted_path).resolve(), hint=dist_name or "")
    else:
        return _findRootPackage(_REPO_ROOT, hint=dist_name or "")


ROOT_PACKAGE = _parseRootPackage()
_API_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Docstring formatter
# ---------------------------------------------------------------------------


def formatDocstring(docstring: str) -> str:
    """Convert a raw docstring to clean markdown."""
    if not docstring:
        return ""

    lines = docstring.strip().split("\n")
    formatted = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if "Example:" in stripped or "Examples:" in stripped:
            if in_code_block:
                formatted.append("```\n")
                in_code_block = False
            formatted.append("\n**Examples**\n")
            continue

        if ".. code-block::" in stripped:
            formatted.append("\n```python")
            in_code_block = True
            continue

        if stripped.startswith(">>>") or stripped.startswith("..."):
            if not in_code_block:
                formatted.append("\n```python")
                in_code_block = True
            formatted.append(stripped[4:] if stripped.startswith(">>> ") else stripped)
            continue

        if in_code_block:
            if line.startswith("    ") or stripped == "":
                formatted.append(line[4:] if line.startswith("    ") else "")
                continue
            formatted.append("```\n")
            in_code_block = False

        formatted.append(line)

    if in_code_block:
        formatted.append("```\n")

    return "\n".join(formatted)


# ---------------------------------------------------------------------------
# Path-neutralizing rendering
#
# Function/class signature defaults often point into the installed package
# data dir (e.g. ``categoryDir: Path = CATEGORY_DIR``).  Because those
# constants resolve to absolute paths at import time, ``inspect.signature``
# renders build-machine-specific values like
# ``PosixPath('/home/user/repo/tinytot/_data/categories')``.  These would
# change on every machine that regenerates the docs, so we rewrite them to
# portable, package-relative ``Path('tinytot/_data/categories')`` defaults.
# This only affects the *rendered text* of the generated docs — nothing else.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _packageDir() -> Path:
    """Absolute directory containing ROOT_PACKAGE."""
    return Path(inspect.getfile(importlib.import_module(ROOT_PACKAGE))).parent


@lru_cache(maxsize=1)
def _packageAnchor() -> Path:
    """Parent of the package dir, so portable defaults read e.g.
    ``Path('tinytot/_data/categories')`` instead of a bare relative path."""
    return _packageDir().parent


def _portablePath(value: PurePath) -> Optional[str]:
    """Render a Path as a ``<pkg>/...`` slash-separated string (relative to the
    directory containing the package), or None when it can't be expressed that
    way (in which case the caller falls back to the built-in repr)."""
    try:
        rel = os.path.relpath(os.path.abspath(os.fspath(value)), _packageAnchor())
    except ValueError:  # e.g. different drives on Windows
        return None
    if rel == "." or rel.startswith("..") or os.path.isabs(rel):
        return None
    return rel.replace(os.sep, "/")


def _portableRepr(value: object) -> str:
    """repr() for doc output that abstracts the build machine's filesystem."""
    if isinstance(value, PurePath):
        rel = _portablePath(value)
        if rel is not None:
            return f"Path('{rel}')"
    return repr(value)


def _portableStrDefault(value: object) -> str:
    """str()-style default rendering (no quotes for plain values) that still
    abstracts filesystem paths."""
    if isinstance(value, PurePath):
        rel = _portablePath(value)
        if rel is not None:
            return f"Path('{rel}')"
    return str(value)


def _signatureText(func) -> str:
    """str(inspect.signature(func)) with build-machine paths abstracted.

    Keeps inspect's full formatting (positional-only markers, *args/**kwargs,
    annotations, etc.) and only rewrites the reprs of default values.
    """
    sig = inspect.signature(func)
    text = str(sig)
    for param in sig.parameters.values():
        if param.default is not inspect.Parameter.empty:
            orig = repr(param.default)
            portable = _portableRepr(param.default)
            if portable != orig:
                text = text.replace(orig, portable)
    return text


# ---------------------------------------------------------------------------
# Per-symbol doc generators
# ---------------------------------------------------------------------------


def _pydanticFieldsSection(cls) -> str:
    fields = getattr(cls, "model_fields", None)
    if not fields:
        return ""
    lines = ["**Fields:**\n"]
    for name, field_info in fields.items():
        annotation = getattr(field_info, "annotation", "")
        description = field_info.description or ""
        required = field_info.is_required() if hasattr(field_info, "is_required") else False
        default = "" if required else f", default: `{_portableStrDefault(field_info.default)}`"
        type_str = getattr(annotation, "__name__", str(annotation))
        lines.append(f"- `{name}` ({type_str}{default}): {description}")
    return "\n".join(lines) + "\n"


def generateClassDoc(cls, module_name: str, output_file: Path) -> None:
    doc = f"# {cls.__name__}\n\n"
    if cls.__doc__:
        doc += formatDocstring(cls.__doc__) + "\n\n"
    doc += f"**Module**: `{module_name}`\n\n"
    doc += _pydanticFieldsSection(cls)

    try:
        init_params = inspect.signature(cls.__init__).parameters
        if len(list(init_params)) > 1:
            doc += "## Constructor\n\n"
            doc += f"```python\n{cls.__name__}{_signatureText(cls.__init__)}\n```\n\n"
            if cls.__init__.__doc__:
                doc += formatDocstring(cls.__init__.__doc__) + "\n\n"
    except (ValueError, TypeError):
        pass

    methods = [
        (name, member)
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    ]
    if methods:
        doc += "## Methods\n\n"
        for name, method in methods:
            try:
                doc += f"### `{name}{_signatureText(method)}`\n\n"
            except (ValueError, TypeError):
                doc += f"### `{name}()`\n\n"
            if method.__doc__:
                doc += formatDocstring(method.__doc__) + "\n\n"

    output_file.write_text(doc.rstrip("\n") + "\n", encoding="utf-8")
    print(f"  Generated: {output_file.name}")


def generateEnumDoc(cls, module_name: str, output_file: Path) -> None:
    doc = f"# {cls.__name__}\n\n"
    if cls.__doc__:
        doc += formatDocstring(cls.__doc__) + "\n\n"
    doc += f"**Module**: `{module_name}`\n\n**Type**: Enum\n\n## Values\n\n"
    for member in cls:
        doc += f"- **`{member.name}`**: `{_portableRepr(member.value)}`\n"
    doc += "\n"
    output_file.write_text(doc.rstrip("\n") + "\n", encoding="utf-8")
    print(f"  Generated: {output_file.name}")


def generateFunctionDoc(func, module_name: str) -> str:
    try:
        sig_str = f"{func.__name__}{_signatureText(func)}"
    except (ValueError, TypeError):
        sig_str = f"{func.__name__}()"
    doc = f"## `{func.__name__}`\n\n```python\n{sig_str}\n```\n\n"
    if func.__doc__:
        doc += formatDocstring(func.__doc__) + "\n\n"
    return doc


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _slug(name: str) -> str:
    return name.lower().replace(".", "_")


def discoverAndDocument() -> Dict[str, List[Tuple[str, str]]]:
    """Walk every submodule under ROOT_PACKAGE, collect public symbols from
    __all__, generate per-symbol markdown docs, and return an index."""
    root_mod = importlib.import_module(ROOT_PACKAGE)
    root_path = Path(inspect.getfile(root_mod)).parent
    index: Dict[str, List[Tuple[str, str]]] = {}

    modules_to_scan = [ROOT_PACKAGE]
    for _finder, modname, _ispkg in pkgutil.walk_packages(path=[str(root_path)], prefix=ROOT_PACKAGE + "."):
        modules_to_scan.append(modname)

    for modname in modules_to_scan:
        # Skip test subpackages
        if ".tests" in modname or ".cli" in modname:
            continue
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue

        all_names = getattr(mod, "__all__", None)
        if not all_names:
            continue

        module_entries: List[Tuple[str, str]] = []
        for name in all_names:
            obj = getattr(mod, name, None)
            if obj is None or not (inspect.isclass(obj) or inspect.isfunction(obj)):
                continue

            filename = f"{_slug(name)}.md"
            out = _API_DIR / filename

            if isinstance(obj, EnumMeta):
                generateEnumDoc(obj, modname, out)
            elif inspect.isclass(obj):
                generateClassDoc(obj, modname, out)
            else:
                content = f"# `{name}`\n\n**Module**: `{modname}`\n\n"
                content += generateFunctionDoc(obj, modname)
                out.write_text(content.rstrip("\n") + "\n", encoding="utf-8")
                print(f"  Generated: {out.name}")

            module_entries.append((name, filename))

        if module_entries:
            index[modname] = module_entries

    return index


# ---------------------------------------------------------------------------
# Index generator
# ---------------------------------------------------------------------------


def generateIndex(index: Dict[str, List[Tuple[str, str]]]) -> None:
    root_mod = importlib.import_module(ROOT_PACKAGE)
    pkg_doc = (root_mod.__doc__ or "").strip().split("\n")[0]

    lines = [f"# {ROOT_PACKAGE} — API Reference\n"]
    if pkg_doc:
        lines.append(f"{pkg_doc}\n")
    lines.append("> Auto-generated from source docstrings. To regenerate run `make docs`.\n")

    for modname, entries in sorted(index.items()):
        mod = importlib.import_module(modname)
        mod_doc = (mod.__doc__ or "").strip().split("\n")[0]
        lines.append(f"## `{modname}`\n")
        if mod_doc:
            lines.append(f"{mod_doc}\n")
        for sym_name, filename in sorted(entries):
            lines.append(f"- [{sym_name}]({filename})")
        lines.append("")

    (_API_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  Generated: README.md (index)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    from tinytot._stdio import ensureUtf8Stdio

    ensureUtf8Stdio()
    print(f"Generating API docs for {ROOT_PACKAGE} ...\n")
    index = discoverAndDocument()
    generateIndex(index)
    print(f"\nDone. Output: {_API_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
