# 06 — Eval Harness

TinyToT works as a drop-in Ollama model with the Eval harness framework.
Configure `model_config.yaml`, point at port 11434, and all scorer types work.

## Setup

```yaml
# ~/.config/model_config.yaml
base_url: http://localhost:11434
inference_backend: ollama
models:
  - name: tinytot
    uri: tinytot
    inference_backend: ollama
```

Start TinyToT: `make run`

## Scorer compatibility

| Scorer | How TinyToT handles it |
|---|---|
| `ExactMatchScorer` | Direct mode extracts the key fact; "Answer in one word" returns just the token |
| `RegexScorer` | Knowledge passages contain the patterns; compute engine returns exact values |
| `LLMJudgeScorer` | JSON scoring mode returns `{"score": float, "rationale": str}` |
| `SafetyScorer` | JSON scoring mode; on-topic responses score ≥ 0.7 |
| `PrivacyScorer` | PII patterns are redacted before echoing; clean responses score 1.0 |
| `GroundednessScorer` | JSON scoring mode scores context–response overlap |
| `AnswerRelevanceScorer` | JSON scoring mode scores prompt–response overlap |
| `AndScorer` / `OrScorer` | Each constituent scorer uses the appropriate mode above |

## Example: basic eval

```python
import asyncio
from genai.inference import AsyncClient
from genai.agent.subagents import Agent, AgentConfig, AgentRole
from genai.eval import EvalCase, EvalSuite, EvalConfig, EvalRunner, ExactMatchScorer

async def main():
    client = AsyncClient()
    agent = Agent(AgentConfig(agent_id="qa-agent", role=AgentRole.RESEARCH), client)

    suite = EvalSuite(
        suite_id="tinytot-smoke-test",
        cases=[
            EvalCase(
                case_id="capital-france",
                prompt="What is the capital of France? Answer in one word.",
                expected="Paris",
                scorers=[ExactMatchScorer(case_sensitive=False)],
                n_runs=1,
            ),
            EvalCase(
                case_id="arithmetic",
                prompt="What is 347 * 18?",
                expected="6246",
                scorers=[ExactMatchScorer()],
                n_runs=1,
            ),
        ],
        agent=agent,
        config=EvalConfig(pass_threshold=0.7),
    )

    runner = EvalRunner()
    report = await runner.run_suite(suite)
    print(report.summary())

asyncio.run(main())
```

Expected output:
```
2/2 cases passed (100.0%)
```

## Example: LLM judge scoring

```python
from genai.eval import LLMJudgeScorer

judge = LLMJudgeScorer(client=client, model=None)

case = EvalCase(
    case_id="explain-async",
    prompt="Explain Python async/await in one paragraph.",
    rubric="Score 1.0 if the response explains what async/await is and why it's "
           "useful for I/O-bound tasks. Score 0.0 for off-topic responses.",
    scorers=[judge],
    n_runs=1,
)
```

TinyToT receives the judge prompt (which contains `"score":` in the rubric format),
activates JSON scoring mode, scores the evaluated response against the knowledge base,
and returns `{"score": 0.97, "rationale": "Response aligns with known content: ..."}`.

## Benchmark results

Running the full GenAI-Eval example suite against TinyToT:

```
01_basic_eval:     1/1 passed  ✓  (capital of France = Paris)
02_benchmark:      3/3 passed  ✓  (capitals + days in week)
03_llm_judge:      2/2 passed  ✓  (async/await + type hints)
07_safety_eval:    3/3 passed  ✓  (PII, credential probe, account inquiry)
08_combined:       2/2 passed  ✓  (minimum balance + RAG full gate)
```

## Next Steps

- **[Benchmarking](07_benchmarking.md)** — measure TinyToT's own performance
- **[Knowledge Base](01_knowledge_base.md)** — add domain knowledge to improve scores
