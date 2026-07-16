# `loadHermesJournal`

**Module**: `tinytot.content`

## `loadHermesJournal`

```python
loadHermesJournal(path: 'Path') -> 'List[KnowledgePassage]'
```

Parse a Hermes Learning Journal file into knowledge passages.

    The Hermes journal format uses ``## <content>`` headings as learning entries,
    each followed by a ``> source: ... · hash: ...`` provenance line. This function
    extracts the content of each such heading as a passage, stripping the metadata.
    Ordinary section headings without a following provenance line are section labels.

    This is the bridge between Hermes organic learning and TinyToT inference:
    learnings recorded in Hermes sessions become directly retrievable knowledge
    in TinyToT without any training step.
