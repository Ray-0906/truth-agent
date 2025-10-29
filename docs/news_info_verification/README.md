# News & Information Verification Agent

## Overview

The news & information verification system is an [ADK](https://google.github.io/adk-docs/) application that orchestrates multiple `LlmAgent` and workflow agents to classify user submissions, gather evidence from external services, and deliver a consolidated Markdown report. The root agent (`adk_agents.news_info_verification.agent.root_agent`) acts as a custom router: it inspects each message, determines which verification lanes apply (`news`, `fact`, `scam`), delegates work to specialised agents via `AgentTool`, and always finishes by calling the final report compiler. Every agent adheres to ADK patterns highlighted in the official LLM agent and workflow agent guides, maintaining deterministic control flow while allowing individual workers to leverage Gemini reasoning.

## Key Components

- `agent.py` defines the routing `LlmAgent`. Custom `NormalizedAgentTool` wrappers normalise nested function-call payloads, while `FinalReportAgentTool` prevents redundant recomputation if the report already exists in session state.
- `config.py` centralises the default Gemini model (`gemini-2.0-flash`) and the canonical session state contract used across lanes.
- `lanes/<lane>/` holds the workflow for each intent. A `ParallelAgent` fans out to worker LLM agents that call real APIs, followed by a merge LLM agent that emits Markdown aligned with the final report skeleton.
- `tools/` exposes `FunctionTool` implementations that call external services (GNews, Google Fact Check API, VirusTotal). Tool docstrings describe usage so the LLM can select the correct capability during function calling.
- `reporting/final_report.py` constructs the deterministic `FinalProcessingAgent`, which stitches lane outputs into the final Markdown document.
- `services/` contains HTTP clients and helper utilities used inside the tools for authentication, payload sanitisation, and context extraction.

### Directory Layout

```
adk_agents/news_info_verification/
├── agent.py
├── config.py
├── lanes/
│   ├── fact/
│   │   ├── merge.py
│   │   └── sub_agents/
│   │       ├── fact_perplexity.py
│   │       └── fact_primary.py
│   ├── news/
│   │   ├── merge.py
│   │   └── sub_agents/
│   │       ├── news_api.py
│   │       ├── news_fact_checker.py
│   │       └── news_perplexity.py
│   └── scam/
│       ├── merge.py
│       └── sub_agents/
│           ├── scam_link.py
│           ├── scam_perplexity.py
│           └── scam_sentiment.py
├── reporting/
│   └── final_report.py
├── services/
│   ├── context_helpers.py
│   ├── factcheck_client.py
│   ├── gnews_client.py
│   ├── perplexity_client.py
│   ├── text_utils.py
│   └── virustotal_client.py
└── tools/
        ├── fact_tools.py
        ├── news_tools.py
        └── scam_tools.py
```

## Verification Lanes

Each lane maps to a deterministic workflow agent that encapsulates the sourcing strategy for that intent.

### News Lane

- `NewsParallelFanout` (`ParallelAgent`) dispatches three workers:
  - `NewsApiAgent` calls `fetch_news_evidence` to pull licensed coverage.
  - `NewsFactCheckerAgent` reuses the fact-check tool, allowing cross-lane sharing of authoritative verdicts.
  - `NewsPerplexityAgent` prompts Gemini to synthesise secondary open-web perspective when API data is sparse.
- `NewsMergeAgent` consumes worker JSON from session state and emits a Markdown section titled `## News Verification`, including numbered references and explicit error propagation if upstream tools return `status=error` or `status=no_data`.

### Fact Lane

- `FactParallelFanout` fans out to:
  - `FactPrimaryAgent`, which mirrors an ADK FunctionTool to call Google Fact Check API and return its JSON verbatim.
  - `FactPerplexityAgent`, which prompts Gemini to summarise consensus and highlight gaps.
- `FactMergeAgent` fuses the feeds into Markdown with fixed bullet labels (`consensus_verdict`, `confidence_range`, `registry_alignment`) and carries over reference numbering so the final report can deduplicate sources.

### Scam Lane

- `ScamParallelFanout` runs:
  - `MaliciousLinkAgent` (tool-backed) leveraging the VirusTotal client.
  - `ScamPerplexityAgent` focusing on behavioural red flags detected in unstructured communication.
  - `ScamSentimentAgent` capturing tone cues that indicate urgency, threats, or financial pressure.
- `ScamMergeAgent` emits a Markdown block captioned `## Scam Verification`, edging towards risk scoring and capturing link intelligence.

## Session State Contract

`config.StateKeys` enumerates the immutable state keys and ensures consistent naming across lanes, tools, and the final report.

| Purpose | Key |
| --- | --- |
| Raw GNews evidence | `news_api_signal` |
| Fact-check registry pull used in news lane | `news_fact_checker_signal` |
| Gemini open-web synthesis for news | `news_perplexity_signal` |
| News lane Markdown summary | `news_check_summary` |
| Primary fact-check API response | `fact_primary_signal` |
| Gemini secondary fact analysis | `fact_perplexity_signal` |
| Fact lane Markdown summary | `fact_check_summary` |
| Scam sentiment analysis | `scam_sentiment_signal` |
| VirusTotal link intelligence | `scam_link_signal` |
| Gemini scam heuristic write-up | `scam_perplexity_signal` |
| Scam lane Markdown summary | `scam_check_summary` |
| Final Markdown report returned to the user | `final_report` |

Every worker agent writes to one of the raw signal keys via its `output_key`. Merge agents read those signals synchronously (after the parallel fanout completes) and publish structured Markdown to the `*_SUMMARY` keys. The router and final report agents only reference these summary keys, ensuring a clean separation between data acquisition and presentation.

## End-to-End Invocation Flow

1. **User message received** – The `root_agent` (`ContentRoutingAgent`) inspects the latest message and existing session state.
2. **Intent classification** – Based on heuristics in the router prompt, the agent selects relevant intents (`news`, `fact`, `scam`). Skip reasons are recorded for omitted intents so downstream reporting remains transparent.
3. **Lane execution** – For each selected intent, the router invokes the corresponding `AgentTool` with `{"request": "<claim>"}`. `NormalizedAgentTool` guarantees the payload is flattened before dispatching to the workflow agent.
4. **Tool fanout** – Workflow agents run their parallel workers. Tool-backed workers call out to HTTP clients housed in `services/`, normalise the JSON payloads, and push results to state.
5. **Lane merge** – Merge agents convert raw signals into deterministic Markdown, copying error messages verbatim and enumerating references with full URLs.
6. **Final report** – After all requested lanes finish, the router invokes `FinalProcessingAgent` exactly once. A guard inside `FinalReportAgentTool` returns the cached report if the key already exists, preventing duplicate execution when users follow up within the same session.
7. **Response emission** – The `root_agent` returns the Markdown stored in `state['final_report']` as the user-facing answer.

## External Integrations & Environment Variables

The agent package depends on real-time data from several APIs. Configure the following before running `adk` commands:

- `GNEWS_API_TOKEN` for licensed news search via `tools/news_tools.py`.
- `GOOGLE_FACT_CHECK_API_KEY` for Google Fact Check API access (`tools/fact_tools.py`).
- `VT_API_KEY` for VirusTotal link scanning (`tools/scam_tools.py`).
- Gemini authentication variables as documented in ADK (either `GOOGLE_API_KEY` for AI Studio or Vertex AI project variables with ADC).

All tools implement defensive fallbacks: missing credentials or empty claims return structured `status="error"` payloads with explanatory notes so the user sees why evidence could not be collected.

## Running the Agent Locally

1. Install Python dependencies: `pip install -r requirements.txt`.
2. Populate the environment variables above (for Windows PowerShell: `setx GNEWS_API_TOKEN "<token>"`).
3. Launch the ADK Dev UI: `adk web adk_agents.news_info_verification.agent:root_agent`.
4. Alternatively, run in the terminal: `adk run adk_agents.news_info_verification.agent:root_agent` and chat inline.
5. Use `.env` with `python-dotenv` if you prefer local configuration files; the ADK CLI automatically loads it when present.

The Dev UI mirrors the ADK documentation experience: you can inspect event logs, tool calls, and session state deltas to confirm each lane executed as expected.

## Serving via API Server

- **Project root:** Run all commands from the repository root (`c:\Users\astra\Desktop\Adk-agent1`). Activate your Python environment first.
- **Environment:** Export every credential required for live tool calls:
  - `GOOGLE_API_KEY` (or Vertex credentials) and `GOOGLE_GENAI_USE_VERTEXAI=True`
  - `GNEWS_API_TOKEN`, `GOOGLE_FACT_CHECK_API_KEY`, `VT_API_KEY`
  - In PowerShell, set temporary variables for the current session with `setx` for persistence or `$Env:GOOGLE_API_KEY = "<key>"` for immediate use.
- **Start the server:**
  - `adk api_server adk_agents/news_info_verification --host 0.0.0.0 --port 8000`
  - This exposes a FastAPI app with `/query` (batched response) and `/stream` (SSE streaming) endpoints.
- **Sample request:**
  - PowerShell: `Invoke-WebRequest -Uri http://localhost:8000/query -Method Post -ContentType 'application/json' -Body '{"session_id":"demo-session","user_input":"I saw a post claiming a new vaccine causes 5G connectivity issues."}'`
  - `session_id` is any stable identifier; reuse it to maintain context between turns.
- **Stop / redeploy:** Press `Ctrl+C` to terminate, then rerun the same command after code changes. Container or Cloud Run deployments can proxy the same command inside an image if needed.

## Final Report Format

`FinalProcessingAgent` emits Markdown using the skeleton below. Lane summaries drop straight into the relevant sections, preserving references and confidence scores supplied upstream.

```
# Verification Report
## Report Summary
<Overall verdict in 1-3 sentences>

## Claim Overview
- paraphrase: <restated claim>
- submission_time: <timestamp or 'unspecified'>

## News Assessment
- summary: <news lane summary or 'not requested'>
- confidence: <value or range>
- sources:
  * <Outlet - URL or 'none'>

## Fact Assessment
- summary: <fact lane summary or 'not requested'>
- confidence: <value or range>
- sources:
  * <Organization - URL or 'none'>

## Scam Risk
- summary: <scam lane summary or 'not requested'>
- confidence: <value or range>
- sources:
  * <Signal description - URL or 'n/a'>

## Lane Execution
- executed: <comma-separated list>
- skipped: <comma-separated list with reasons>

## Final Verdict
- outcome: <true|false|mixed|unknown>
- confidence: <value or range>
- residual_risks:
  * <bullet per known gap or 'none'>

## Sources
1. <Unique citations with full URLs>
```

The router and merge agents emphasise transparency: if a lane fails, the Markdown includes the originating error string, preventing silent degradation. Sources retain the exact URLs returned by each FunctionTool to maintain traceability back to the evidence corpus.

## Extensibility Checklist

- **Swap models** – update `MODEL` in `config.py` to target a different Gemini release or Vertex deployment.
- **Add a new lane** – create a sibling directory under `lanes/`, define worker sub-agents, register a merge agent, and expose a factory function in `lanes/__init__.py`. Wire it into the router prompt and tool list using a new `NormalizedAgentTool` instance.
- **Augment tools** – implement additional `FunctionTool` wrappers inside `tools/` and import them into the relevant worker agent. Follow ADK guidance on descriptive docstrings so the LLM selects the proper tool.
- **Evaluation** – author `.test.json` scenarios or an evalset referencing the final report schema. ADK’s evaluation framework can then score tool trajectory and final response quality per the docs in `refs/adk-docs/evaluate/`.

## Troubleshooting

- Missing credentials surface as `status="error"` payloads; inspect the Dev UI event log to confirm which variable is misconfigured.
- If the router skips a lane, check the skip reason embedded in the final Markdown and validate the routing prompt still matches your use case.
- Ensure `requests` is up to date; a duplicated constraint exists in `requirements.txt` and pip resolves to the latest declared version (`>=2.32.3`).
- For deeper ADK behaviour, consult the upstream docs mirrored in `refs/adk-docs/`—especially the sections on LLM agents, workflow agents, and custom agents—to understand how control flow and context propagation operate.
