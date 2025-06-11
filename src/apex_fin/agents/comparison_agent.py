"""
Comparison Agent that takes a primary stock and compares it against
its main competitors across valuation and financial health metrics.
"""
import json
from typing import Optional, List, Union, Dict
from agno.agent import Agent, RunResponse
from agno.tools.thinking import ThinkingTools
from apex_fin.agents.analysis_agent import build_auto_analysis_agent
from apex_fin.agents.base import create_agent
from apex_fin.agents.competitor_agent import get_competitors
from apex_fin.prompts.comparison_instructions import COMPARISON_PROMPT
from apex_fin.config import settings
from apex_fin.utils.prompt_loader import load_prompt
from apex_fin.utils.yf_fetcher import YFinanceFinancialAnalyzer
from apex_fin.agents.analysis_agent import AnalysisResponse

import logging

logger = logging.getLogger(__name__)

def build_comparison_agent() -> Agent:
    """
    Constructs the comparison agent.

    Returns
    -------
    Agent
        Configured comparison agent.
    """
    instructions = [load_prompt(settings.prompt_paths.comparison, COMPARISON_PROMPT)]
    return create_agent(
        tools=[ThinkingTools()],
        show_tool_calls=False,
        instructions=instructions,
        markdown=True,
    )


def _fetch_and_analyze_ticker_for_summary(
    ticker_to_analyze: str,
    analysis_agent_instance: Agent,
    logger_instance: logging.Logger
) -> Optional[str]:
    """Fetches data, analyzes it, and returns a markdown summary.

    This function orchestrates the process of fetching financial data for a
    given ticker, running an analysis agent on this data, and extracting
    the markdown summary from the agent's response. It handles potential
    errors during data fetching and analysis.

    Parameters
    ----------
    ticker_to_analyze : str
        The stock ticker symbol to fetch and analyze.
    analysis_agent_instance : Agent
        An instance of the analysis agent to perform the financial analysis.
    logger_instance : logging.Logger
        The logger instance for recording progress and errors.

    Returns
    -------
    Optional[str]
        The markdown summary string if successful, otherwise None.
    """
    logger_instance.info(f"Fetching and analyzing data for: {ticker_to_analyze}")

    input_json_for_agent: str
    try: 
        analyzer = YFinanceFinancialAnalyzer(ticker_to_analyze)
        data_dict = analyzer.get_financial_snapshot_dict()
        input_json_for_agent = json.dumps(data_dict)
        logger_instance.info(f"Successfully pre-fetched data for {ticker_to_analyze}.")
    except Exception as e:
        logger_instance.error(f"Failed to pre-fetch data for {ticker_to_analyze}: {str(e)}", exc_info=True)
        error_payload = {
            "error": f"Data pre-fetch failed for '{ticker_to_analyze}': {str(e)}",
            "ticker_symbol": ticker_to_analyze
        }
        input_json_for_agent = json.dumps(error_payload)

    try: 
        logger_instance.info(f"Running analysis agent for '{ticker_to_analyze}' with input: {input_json_for_agent[:200]}...")
        result: RunResponse = analysis_agent_instance.run(input_json_for_agent)

        if hasattr(result, "content") and result.content:
            if isinstance(result.content, AnalysisResponse):
                logger_instance.info(f"Successfully retrieved AnalysisResponse for {ticker_to_analyze}.")
                return result.content.markdown_summary.strip()
            # This else block might be hit if the response_model isn't strictly enforced or if there's an unexpected agent output
            logger_instance.warning(
                f"Analysis for {ticker_to_analyze} did not return an AnalysisResponse object. "
                f"Content type: {type(result.content)}. Using raw content string if available."
            )
            return str(result.content).strip() if result.content is not None else None
        else:
            logger_instance.error(f"Analysis for {ticker_to_analyze} returned None or empty content.")
            return None
    except Exception as e:
        logger_instance.error(f"Exception during analysis agent run for {ticker_to_analyze}: {e}", exc_info=True)
        return None

def _parse_ticker_input(
    ticker_or_list_input: Union[str, List[str]], logger_instance: logging.Logger
) -> tuple[Optional[str], List[str]]:
    """Parses ticker input into a primary ticker and a list of competitors.

    The input can be a single ticker string (competitors will be fetched)
    or a list of tickers (first is primary, rest are competitors).

    Parameters
    ----------
    ticker_or_list_input : Union[str, List[str]]
        The input ticker string or list of ticker strings.
    logger_instance : logging.Logger
        The logger instance for recording parsing activity.

    Returns
    -------
    tuple[Optional[str], List[str]]
        A tuple containing the uppercase primary ticker (or None if invalid)
        and a list of uppercase competitor tickers.
    """
    if isinstance(ticker_or_list_input, str):
        primary_ticker_upper = ticker_or_list_input.upper()
        logger_instance.info(f"Primary ticker (string input): {primary_ticker_upper}. Fetching competitors.")
        competitor_list = get_competitors(primary_ticker_upper)
        return primary_ticker_upper, competitor_list
    elif isinstance(ticker_or_list_input, list):
        if not ticker_or_list_input:
            logger_instance.error("Received an empty list of tickers for comparison.")
            return None, []
        
        primary_ticker_upper = ticker_or_list_input[0].upper()
        if len(ticker_or_list_input) > 1:
            competitor_list = [t.upper() for t in ticker_or_list_input[1:]]
            logger_instance.info(f"Primary ticker (list input): {primary_ticker_upper}. Using provided competitors: {competitor_list}")
        else:
            logger_instance.info(f"Primary ticker (single item list input): {primary_ticker_upper}. Fetching competitors.")
            competitor_list = get_competitors(primary_ticker_upper)
        return primary_ticker_upper, competitor_list
    else:
        logger_instance.error(f"Invalid type for ticker_or_list_input: {type(ticker_or_list_input)}. Expected str or List[str].")
        return None, []


def compare_company(
    ticker_or_list_input: Union[str, List[str]],
    primary_company_analysis: Optional[AnalysisResponse] = None,
) -> str:
    """
    Compares a company to its top competitors.

    Parameters
    ----------
    ticker_or_list_input : Union[str, List[str]]
        The main stock ticker to analyze (e.g., "AAPL") or a list of tickers
        where the first is primary and the rest are competitors (e.g., ["AAPL", "MSFT", "GOOG"]).
        If a single ticker string is provided, or a list with only one ticker,
        competitors will be fetched automatically.
    primary_company_analysis : Optional[AnalysisResponse], optional
        Pre-computed AnalysisResponse object for the primary company.
        If provided, this avoids re-analyzing the primary company.
        Defaults to None.

    Returns
    -------
    str
        Markdown comparison report, or an error message string if input is invalid.
    """
    primary_ticker_upper, competitor_list = _parse_ticker_input(ticker_or_list_input, logger)

    if not primary_ticker_upper:
        # _parse_ticker_input already logged the specific error
        if not isinstance(ticker_or_list_input, (str, list)) or \
           (isinstance(ticker_or_list_input, list) and not ticker_or_list_input):
            return "Error: An empty or invalid list of tickers was provided for comparison."
        return "Error: Invalid input type for comparison. Provide a ticker string or a list of tickers."

    logger.info(f"Starting comparison for primary ticker: {primary_ticker_upper}")
    if competitor_list:
        logger.info(f"Competitors to analyze for {primary_ticker_upper}: {competitor_list}")
    else:
        logger.warning(f"No competitors found or provided for {primary_ticker_upper}. Comparison will be limited.")

    analysis_agent_instance = build_auto_analysis_agent()
    summaries_map: Dict[str, Optional[str]] = {} # Value can be None if analysis fails

    if primary_company_analysis:
        if isinstance(primary_company_analysis, AnalysisResponse):
            summaries_map[primary_ticker_upper] = primary_company_analysis.markdown_summary.strip()
            logger.info(f"Using pre-computed AnalysisResponse.markdown_summary for primary ticker {primary_ticker_upper}.")
        else:
            # This case handles if a string was passed, possibly from older calling code.
            summaries_map[primary_ticker_upper] = str(primary_company_analysis).strip()
            logger.warning(
                f"Received primary_company_analysis as type {type(primary_company_analysis)} for {primary_ticker_upper}, "
                f"but expected AnalysisResponse. Assuming it's a pre-rendered markdown summary."
            )
    
    # Analyze primary company if its analysis wasn't provided in summaries_map
    if primary_ticker_upper not in summaries_map:
        summaries_map[primary_ticker_upper] = _fetch_and_analyze_ticker_for_summary(
            primary_ticker_upper, analysis_agent_instance, logger
        )
        if summaries_map[primary_ticker_upper]:
            logger.info(f"Markdown summary for {primary_ticker_upper}:\n{summaries_map[primary_ticker_upper][:500]}...") # type: ignore

    # Analyze competitors
    for comp_ticker_str in competitor_list:
        comp_ticker_upper = comp_ticker_str.upper()
        if comp_ticker_upper not in summaries_map: # Avoid re-analyzing
            summaries_map[comp_ticker_upper] = _fetch_and_analyze_ticker_for_summary(
                comp_ticker_upper, analysis_agent_instance, logger
            )
            if summaries_map[comp_ticker_upper]:
                logger.info(f"Markdown summary for {comp_ticker_upper}:\n{summaries_map[comp_ticker_upper][:500]}...") # type: ignore

    # Assemble summaries in order: primary first, then competitors
    # Only include summaries that were successfully generated and stored in summaries_map
    ordered_summaries: List[str] = []
    primary_summary = summaries_map.get(primary_ticker_upper)
    if primary_summary:
        ordered_summaries.append(primary_summary)

    for comp_ticker_str in competitor_list:
        comp_ticker_upper = comp_ticker_str.upper()
        competitor_summary = summaries_map.get(comp_ticker_upper)
        if competitor_summary and comp_ticker_upper != primary_ticker_upper: # Ensure it exists and not a duplicate of primary
            ordered_summaries.append(competitor_summary)
    
    if not ordered_summaries:
        logger.error(f"No valid analysis summaries could be generated for {primary_ticker_upper} or its competitors.")
        return f"Error: Could not generate analysis for {primary_ticker_upper} or its competitors to perform a comparison."

    comparison_agent = build_comparison_agent()
    # Ensure there's at least one summary to compare.
    # The comparison prompt expects at least one, ideally more.
    if len(ordered_summaries) == 1 and primary_summary:
        comparison_prompt_text = (
            f"Provide an analysis of the following company based on its summary. "
            f"No direct competitors were available or analyzed for comparison:\n\n{ordered_summaries[0]}"
        )
    else:
        comparison_prompt_text = "Compare these companies:\n\n" + "\n\n".join(ordered_summaries)

    logger.debug(f"Comparison prompt being sent to LLM:\n{comparison_prompt_text}")
    final_result: RunResponse = comparison_agent.run(comparison_prompt_text)

    return str(final_result.content).strip() if final_result.content else "Comparison agent returned no content."


if __name__ == "__main__":
    # Logging setup is done within the if block
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    main_logger = logging.getLogger(__name__)

    main_logger.info("Testing Comparison Agent (via compare_company function)...")
    try:
        if not settings.GEMINI_API_KEY:
            main_logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        test_cases = [
            {"name": "Single Ticker (e.g., TSLA)", "input": "TSLA", "expected_error": False},
            # {"name": "List of Tickers (Primary + Competitors)", "input": ["MSFT", "AAPL", "GOOG"], "expected_error": False},
            # {"name": "List with Single Ticker (should fetch competitors)", "input": ["NVDA"], "expected_error": False},
            # {"name": "Ticker that might have no direct competitors found by agent", "input": "BRK-A", "expected_error": False}, # Comparison will be limited
            # {"name": "Empty List (should error gracefully)", "input": [], "expected_error": True},
            # {"name": "Invalid Type (should error gracefully)", "input": 123, "expected_error": True},
            # {"name": "Invalid Ticker (data fetch should fail, leading to error summary)", "input": "NONEXISTENTTICKERXYZ123"},
        ]

        for test_case in test_cases:
            main_logger.info(f"--- Running Test Case: {test_case['name']} ---")
            input_val = test_case["input"]
            main_logger.info(f"Input to compare_company: {input_val}")
            
            try:
                # The type: ignore is because Pylance/MyPy might struggle with the Union type in a loop
                comparison_report = compare_company(input_val) # type: ignore 

                if comparison_report:
                    is_error_report = "Error:" in comparison_report or "Could not" in comparison_report
                    if is_error_report:
                         main_logger.error(
                            f"Comparison for '{input_val}' returned an error/warning message: {comparison_report}"
                        )
                    else:
                        main_logger.info(
                            f"Comparison report for '{input_val}':\n{comparison_report[:1000]}..."
                        )
                    if test_case.get("expected_error") and not is_error_report:
                        main_logger.warning(f"Test case '{test_case['name']}' expected an error but received a success-like report.")
                else:
                    main_logger.error(
                        f"Failed to get comparison report for '{input_val}' (empty response)."
                    )
            except Exception as e_inner: # Catch exceptions from within compare_company if they are not handled
                 main_logger.error(f"Exception during test case '{test_case['name']}' with input '{input_val}': {e_inner}", exc_info=True)
            main_logger.info(f"--- Finished Test Case: {test_case['name']} ---\n")

    except Exception as e:
        main_logger.error(f"Error during Comparison Agent test: {e}", exc_info=True)
    main_logger.info("Comparison Agent test finished.")
