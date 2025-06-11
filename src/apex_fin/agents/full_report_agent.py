import logging
from agno.agent import Agent
from agno.team import Team
from apex_fin.config import settings
from apex_fin.agents.analysis_agent import build_analysis_agent, _fetch_financial_data_for_agent
from apex_fin.agents.comparison_agent import compare_company
from apex_fin.agents.thinking_agent import build_thinking_agent
from apex_fin.agents.news_agent import get_financial_news
from apex_fin.agents.base import create_agent
from apex_fin.utils.ticker_validation import validate_and_get_ticker

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def build_full_report(ticker: str) -> str:
    """
    Generate a complete financial report using all relevant agents.

    Configuration from `settings` determines:
      - Whether to include contextual risk assessment
      - Whether to polish the final report

    Returns
    -------
    str
        The final Markdown-formatted investment report.
    """
    
    ticker, company_name = validate_and_get_ticker(ticker)
    
    analysis_agent = build_analysis_agent()
    # The comparison_agent is built and used within the compare_company function
    thinking_agent = build_thinking_agent(ticker)
    polishing_agent = (
        _build_polishing_agent() if settings.report_enable_polishing else None
    )

    try:
        logger.info(f"Full Report: Fetching financial data for analysis section for {ticker}...")
        input_json_for_analysis = _fetch_financial_data_for_agent(ticker, logger)

        # Check if pre-fetch returned an error payload
        if '"error":' in input_json_for_analysis and "Data pre-fetch failed" in input_json_for_analysis:
            error_msg = f"Data pre-fetch failed for '{ticker}' during full report generation. Details: {input_json_for_analysis}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Full Report: Running analysis agent for {ticker} with pre-fetched data...")
        analysis_run_response = analysis_agent.run(input_json_for_analysis)
        
        section_analysis: str
        if hasattr(analysis_run_response, "content") and analysis_run_response.content:
            section_analysis = str(analysis_run_response.content).strip()
        else:
            error_msg = f"Analysis agent returned no content or empty content for {ticker} in full report. Response: {analysis_run_response}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not section_analysis or len(section_analysis) < 20: # Threshold for meaningful summary
            error_msg = f"Analysis agent returned an empty or insufficient summary for {ticker} in full report. Summary: '{section_analysis[:100]}...'"
            logger.warning(error_msg) # Log as warning, but raise to stop potentially poor report
            raise ValueError(error_msg)
        logger.info(f"Full Report: Successfully generated analysis section for {ticker}.")

        section_comparison = compare_company(
            ticker_or_list_input=ticker, 
            primary_company_analysis=section_analysis # Pass the generated markdown summary
        )

        section_context = ""
        if settings.report_include_context:
            section_context = _run_agent(
                thinking_agent,
                f"Generate a comprehensive risk assessment report for {ticker}.",
            )
            
        section_news = ""
        if settings.report_include_news:
             section_news = get_financial_news(ticker)

        raw_report = _assemble_raw_report(
            analysis=section_analysis,
            comparison=section_comparison,
            context=section_context,
            news=section_news,
        )

        return (
            _polish_report(polishing_agent, raw_report)
            if polishing_agent
            else raw_report
        )

    except Exception as e:
        logger.error(f"Failed to generate report for {ticker}: {e}")
        raise


def _run_agent(agent: Agent | Team, prompt: str) -> str:
    """Executes an agent or team with a given prompt and returns its content.

    Parameters
    ----------
    agent : Agent | Team
        The agent or team instance to run.
    prompt : str
        The prompt to send to the agent or team.

    Returns
    -------
    str
        The textual content from the agent's or team's response.

    Raises
    ------
    ValueError
        If the agent or team returns empty content.
    """
    result = agent.run(prompt)
    content = (
        result.content.strip() if hasattr(result, "content") else str(result).strip()
    )
    if not content:
        raise ValueError("Agent returned empty content.")
    return content


def _assemble_raw_report(analysis: str, comparison: str, context: str = "", news: str = "") -> str:
    """Combines individual report sections into a raw Markdown report.

    Parameters
    ----------
    analysis : str
        The company analysis section in Markdown format.
    comparison : str
        The competitor comparison section in Markdown format.
    context : str, optional
        The contextual considerations section in Markdown format. Defaults to "".
    news : str, optional
        The financial news section in Markdown format. Defaults to ""

    Returns
    -------
    str
        The assembled raw Markdown report.
    """
    report = f"""## Company Analysis

{analysis}

## Competitor Comparison

{comparison}
"""
    if news:
        report += f"\n## Financial News\n\n{news}"
        
    if context:
        report += f"\n## Contextual Considerations\n\n{context}"

    return report.strip()


def _build_polishing_agent() -> Agent:
    """Constructs an agent for refining and polishing a Markdown report.

    Returns
    -------
    Agent
        A configured agent tasked with improving the structure, flow,
        and formatting of a financial report.
    """
    return create_agent(
        instructions=[
            "You are a financial editor tasked with refining a multi-section financial report.",
            "Improve structure, flow, and clarity. Remove redundancies and ensure best practices Markdown formatting.",
            "The report will contain sections such as: '## Company Analysis', '## Competitor Comparison', '## Financial News', and '## Contextual Considerations' (if provided). Ensure these sections are well-integrated.",
            "Add a final section '## Final Recommendation' based on all inputs.",
            "Respond with only the polished Markdown output, not internal thoughts or comments.",
        ],
        markdown=True,
        show_tool_calls=False,
    )


def _polish_report(polishing_agent: Agent, raw_report: str) -> str:
    """Uses a polishing agent to refine a raw Markdown report.

    The agent aims to improve layout, narrative flow, and overall presentation.
    If polishing fails, the raw report is returned with a warning.

    Parameters
    ----------
    polishing_agent : Agent
        The agent configured for polishing reports.
    raw_report : str
        The raw Markdown report content to be polished.

    Returns
    -------
    str
        The polished Markdown report, or the raw report if polishing fails.
    """
    try:
        prompt = f"""Please polish the following financial report content.
Respond with a clean, well-formatted Markdown version.

Report:
---
{raw_report}
---
"""
        return _run_agent(polishing_agent, prompt)
    except Exception as e:
        logger.warning("Polishing failed, returning raw report. Error: %s", e)
        return "# Full Financial Report (Raw)\n\n" + raw_report


if __name__ == "__main__":
    # The module already has `logger = logging.getLogger(__name__)`
    # and `logging.basicConfig(level=logging.INFO)`.
    # This check ensures it's configured if run standalone and not imported.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    logger.info("Testing Full Report Agent (via build_full_report function)...")
    try:
        if not settings.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        # Ensure thinking_agent dependencies are met (similar to thinking_agent test)
        if not hasattr(settings, "enabled_risks") or not settings.enabled_risks:
            logger.warning(
                "`settings.enabled_risks` is not configured for full_report. Using a default for testing."
            )
            settings.enabled_risks = ["test_risk_for_full_report"]
            if not hasattr(settings, "risk_guidelines"):
                settings.risk_guidelines = {}
            settings.risk_guidelines["test_risk_for_full_report"] = (
                "Briefly assess this test risk for the full report."
            )

        # Ensure prompt paths are set if not loaded automatically by your settings mechanism.
        # Example: settings.prompt_paths.analysis, .comparison, etc.
        # This is crucial if load_prompt is used and paths are not default/discoverable.
        # Assuming they are correctly configured by the `settings` object for this test.

        ticker_for_report = "VW"  # Example ticker
        logger.info(f"Generating full report for: {ticker_for_report}")

        full_report_md = build_full_report(ticker_for_report)

        if full_report_md:
            logger.info(
                f"Full report for {ticker_for_report}:\n{full_report_md}"
            )  # Potentially very long
        else:
            logger.error(f"Failed to generate full report for {ticker_for_report}.")
    except Exception as e:
        logger.error(f"Error during Full Report Agent test: {e}", exc_info=True)
    logger.info("Full Report Agent test finished.")
