# tinytot — API Reference

tinytot — Tree of Thoughts inference server with Ollama API compatibility.

> Auto-generated from source docstrings. To regenerate run `make docs`.

## `tinytot.agent`

tinytot.agent — Agentic Plan-Execute loop for TinyToT.

- [LearningJournal](learningjournal.md)
- [PlanExecuteLoop](planexecuteloop.md)
- [agentResponse](agentresponse.md)
- [detectAgentNeeds](detectagentneeds.md)

## `tinytot.clone`

tinytot.clone — Self-replication: create a lightweight variant delta directory.

- [clone](clone.md)

## `tinytot.codegen`

tinytot.codegen -- Dataset-driven code generation.

- [detectCodeRequest](detectcoderequest.md)
- [detectLanguage](detectlanguage.md)
- [generateCode](generatecode.md)
- [generateProject](generateproject.md)
- [isCodeRequest](iscoderequest.md)
- [isProjectRequest](isprojectrequest.md)

## `tinytot.compute`

tinytot.compute — Safe arithmetic, unit conversion, date reasoning, and word-problem solver.

- [detectComputePrompt](detectcomputeprompt.md)
- [solveCompute](solvecompute.md)

## `tinytot.content`

tinytot.content — chain loading, category discovery, schema parsing.

- [loadHermesJournal](loadhermesjournal.md)
- [loadToolPatterns](loadtoolpatterns.md)

## `tinytot.generate`

tinytot.generate — Use-case handlers for the 80-90% of GenAI workloads.

- [detectUseCase](detectusecase.md)
- [handleUseCase](handleusecase.md)

## `tinytot.inference`

tinytot.inference — Tree of Thoughts reasoning, response formatting.

- [buildContextPrompt](buildcontextprompt.md)
- [detectResponseMode](detectresponsemode.md)
- [executeReasoningSteps](executereasoningsteps.md)
- [extractEvaluatedResponse](extractevaluatedresponse.md)
- [generateJsonScoringResponse](generatejsonscoringresponse.md)
- [generateReasoningResponse](generatereasoningresponse.md)
- [generateTreeOfThoughtsResponse](generatetreeofthoughtsresponse.md)
- [normalizePrompt](normalizeprompt.md)
- [shapeDirectAnswer](shapedirectanswer.md)

## `tinytot.refine`

tinytot.refine — Rule-based code refinement and reasoning explanation.

- [applyRefinement](applyrefinement.md)
- [detectRefinementIntent](detectrefinementintent.md)
- [explainCode](explaincode.md)
- [explainReasoning](explainreasoning.md)
- [extractPriorCode](extractpriorcode.md)

## `tinytot.retrieval`

tinytot.retrieval — Multi-headed TF-IDF retrieval, chain ranking, categorization.

- [categorizePrompt](categorizeprompt.md)
- [chainVector](chainvector.md)
- [cosineSim](cosinesim.md)
- [findKnowledgeAnswer](findknowledgeanswer.md)
- [multiHeadScore](multiheadscore.md)
- [multiHeadScorePassage](multiheadscorepassage.md)
- [queryVector](queryvector.md)
- [rankChains](rankchains.md)
- [scoreChain](scorechain.md)
- [scoreResponse](scoreresponse.md)

## `tinytot.summarize`

tinytot.summarize -- Abstractive-style document summarisation using TF-IDF sentence election.

- [summarizeDocument](summarizedocument.md)
- [summarizeFile](summarizefile.md)

## `tinytot.tools`

tinytot.tools — tool detection, parameter extraction, MCP tool matching.

- [detectInformationNeed](detectinformationneed.md)
- [detectToolUsage](detecttoolusage.md)
- [extractTopic](extracttopic.md)
- [matchToolFromAvailable](matchtoolfromavailable.md)

## `tinytot.tools_ext`

tinytot.tools_ext — Extended tool library for agentic TinyToT.

- [AudioTool](audiotool.md)
- [DataTool](datatool.md)
- [DocumentTool](documenttool.md)
- [FileTool](filetool.md)
- [ImageTool](imagetool.md)
- [MediaFetchTool](mediafetchtool.md)
- [SearchTool](searchtool.md)
- [ShellTool](shelltool.md)
- [Tool](tool.md)
- [ToolRegistry](toolregistry.md)
- [TranslateTool](translatetool.md)
- [VideoTool](videotool.md)
- [WebTool](webtool.md)
