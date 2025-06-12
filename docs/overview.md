# Overview and Architecture

## Agents & Their Responsibilities

Each agent module defines a part of the logic chain:

| Agent                  | Purpose                                              | API Reference                                                                                                                               |
| ---------------------- | ---------------------------------------------------- |---------------------------------------------------------------------------------------------------------------------------------------------|
| `analysis_agent.py`    | Performs core financial analysis of a single company | [analysis_agent.md](reference/apex_fin/agents/analysis_agent.md)                                                                            |
| `comparison_agent.py`  | Benchmarks company vs. competitors                   | [comparison_agent.md](reference/apex_fin/agents/comparison_agent.md)                                                                        |
| `thinking_agent.py`    | Injects macroeconomic and contextual risk analysis   | [thinking_agent.md](reference/apex_fin/agents/thinking_agent.md)                                                                            |
| `evaluation_agent.py`  | Assesses report quality and gives feedback (Used internally) | [evaluation_agent.md](reference/apex_fin/agents/evaluation_agent.md)                                                                        |
| `refinement_agent.py`  | (if enabled) Revises sections based on feedback (Used internally) | [refinement_agent.md](reference/apex_fin/agents/refinement_agent.md)                                                                        |
| `full_report_agent.py` | Generates a predefined full report sequence          | [full_report_agent.md](reference/apex_fin/agents/full_report_agent.md)                                                                      |
| `competitor_agent.py`  | (Potentially) gathers or ranks competitors (Used internally) | [competitor_agent.md](reference/apex_fin/agents/competitor_agent.md)                                                                        |
| `team_report.py`       | Runs multi-agent orchestration as a "team" (Experimental, not in CLI) | [report_team.md](reference/apex_fin/teams/report_team.md)                                                                                   |
| `base.py`              | Defines base logic/abstractions for agent execution  | [base.md](reference/apex_fin/agents/base.md)                                                                                                |

These are orchestrated either directly (CLI commands) or via a **central planner** (`team_report`).

## Prompts (Instructions) – in `prompts/`

Each agent is driven by its associated **prompt file**, which defines:

| File                         | Drives...                             | API Reference                                                                                                                               |
| ---------------------------- | ------------------------------------- |---------------------------------------------------------------------------------------------------------------------------------------------|
| `analysis_instructions.py`   | How the company analysis is done      | [analysis_instructions.md](reference/apex_fin/prompts/analysis_instructions.md)                                                             |
| `comparison_instructions.py` | What comparison logic is followed     | [comparison_instructions.md](reference/apex_fin/prompts/comparison_instructions.md)                                                         |
| `thinking_instructions.py`   | How contextual factors are considered | [thinking_instructions.md](reference/apex_fin/prompts/thinking_instructions.md)                                                             |
| `evaluation_instructions.py` | How quality is evaluated              | [evaluation_instructions.md](reference/apex_fin/prompts/evaluation_instructions.md)                                                         |
| `team_instructions.py`       | Master prompt coordinating all agents | [team_instructions.md](reference/apex_fin/prompts/team_instructions.md)                                                                     |

These prompts are often **static** but can be overridden. The default prompt files are located in [reference/apex_fin/prompts/index.md](reference/apex_fin/prompts/index.md).

They could be:

* Injected with runtime context (e.g., `ticker`, `sector`)
* Overridden by users (via config or custom folder)

## Configuration (`config.py` + YAML)

Settings affect how the app behaves globally:

| Source                        | Drives...                                                                                        | API Reference                                                                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |---------------------------------------------------------------------------------------------------------------------------------------------|
| `.env` + `pydantic-settings`  | Model/backend configs (e.g., `LLM_MODEL`, `GEMINI_API_KEY`)                                      |                                                                                                                                             |
| `apex_config.yaml` (optional) | Feature toggles: enabled agents, caching, section style, thresholds, prompt override paths, etc. |                                                                                                                                             |
| CLI `--config` flag           | Loads custom YAML for session                                                                    |                                                                                                                                             |

Configuration settings from `.env` and `apex_config.yaml` are merged, with YAML settings taking precedence. The resulting settings are managed by the [config.md](reference/apex_fin/config.md) class.

## Runtime Parameters (from CLI)

Your `typer` CLI exposes runtime flags that control execution:

| Flag           | Impact                                       |
| -------------- | -------------------------------------------- |
| `--output/-o`  | Writes the report to file                    |
| `--config/-c`  | Specifies a custom config YAML file          |

## Model Architecture

Depending on config, you can switch:

* Which LLM provider (e.g., Azure OpenAI vs Gemini)
* The `BASE_URL` or `LLM_MODEL`
* Potentially prompt format based on LLM requirements

## Report Logic (Hardcoded or Template-Driven)

Markdown structure is usually:

```markdown
# Full Investment Report: {TICKER}

## Company Analysis
<generated by analysis_agent>

## Competitor Comparison
<comparison_agent>

## Contextual Considerations
<thinking_agent>

## Recommendation
<output or summary>
```

But this could be **dynamic or user-specified** in future.

## Agent Output Flow / Orchestration Logic

Main orchestration types:

* **Single agent invocation** (e.g. `analyze`, `compare`)
* **Sequential flow** (e.g., `fullreport` command)
* **Multi-agent coordination** (e.g., `teamreport` - currently experimental)
* **Dynamic routing based on natural language** (not currently exposed in CLI)

In advanced cases (like team-based), outputs are **passed between agents**, and **feedback evaluation** can control whether a report is generated or revision is triggered.
