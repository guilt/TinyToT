---
schema_version: 3.0
description: Simplified tool detection mapping for MCP integration
---

# Tool Detection Patterns

## Date Time Tools
- keywords: what is the date, what date, today's date, what time, current time, what day, date today, current date
- tool_name: get_datetime
- params: {}

## Search Tools
- keywords: search, find, latest, research, news, developments, papers, data
- tool_name: ddg-search
- params: {"query": "extract_topic"}

## File System Tools
- keywords: file, read, list, png, count, duplicate, search.*files
- tool_name: filesystem
- params: {"operation": "read", "path": "~/"}

## Database Tools
- keywords: sqlite, database, query
- exclude_keywords: rds, aws
- tool_name: sqlite
- params: {"query": "full_prompt"}

## Information Lookup
- keywords: tell me about, information about, what is, who is, explain
- exclude_keywords: date, time, today, now, current date, current time, what time
- tool_name: grokipedia
- params: {"title": "extract_topic"}
