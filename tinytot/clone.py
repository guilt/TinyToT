"""
tinytot.clone — Self-replication: create a lightweight variant delta directory.

A TinyToT clone is a **minimal delta** — only the files that differ from the
base install.  The base knowledge, categories, codegen, and all other data stay
in the original ``pip install tinytot`` package.  The delta dir holds only:

  - ``variant.yaml``       personality (greeting, name, emoji)
  - ``knowledge/*.md``     domain-specific knowledge (optional)

At runtime, TinyToT merges both layers: delta files override base files of the
same name; new delta files extend the corpus.

Usage (Python):
    from tinytot.clone import clone
    clone("~/nanotot-dino", variant="dino")
    clone("~/nanotot-custom", extra_knowledge=["my_facts.md"])

Usage (CLI):
    tinytot-clone ~/nanotot-dino --variant dino
    tinytot-clone ~/nanotot-bird --variant bird --extra-knowledge birds.md
    tinytot-clone ~/nanotot-custom --extra-knowledge my_facts.md
    tinytot-clone ~/exact-copy

Built-in variants: bird, dino, dog
    Each variant has a custom greeting when you say "hello", plus a
    knowledge overlay specific to that domain.

Self-replication chain (NanoToT pattern):
    pip install tinytot
    tinytot-clone ~/nanotot-bird --variant bird
    TINYTOT_DATA_DIR=~/nanotot-bird tinytot
    # → "Chirp chirp! I'm TinyToT Bird — your feathered knowledge companion..."
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .content import VARIANTS_DIR as _VARIANTS_DIR

__all__ = ["clone"]

# Built-in variants — key must match a file in _data/variants/<key>.yaml
_BUILTIN_VARIANTS = ("bird", "dino", "dog")


def _load_variant_template(variant: str) -> Dict[str, Any]:
    """Load a built-in variant YAML template, or raise ValueError if unknown."""
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("pyyaml is required for variant support") from exc

    path = _VARIANTS_DIR / f"{variant}.yaml"
    if not path.exists():
        raise ValueError(
            f"Unknown variant '{variant}'. "
            f"Built-in variants: {', '.join(_BUILTIN_VARIANTS)}. "
            f"Or supply --extra-knowledge files to create a custom variant."
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def clone(
    target: str | Path,
    variant: Optional[str] = None,
    extra_knowledge: Optional[List[str | Path]] = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Create a minimal variant delta directory at *target*.

    The delta dir contains only the files that differ from the base install —
    no full copy of categories, codegen, or schema.  Point TINYTOT_DATA_DIR
    at this directory and TinyToT will merge the delta over the base install.

    Parameters
    ----------
    target:
        Directory to create.  Must not exist unless *overwrite* is True.
    variant:
        Built-in variant name: ``"bird"``, ``"dino"``, or ``"dog"``.
        Writes a ``variant.yaml`` so the server uses the variant's greeting
        when the user says "hello".
    extra_knowledge:
        Additional .md files to copy into the delta ``knowledge/`` directory.
        Files with the same stem as base knowledge files replace them for this
        variant; new files extend the corpus.
    overwrite:
        If True, delete *target* first if it already exists.

    Returns
    -------
    Path
        Resolved path of the delta directory (set TINYTOT_DATA_DIR to this).
    """
    dest = Path(target).expanduser().resolve()

    if dest.exists():
        if overwrite:
            shutil.rmtree(dest)
        else:
            raise FileExistsError(f"{dest} already exists. Pass overwrite=True to replace it.")

    dest.mkdir(parents=True)

    # Write variant.yaml so the server loads the greeting/name
    if variant:
        cfg = _load_variant_template(variant)
        try:
            import yaml
        except ImportError as exc:
            raise ImportError("pyyaml is required for variant support") from exc
        (dest / "variant.yaml").write_text(yaml.dump(cfg, allow_unicode=True), encoding="utf-8")

    # Layer extra knowledge files into delta/knowledge/
    if extra_knowledge:
        knowledge_dir = dest / "knowledge"
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        for src in extra_knowledge:
            src_path = Path(src).expanduser().resolve()
            if not src_path.exists():
                raise FileNotFoundError(f"Extra knowledge file not found: {src_path}")
            shutil.copy2(src_path, knowledge_dir / src_path.name)

    return dest


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="tinytot-clone",
        description=(
            "Create a TinyToT variant delta directory.  Only the delta files "
            "(variant.yaml + extra knowledge) are written — base data is shared "
            "from the pip install.  Set TINYTOT_DATA_DIR to the output path to run."
        ),
    )
    parser.add_argument("target", help="Destination directory for the delta")
    parser.add_argument(
        "--variant",
        choices=list(_BUILTIN_VARIANTS),
        metavar="NAME",
        help=f"Built-in variant personality: {', '.join(_BUILTIN_VARIANTS)}",
    )
    parser.add_argument(
        "--extra-knowledge",
        nargs="*",
        metavar="FILE",
        default=[],
        help=".md knowledge files to add or override in the variant",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace target directory if it already exists",
    )
    args = parser.parse_args()

    dest = clone(
        args.target,
        variant=args.variant,
        extra_knowledge=args.extra_knowledge or None,
        overwrite=args.overwrite,
    )
    print(f"Delta created: {dest}")
    if args.variant:
        try:
            import yaml

            cfg = yaml.safe_load((dest / "variant.yaml").read_text(encoding="utf-8"))
            print(f"Variant:       {cfg.get('name', args.variant)}")
            print(f"Greeting:      {cfg.get('greeting', '')}")
        except Exception:
            pass
    print(f"Run with:      TINYTOT_DATA_DIR={dest} tinytot")


if __name__ == "__main__":
    _cli()
