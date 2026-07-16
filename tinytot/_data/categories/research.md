---
category: research
keywords: research, paper, arxiv, study, literature, review, cite, author, publication, journal, conference, findings, methodology, results, abstract, hypothesis, experiment, dataset, benchmark, model, evaluate
---

# Research Chains

Reasoning chains for academic research, paper analysis, and literature review.

## Chain 1: Find and Summarise a Research Paper
<!-- Handles: paper, arxiv, research, study, publication, author, cite -->
Thought 1: Search for the paper by title, author, or topic on arXiv or the web.
Thought 2: Fetch the abstract and key sections — introduction, methodology, results.
Thought 3: Identify the research question, approach, and key contributions.
Thought 4: Extract the main experimental results and benchmarks reported.
Thought 5: Summarise in plain language: problem, method, results, significance.

## Chain 2: Compare Multiple Papers on a Topic
<!-- Handles: compare, survey, literature review, related work, paper differences -->
Thought 1: Search for the top papers on the topic from the last 2-3 years.
Thought 2: For each paper, extract: approach, dataset, key metric, result.
Thought 3: Identify common themes and contrasting approaches across papers.
Thought 4: Note which approach achieves best results and under what conditions.
Thought 5: Produce a structured comparison table and synthesis paragraph.

## Chain 3: Explain a Research Methodology
<!-- Handles: method, methodology, how does, approach, technique, algorithm -->
Thought 1: Identify the specific method or algorithm to explain.
Thought 2: Fetch the original paper or primary reference for the method.
Thought 3: Extract the core idea, inputs, outputs, and key equations.
Thought 4: Find a concrete example or intuitive analogy.
Thought 5: Explain the method clearly, noting assumptions and limitations.

## Chain 4: Reproduce Experimental Results
<!-- Handles: reproduce, replicate, dataset, benchmark, evaluate, metric -->
Thought 1: Identify the paper, dataset, and metric to reproduce.
Thought 2: Locate the dataset and any public code or checkpoints.
Thought 3: Understand the experimental setup exactly as described in the paper.
Thought 4: Note any discrepancies between paper and available resources.
Thought 5: Summarise what is needed to reproduce the result end-to-end.

## Chain 5: Research Auto-Summarisation (fetch → extract → ToT)
<!-- Handles: auto-research, fetch and summarize, read the paper, analyse the url -->
Thought 1: Extract the URL or paper identifier from the request.
Thought 2: Fetch the document — PDF via document_extract or HTML via web_fetch.
Thought 3: Identify the abstract, key contributions, and conclusion sections.
Thought 4: Run ToT summarisation over the extracted sections.
Thought 5: Return: title, authors, problem, method, results, 3 key takeaways.
