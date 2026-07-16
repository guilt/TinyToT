---
category: agent
keywords: plan and execute, multi-step workflow, agentic pipeline, fetch and summarize, gather and process, research paper, auto-research, document pipeline, tool sequence, step by step plan, execute steps, coordinate tools
---

# Agent Planning Chains

Reasoning chains for multi-step agentic tasks: planning, tool selection, and execution.

## Chain 1: Research and Summarise a Topic
<!-- Handles: auto-research, fetch paper, summarize article, investigate topic, gather information -->
Thought 1: Identify the core topic or question to research.
Thought 2: Search for the most relevant and authoritative sources.
Thought 3: Fetch and extract the full content from the top results.
Thought 4: Synthesise findings into a concise, structured summary.
Thought 5: Highlight key insights, conclusions, and open questions.

## Chain 2: Analyse a Data File
<!-- Handles: data, csv, json, analyse, explore, describe, schema, statistics -->
Thought 1: Identify the file path and format (CSV, JSON, JSONL).
Thought 2: Inspect the schema — column names, types, and row count.
Thought 3: Compute basic statistics — min, max, mean, unique values.
Thought 4: Filter or query for rows matching specific criteria.
Thought 5: Summarise the key patterns and anomalies found.

## Chain 3: Fetch and Process a Document
<!-- Handles: pdf, docx, document, read, extract, file, paper -->
Thought 1: Locate the document — local path or URL to the PDF, DOCX, or text file.
Thought 2: Use DocumentTool to extract the full text, handling format-specific quirks.
Thought 3: Identify the document structure — sections, headings, tables within the file.
Thought 4: Pull out the relevant passages that answer the query from the document.
Thought 5: Return a structured answer grounded in the extracted document text.

## Chain 4: Translate and Analyse Foreign Content
<!-- Handles: translate, translation, foreign, language, multilingual -->
Thought 1: Detect the source language of the foreign-language text.
Thought 2: Translate the text to the target language using TranslateTool.
Thought 3: Analyse the translated text for the requested meaning or facts.
Thought 4: Return the analysis with any translation caveats if relevant.

## Chain 5: Explore Local Files and Directories
<!-- Handles: list local files, explore directory, filesystem path, folder contents -->
Thought 1: Identify the target directory or file path.
Thought 2: List the contents and identify relevant files.
Thought 3: Read or search within files matching the query.
Thought 4: Summarise the findings from the filesystem exploration.

## Chain 6: Run a Shell Command and Interpret Output
<!-- Handles: run, execute, shell, bash, script -->
Thought 1: Determine the exact shell invocation needed to accomplish the agentic task.
Thought 2: Verify the shell invocation is safe and within the agent's permitted scope.
Thought 3: Execute via ShellTool and capture stdout and stderr.
Thought 4: Interpret the exit code, flagging any errors encountered.
Thought 5: Return a concise explanation of what the shell invocation did and its result.

## Chain 7: Analyse an Image
<!-- Handles: image, photo, picture, describe image, analyse image, ocr, visual -->
Thought 1: Load the image and inspect its basic properties — size, format, mode.
Thought 2: Analyse pixel statistics — brightness, dominant colours, contrast.
Thought 3: Check for embedded text regions using edge density heuristics.
Thought 4: Describe the visual content based on colour and structural analysis.
Thought 5: Suggest follow-up tools if full OCR or object recognition is needed.

## Chain 8: Multi-Step Pipeline
<!-- Handles: first then, step by step, pipeline, workflow, sequence, and then -->
Thought 1: Parse the request into an ordered sequence of sub-tasks.
Thought 2: Identify the tool required for each sub-task.
Thought 3: Execute sub-tasks in order, passing output from one to the next.
Thought 4: Accumulate context from each step to inform later steps.
Thought 5: Synthesise all gathered context into a final coherent response.
