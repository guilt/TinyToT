# Tool Calling Test Cases
# Format: PROMPT | EXPECTED_CATEGORY | EXPECTED_TOOL | EXPECTED_PATTERNS
# Note: In the new architecture, tool execution happens via mcphost, not in TinyToT's output
# Tests verify category detection and reasoning chain selection

Search for information about quantum computing | tool_calling | ddg-search | Category: tool calling.*Search for Information
Tell me about the history of artificial intelligence | tool_calling | grokipedia | Category: tool calling.*Search for Information
What are the latest developments in machine learning? | tool_calling | ddg-search | Category: tool calling.*Search for Information
Find research papers on neural networks | tool_calling | grokipedia | Category: tool calling.*Search for Information
Search for weather information | tool_calling | ddg-search | Category: tool calling.*Search for Information
Look up information about climate change | tool_calling | grokipedia | Category: tool calling.*Search for Information
Find data about population growth | tool_calling | ddg-search | Category: tool calling.*Search for Information
Research the effects of social media | tool_calling | grokipedia | Category: tool calling.*Search for Information
Search for news about technology | tool_calling | ddg-search | Category: tool calling.*Search for Information
Tell me about the Roman Empire | tool_calling | grokipedia | Category: tool calling.*Search for Information
