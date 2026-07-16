# `clone`

**Module**: `tinytot.clone`

## `clone`

```python
clone(target: 'str | Path', variant: 'Optional[str]' = None, extra_knowledge: 'Optional[List[str | Path]]' = None, *, overwrite: 'bool' = False) -> 'Path'
```

Create a minimal variant delta directory at *target*.

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
