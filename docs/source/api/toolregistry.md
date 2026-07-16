# ToolRegistry

Holds all registered tools and dispatches by name.

**Module**: `tinytot.tools_ext`

## Methods

### `all(self) -> 'List[Tool]'`

### `get(self, name: 'str') -> 'Optional[Tool]'`

### `register(self, tool: 'Tool') -> 'None'`

### `run(self, name: 'str', **kwargs: 'Any') -> 'str'`

### `schemas(self) -> 'List[Dict[str, Any]]'`
