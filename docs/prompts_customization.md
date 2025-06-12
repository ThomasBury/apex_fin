# Customizing Prompts

The behavior of the LLM agents in `apex-fin` is heavily guided by prompts. You can customize these prompts to tailor the analysis, tone, and output format to your specific needs.

## How Prompts are Loaded

Prompts are loaded using the `load_prompt` function found in [prompt_loader.md](reference/apex_fin/utils/prompt_loader.md). This function allows you to specify paths to custom prompt files in your `apex_fin.yaml` configuration.

If a path is provided in `apex_fin.yaml` for a specific prompt (e.g., `prompts.analysis`), `apex-fin` will attempt to load the content of that file. If the path is not specified, or the file cannot be loaded, a default, hardcoded prompt within the respective agent-building module will be used as a fallback.

## Configuring Custom Prompt Paths

In your `apex_fin.yaml` file, under the `prompts` section, you can specify paths to your custom prompt files. These paths should be relative to the project root directory.

**Example `apex_fin.yaml` snippet:**

```yaml
prompts:
  team: "custom_prompts/my_custom_team_prompt.txt"
  analysis: "custom_prompts/detailed_analysis_instructions.md"
  comparison: "custom_prompts/competitor_focus_prompt.txt"
  # ... other prompts
```

In this example:

* The Team Agent would use the content from `custom_prompts/my_custom_team_prompt.txt`.
* The Analysis Agent would use `custom_prompts/detailed_analysis_instructions.md`.

Create a directory like `custom_prompts` in your project root to store your custom prompt files.

## Writing Effective Prompts

When writing custom prompts, consider the following:

* **Be Specific and Clear:** Clearly define the agent's persona, goal, expected input (if any), required tasks, and desired output format.
* **Structure:** Use Markdown or clear text formatting within your prompt files to delineate sections like "Persona," "Goal," "Input," "Tasks," "Output Format," and "Constraints." This helps the LLM understand the instructions better.
* **Output Format Enforcement:** If you need a specific output format (e.g., Markdown tables, JSON), explicitly state this and provide examples if necessary. The `ANALYSIS_PROMPT` in [analysis_instructions.md](reference/apex_fin/prompts/analysis_instructions.md) is a good example of enforcing a Markdown table structure.
* **Constraints:** Include critical constraints, such as "Do NOT include any introductory phrases" or "Base your analysis strictly on the provided data."
* **Iterate:** Prompt engineering is often an iterative process. Start with a base prompt (you can copy the defaults from [prompts/index.md](reference/apex_fin/prompts/index.md)) and refine it based on the agent's output.
* **Placeholders and Templating:** Some prompts, like the `RISK_PROMPT_TEMPLATE` in [risk_instructions.md](reference/apex_fin/prompts/risk_instructions.md), use Jinja2 templating. This allows dynamic information (e.g., `risk_name`, `context`, `focus`) to be injected into the prompt at runtime. If you are customizing such prompts, ensure your custom file maintains the required template variables.

## Example: Customizing the Analysis Prompt

Suppose you want the Analysis Agent to focus more on future outlook and less on historical data.

1. **Copy the default prompt:** Start by copying the content of [analysis_instructions.md](reference/apex_fin/prompts/analysis_instructions.md) (e.g., `AUTO_ANALYSIS_PROMPT`) into a new file, say `custom_prompts/future_focused_analysis.txt`.
2. **Modify the content:** Adjust the instructions within `future_focused_analysis.txt` to emphasize future prospects, potential growth drivers, and analyst forward-looking statements. You might reduce the emphasis on past performance metrics.
3. **Update `apex_fin.yaml`:**

    ```yaml
    prompts:
      analysis: "custom_prompts/future_focused_analysis.txt"
    ```

    Now, when the Analysis Agent is run, it will use your custom instructions.

## Default Prompts Location

The default prompts are located within the [prompts/index.md](reference/apex_fin/prompts/index.md) directory (e.g., `analysis_instructions.py`, `comparison_instructions.py`, etc.). Reviewing these files is a good starting point for understanding their structure and content before creating your own customizations.
