# 04 — Tool Calling

TinyToT supports the Ollama tool-calling format. When a prompt matches a configured
tool pattern, it returns a `tool_calls` response that mcphost (or any compatible
client) can execute.

## How it works

1. Prompt arrives at `/api/chat` with a `tools` list
2. TinyToT checks `data/schema/information_patterns.md` for keyword matches
3. On match: returns `tool_calls` with the matched tool name and extracted params
4. Client executes the tool and sends result back in a second turn
5. TinyToT returns the tool result as the final response

## Schema format

Edit `data/schema/information_patterns.md` to define tool patterns:

```markdown
---
schema_version: 1.0
---

## My Search Tool
- keywords: search, find, latest, news, look up
- tool_name: my-search
- params: {"query": "extract_topic"}

## My Database Tool
- keywords: query, database, look up record
- exclude_keywords: aws, rds
- tool_name: my-db
- params: {"query": "full_prompt"}
```

Parameter extraction directives:
- `"extract_topic"` — strips action/stop words and returns the main subject
- `"full_prompt"` — passes the entire prompt as the parameter value

## Using with mcphost

```bash
# Start TinyToT
make run

# Run a query that triggers tool use
mcphost -m "ollama:tinytot" \
  --config ~/.mcphost.json \
  -p "Search for the latest developments in quantum computing"
```

TinyToT detects "search" + "latest" keywords, matches `ddg-search`, and returns:
```json
{
  "message": {
    "role": "assistant",
    "content": "Based on the prompt..., I need to search...",
    "tool_calls": [{
      "id": "call_1234",
      "type": "function",
      "function": {
        "name": "ddg__search",
        "arguments": {"query": "quantum computing developments"}
      }
    }]
  }
}
```

mcphost executes the search and returns results. TinyToT passes them through
as the final response.

## Testing tool detection

```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tinytot",
    "messages": [{"role": "user", "content": "Search for latest AI news"}],
    "stream": false,
    "tools": [{
      "type": "function",
      "function": {
        "name": "ddg__search",
        "description": "Search the web",
        "parameters": {
          "type": "object",
          "properties": {"query": {"type": "string"}}
        }
      }
    }]
  }'
```

## Adding a new tool

1. Add a section to `data/schema/information_patterns.md`
2. Restart the server (schema is cached at startup)
3. Pass the tool in the `tools` array when calling `/api/chat`

```markdown
## My Weather Tool
- keywords: weather, temperature, forecast, rain, sunny
- tool_name: weather-api
- params: {"location": "extract_topic"}
```

## Next Steps

- **[Hermes Bridge](05_hermes_bridge.md)** — organic knowledge from agent sessions
- **[Eval Harness](06_eval_harness.md)** — using TinyToT with GenAI-Eval
