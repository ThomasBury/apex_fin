# Detailed Configuration

`apex-fin` uses a combination of an environment file (`.env`) for sensitive keys and a YAML file (`apex_fin.yaml`) for most other configurations. This allows for flexible and secure customization of the tool's behavior.

## Environment File (`.env`)

The `.env` file is used to store sensitive information, primarily API keys. It should be placed in the root directory of the project and **should not be committed to version control**.

Create a `.env` file in the project root with the following content:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
Replace "YOUR_GEMINI_API_KEY_HERE" with your actual Gemini API key.
```

## YAML Configuration (apex_fin.yaml)

The `apex_fin.yaml` file allows you to customize various aspects of the application, from LLM settings to report generation options and prompt overrides. If this file is not present in the project root, default settings (defined internally) will be used for these aspects. You can also specify a custom YAML configuration file path using the `--config` or `-c` CLI option.

Settings in a custom YAML file will override the defaults, and environment variables (like `GEMINI_API_KEY`) always take precedence for their specific settings.

Here's a breakdown of the `apex_fin.yaml` structure and available options (refer to your project's `apex_fin.yaml` for the most current example):

```yaml
llm:
  model: "gemini/gemini-1.5-flash"  # Specifies the LLM model to use (e.g., from LiteLLM supported models)
  base_url: "https://generativelanguage.googleapis.com/v1beta"  # Optional: Custom base URL for the LLM API

report:
  markdown_template_path: "custom_templates/report_template.md"  # Optional: Path to a custom Markdown template for the full report
  enable_polishing: true  # Boolean: Whether to run the polishing agent on the full report for refinement
  include_context: true # Boolean: Whether to include the contextual risk assessment section in the full report
  include_news: true    # Boolean: Whether to include the financial news section in the full report

prompts:
  # Optional: Paths to custom prompt files. Paths are relative to the project root.
  # If a path is provided, the content of that file will be used instead of the default internal prompt.
  team: "custom_prompts/team.txt"
  analysis: "custom_prompts/analysis.txt"
  comparison: "custom_prompts/comparison.txt"
  evaluation: "custom_prompts/evaluation.txt"
  news: "custom_prompts/news.txt"
  # Add other prompt keys here if your application supports more (e.g., risk-specific prompts)

risk:
  enabled: ["macroeconomic", "geopolitical", "climate", "regulatory"] # List of risk types to include in the 'think' and 'fullreport' (if include_context is true)
  guidelines:
    macroeconomic: |
      - Interest rate sensitivity
      - FX volatility
      - Inflation and central bank policy
    geopolitical: |
      - Policy instability
      - Regional conflicts or sanctions
      - Global supply chain disruptions
    # Add guidelines for other enabled risks
  tools:
    macroeconomic: ["DuckDuckGoTools"] # List of tool names (from TOOL_REGISTRY in risk_tools.md) for each risk
    geopolitical: ["DuckDuckGoTools"]
    # Add tool configurations for other enabled risks
```

```yaml
llm:
  model: "gemini/gemini-2.0-flash"  # gemini/gemini-2.5-flash-preview-05-20
  base_url: "https://generativelanguage.googleapis.com/v1beta"  # Optional URL

report:
  markdown_template_path: "custom_templates/report_template.md"  # Optional path for custom report template
  enable_polishing: true  # Whether to run the polishing agent on the full report
  include_context: true # Whether to include the contextual risk assessment section
  include_news: true    # Boolean: Whether to include the financial news section in the full report

prompts:
  # Optional: Paths to custom prompt files. Paths are relative to the project root.
  # If a path is provided, the content of that file will be used instead of the default internal prompt.
  team: "custom_prompts/team.txt"  # Optional path to custom team prompt
  analysis: "custom_prompts/analysis.txt"  # Optional path to custom analysis prompt
  comparison: "custom_prompts/comparison.txt"  # Optional path to custom comparison prompt
  evaluation: "custom_prompts/evaluation.txt"  # Optional path to custom evaluation prompt
  news: "custom_prompts/news.txt"  # Optional path to custom news prompt

risk:
  # List of risk types to include in the 'think' and 'fullreport' (if include_context is true)
  # Guidelines must be provided for each risk type
  enabled: ["macroeconomic", "geopolitical", "climate", "regulatory"]

  guidelines:
    macroeconomic: |
      - Interest rate sensitivity
      - FX volatility
      - Inflation and central bank policy
    geopolitical: |
      - Policy instability
      - Regional conflicts or sanctions
      - Global supply chain disruptions
    climate: |
      - Carbon emissions exposure
      - Physical climate risk (drought, flooding)
      - Regulatory ESG disclosure risk
    regulatory: |
      - Ongoing compliance obligations
      - Risk of new sectoral regulation
      - Dependency on licensed operations

  tools:
    # List of tool names (from TOOL_REGISTRY in risk_tools.md) for each risk
    # possible extention in next iterations
    macroeconomic: ["DuckDuckGoTools"]
    geopolitical: ["DuckDuckGoTools"]
    climate: ["DuckDuckGoTools", "ThinkingTools"]
    regulatory: ["DuckDuckGoTools"]
```




### Key Sections

* **`llm`**:
  * `model`: Defines the specific language model to be used (e.g., "gemini/gemini-1.5-flash"). Ensure this model is compatible with your LiteLLM setup and API key.
  * `base_url`: (Optional) If you are using a proxy or a self-hosted LLM that requires a custom API endpoint.
* **`report`**:
  * `markdown_template_path`: (Optional) If you want to customize the structure of the final Markdown report, provide a path to your Jinja2 template file.
  * `enable_polishing`: Set to `true` to have a final LLM agent review and refine the entire report. Set to `false` to skip this step.
  * `include_context`: Set to `true` to include the "Contextual Considerations" section (generated by the ThinkingAgent) in the fullreport.
  * `include_news`: Set to `true` to include the "Financial News" section (generated by the NewsAgent) in the fullreport.
* **`prompts`**:
    Allows you to override the default system prompts used by various agents. Provide a file path (relative to the project root) for any prompt you wish to customize. See the "Customizing Prompts" documentation for more details.
* **`risk`**:
  * `enabled`: A list of risk categories that the ThinkingAgent will analyze.
  * `guidelines`: A dictionary where each key is a risk name (from `enabled`) and the value is a multi-line string providing specific focus points or questions for the LLM to consider for that risk.
  * `tools`: A dictionary where each key is a risk name and the value is a list of tool names (e.g., "DuckDuckGoTools", "ThinkingTools") that the specialized risk agent can use.

## Settings Precedence

Configuration settings are merged from multiple sources with the following precedence (highest to lowest):

1. Environment Variables (e.g., `GEMINI_API_KEY` from `.env`).
2. Custom YAML file (specified via `--config` CLI option).
3. Default `apex_fin.yaml` (if present in the project root).
4. Internal default application settings.

This layered approach provides flexibility in managing your configurations for different environments or experiments.
