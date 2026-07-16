# LearningJournal

Append-only markdown learning journal.

    One file per day at ``data/journal/YYYY-MM-DD.md``.
    Format mirrors Hermes so ``loadHermesJournal`` in content.py can parse it.

**Module**: `tinytot.agent`

## Constructor

```python
LearningJournal(self, journal_dir: 'Path' = WindowsPath('D:/WS/TinyToT/tinytot/_data/journal')) -> 'None'
```

## Methods

### `recent(self, days: 'int' = 7) -> 'List[str]'`

Return the last N days' learning entries as plain strings.

### `record(self, content: 'str', source: 'str' = 'agent', session_id: 'str' = '') -> 'None'`

Append a learning entry to today's journal.
