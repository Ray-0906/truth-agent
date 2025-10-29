# News & Information Verification Agent

## Architecture Overview

- **ContentRoutingAgent** (LLM) triages every submission, classifies it into news / fact / scam intents, invokes the matching lane via `AgentTool`, and always finishes by calling the final reporting agent.
- Each verification lane lives in `adk_agents/news_info_verification/lanes/<lane>/`:
  - `sub_agents/` holds LLM workers (one per upstream data source) that publish structured JSON into `session.state`.
  - `merge.py` consolidates the fan-out outputs into Markdown formatted for downstream use.
  - `__init__.py` exposes the lane factory (e.g. `create_scam_check_agent`).
- `tools/` exposes FunctionTools that call real external APIs (GNews, Google Fact Check, VirusTotal) and relay their JSON payloads.
- `config.py` centralises the Gemini model ID and all session state keys.
- `reporting/final_report.py` contains the `FinalProcessingAgent`, which stitches lane summaries into the final Markdown.
- `router.py` wires the lane agents and final processor together and embeds the routing playbook.
- `agent.py` exposes `root_agent` for ADK loaders and the factory helper for custom runs.

``` 
adk_agents/news_info_verification/
├── agent.py
├── config.py
├── lanes/
│   ├── __init__.py
│   ├── fact/
│   │   ├── __init__.py
│   │   ├── merge.py
│   │   └── sub_agents/
│   │       ├── __init__.py
│   │       ├── fact_perplexity.py
│   │       └── fact_primary.py
│   ├── news/
│   │   ├── __init__.py
│   │   ├── merge.py
│   │   └── sub_agents/
│   │       ├── __init__.py
│   │       ├── news_api.py
│   │       ├── news_fact_checker.py
│   │       └── news_perplexity.py
│   └── scam/
│       ├── __init__.py
│       ├── merge.py
│       └── sub_agents/
│           ├── __init__.py
│           ├── scam_link.py
│           ├── scam_perplexity.py
│           └── scam_sentiment.py
├── reporting/
│   ├── __init__.py
│   └── final_report.py
└── router.py
```

## Behaviour Summary

1. **Routing**: `ContentRoutingAgent` reads the latest user message, inspects existing lane summaries, and decides which intents apply. It then calls the matching `NewsCheckAgent`, `FactCheckAgent`, and/or `ScamCheckAgent` tools exactly once each before invoking `FinalProcessingAgent`.
2. **Lane Execution**: Each lane runs a `ParallelAgent` with specialised workers. Tool-enabled workers (news API, fact primary, scam link) call their FunctionTool, capture raw JSON, and persist it to `session.state` via keys in `config.StateKeys`.
3. **Aggregation**: Lane merge agents consume the worker state blobs, surface any `status=error` or `status=no_data` messages verbatim, and emit deterministic Markdown sections (`## <Lane> Verification`) including numbered source lists. Results land in the respective `*_SUMMARY` keys.
4. **Final Report**: `FinalProcessingAgent` merges the lane Markdown without rephrasing, populates per-lane summaries and confidence lines, records which lanes executed or were skipped (with reasons), aggregates unique sources into a global `## Sources` list, and stores everything under `final_report`.

The resulting response mirrors the earlier structured format while now providing explicit citations and execution tracebacks.

## Tooling & Data Flow

| Tool | Module | External dependency | Session output |
| ---- | ------ | ------------------- | --------------- |
| `fetch_news_evidence` | `tools/news_tools.py` | GNews Search (`GNEWS_API_TOKEN`) | `STATE_KEYS.NEWS_API` |
| `lookup_fact_checks` | `tools/fact_tools.py` | Google Fact Check (`GOOGLE_FACT_CHECK_API_KEY`) | `STATE_KEYS.FACT_PRIMARY` and via news fact checker |
| `scan_urls_with_virustotal` | `tools/scam_tools.py` | VirusTotal URL lookup (`VT_API_KEY`) | `STATE_KEYS.SCAM_LINK` |

Each FunctionTool expects the LLM to supply `claim: str`. If a lane omits the argument, the tool retrieves the claim text from the session via `context_helpers`. Tool docstrings double as user-visible descriptions, so keep them precise.

## Implementation Notes

- All sub-agents currently use `gemini-2.0-flash`. Switch `MODEL` in `config.py` to retarget a different Gemini build or Vertex endpoint.
- Tool-backed workers now replace the prior prompt-only heuristics:
  - `NewsApiAgent` calls `fetch_news_evidence` to fetch licensed articles.
  - `NewsFactCheckerAgent` reuses the fact-check FunctionTool so news verification also surfaces registry verdicts.
  - `FactPrimaryAgent` and `MaliciousLinkAgent` echo their tool JSON responses verbatim for traceability.
- Required environment variables (set in `.env` or the shell before `adk web`):
  - `GNEWS_API_TOKEN`
  - `GOOGLE_FACT_CHECK_API_KEY`
  - `VT_API_KEY`
  - Gemini auth per ADK docs (`GOOGLE_API_KEY` or Vertex ADC).
- Lane merge prompts output consistent Markdown patterns with numbered source sections; this enables `FinalProcessingAgent` to deduplicate citations and annotate lane execution.
- The routing prompt documents explicit skip reasons to keep the final report transparent when a lane is omitted (e.g., no URLs → scam lane skipped).
- The package avoids circular imports by exposing factories in `__init__.py` modules.
- Merge and report prompts explicitly instruct agents to preserve the full URLs returned by the API tools so the final sources list points at the exact article or ruling, not just the domain.
- The GNews client now sanitises API payloads, discarding placeholder strings such as “invalid URL” and only surfacing articles with verifiable `http(s)` links so downstream summaries retain clickable citations.

## Prompting Strategy

- **Complete context**: Tool workers rely on real API payloads and must report `status=no_data` or `status=error` when appropriate, ensuring downstream agents know why evidence is missing.
- **Consistency**: Shared schema fields (`status`, `confidence`, `verdict`) and templated Markdown reduce the chance of Format drift across lanes.
- **User alignment**: The router narrates lane coverage, while the final agent repeats the executed/skipped breakdown and residual risks so users can see the investigation footprint at a glance.
- **Error resilience**: Prompts instruct agents to surface tool failures verbatim, allowing human reviewers to debug API issues quickly.
- **Evaluation hooks**: Fixed headings (`## News Verification`, `## Sources`, etc.) support regression testing and diff-based QA on both lane and final outputs.

## Final Report Format

`FinalProcessingAgent` emits Markdown that mirrors the structure below. Lane summaries are inserted verbatim from the merge agents, so any change upstream propagates transparently.

```
# Verification Report
## Report Summary
Single paragraph (≤3 sentences) that tells the user whether the claim is verified, refuted, mixed, or likely a scam, cites the headline confidence, references one or two key evidence points or gaps, and notes any skipped/failed lanes.

## Claim Overview
- paraphrase: …
- submission_time: …

## News Assessment
- summary: …
- confidence: …
- sources:
  * …

## Fact Assessment
…

## Scam Risk
…

## Lane Execution
- executed: …
- skipped: …

## Final Verdict
- outcome: …
- confidence: …
- residual_risks:
  * …

## Sources
1. …
```

Numbered sources roll up unique citations from all lanes, ensuring the report always references the real API outputs that informed the decision.

> **Note:** Source sections must keep the full URLs from the tool responses (no domain-only shortening) so that reviewers can click through to the precise articles, fact checks, or VirusTotal reports.

## TODO / Planned Enhancements

- Add unit tests to validate state keys and lane wiring.
- Provide evaluation prompts / fixtures leveraging ADK eval tooling.

## Troubleshooting

- If import resolution fails, confirm the `google-adk` package is installed in the active environment.
- For orchestration reference, see `refs/adk-docs/examples/python/snippets/agents/workflow-agents/parallel_agent_web_research.py`.
- Ensure environment variables for Gemini authentication are set per ADK docs before running `adk run`.
