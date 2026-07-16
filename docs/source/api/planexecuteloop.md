# PlanExecuteLoop

Decompose a prompt into steps, execute each via tools, synthesise via ToT.

    The loop uses TinyToT's own ToT engine (``generateReasoningResponse``) for
    both planning and synthesis — no external LLM needed.

**Module**: `tinytot.agent`

## Constructor

```python
PlanExecuteLoop(self, journal: 'Optional[LearningJournal]' = None) -> 'None'
```

## Methods

### `run(self, prompt: 'str', session_id: 'str' = '') -> 'str'`

Full plan → execute → synthesise cycle.
