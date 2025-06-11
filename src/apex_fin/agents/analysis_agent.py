"""
Analysis Agent that retrieves and summarizes the financial health of a given company.
"""
import json
from pydantic import BaseModel, Field
from typing import Dict, Any

from agno.agent import Agent
from agno.tools import tool
from agno.tools.thinking import ThinkingTools
from apex_fin.agents.base import create_agent
from apex_fin.prompts.analysis_instructions import AUTO_ANALYSIS_PROMPT
from apex_fin.config import settings
from apex_fin.utils.prompt_loader import load_prompt
from apex_fin.utils.yf_fetcher import YFinanceFinancialAnalyzer

import logging

logger = logging.getLogger(__name__)

# Define the response model for the agent's output
class AnalysisResponse(BaseModel):
    markdown_summary: str = Field(..., description="The Markdown formatted financial analysis summary.")
    # raw_data_json: Dict[str, Any] = Field(..., description="The raw financial data fetched, as a JSON object.")


# Define the custom tool to fetch financial data using YFinanceFinancialAnalyzer
class FinancialDataFetcherTool:
    @tool(description="Fetches comprehensive financial data for a given stock ticker. Input should be the stock ticker symbol. Returns a JSON string of the data.")
    def get_financial_data_json(self, ticker: str) -> str:
        """Fetches comprehensive financial data and returns it as a JSON string.

        Fetches comprehensive financial data using YFinanceFinancialAnalyzer
        and returns it as a JSON string.
        The input ticker is first validated and potentially corrected.

        Parameters
        ----------
        ticker : str
            The stock ticker symbol for which to fetch financial data.

        Returns
        -------
        str
            A JSON string containing the financial data, or an error message
            if data fetching fails.
        """
        try:
            analyzer = YFinanceFinancialAnalyzer(ticker)
            # Uses default num_news_stories and num_financial_periods from get_financial_snapshot_dict
            data_dict = analyzer.get_financial_snapshot_dict()
            return json.dumps(data_dict)
        except Exception as e:
            return json.dumps({"error": f"Failed to fetch data for {ticker}: {str(e)}"})


# def build_analysis_agent() -> Agent:
#     """
#     Construct and configure a financial analysis agent.

#     This agent uses YFinanceFinancialAnalyzer (via a custom tool) to fetch
#     comprehensive data for a stock ticker in a single call. It then uses an LLM
#     to generate a markdown summary of this data and returns both the summary
#     and the raw JSON data.

#     Returns
#     -------
#     Agent
#         An instance of the `agno.agent.Agent` class, configured with
#         financial tools and specific instructions based on the chosen mode.

#     """
#     tools = [ThinkingTools()]

#     # Load the base analy prompt
#     base_analysis_prompt = load_prompt(settings.prompt_paths.analysis, ANALYSIS_PROMPT)

#     # Add a strict instruction to ensure only Markdown is output, without conversational preambles
#     strict_output_instruction = (
#         "\n\nIMPORTANT: Do NOT include any introductory phrases, conversational remarks or system commentary. "
        
#     )
#     instructions = [base_analysis_prompt + strict_output_instruction]

#     return create_agent(
#         tools=tools,
#         instructions=instructions,
#         markdown=True,  # Output is a JSON object
#         # response_model=AnalysisResponse,  # Enforce the new response structure
#         show_tool_calls=True,
#     )


def _get_financial_data_for_report(ticker: str) -> str:
    """
    Fetches financial data for the given ticker and returns it as a JSON string.
    
    Parameters
    ----------
    ticker : str
        The stock ticker symbol for which to fetch financial data.
    
    Returns
    -------
    str
        A JSON string containing the financial data.
    """
    analyzer = YFinanceFinancialAnalyzer(ticker)
    return analyzer.get_financial_snapshot_dict()

def build_auto_analysis_agent() -> Agent:
    """
    Construct and configure a financial analysis agent.

    This agent uses YFinanceFinancialAnalyzer (via a custom tool) to fetch
    comprehensive data for a stock ticker in a single call. It then uses an LLM
    to generate a markdown summary of this data and returns both the summary
    and the raw JSON data.

    Returns
    -------
    Agent
        An instance of the `agno.agent.Agent` class, configured with
        financial tools and specific instructions based on the chosen mode.

    """
    tools = [ThinkingTools(), _get_financial_data_for_report]

    # Load the base analy prompt
    base_analysis_prompt = load_prompt(settings.prompt_paths.analysis, AUTO_ANALYSIS_PROMPT)

    # Add a strict instruction to ensure only Markdown is output, without conversational preambles
    strict_output_instruction = (
        "\n\nIMPORTANT: Do NOT include any introductory phrases, conversational remarks or system commentary. "
        
    )
    instructions = [base_analysis_prompt + strict_output_instruction]

    return create_agent(
        tools=tools,
        instructions=instructions,
        markdown=True,  # Output is a JSON object
        # response_model=AnalysisResponse,  # Enforce the new response structure
        show_tool_calls=True,
    )

def _setup_logging():
    """Configures basic logging if no handlers are already present.

    This function sets up a basic configuration for the root logger if it
    has no handlers. This is useful for scripts or standalone tests.
    """
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

def _check_api_key(logger_instance: logging.Logger) -> None:
    """Checks for the GEMINI_API_KEY and logs a warning if not set.

    Parameters
    ----------
    logger_instance : logging.Logger
        The logger instance to use for logging the warning.
    """
    if not settings.GEMINI_API_KEY:
        logger_instance.warning(
            "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
        )

def _fetch_financial_data_for_agent(ticker: str, logger_instance: logging.Logger) -> str:
    """Pre-fetches financial data or creates an error payload.

    This function attempts to retrieve a financial snapshot for the given stock
    ticker using `YFinanceFinancialAnalyzer`. If successful, it returns the data
    as a JSON string. If an error occurs during fetching, it constructs a
    JSON payload detailing the error.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol for which to fetch data.
    logger_instance : logging.Logger
        The logger instance to use for logging information and errors.

    Returns
    -------
    str
        A JSON string containing either the fetched financial data or an
        error payload.
    """
    logger_instance.info(f"Attempting to pre-fetch data for: {ticker}")
    try:
        analyzer = YFinanceFinancialAnalyzer(ticker)
        data_dict = analyzer.get_financial_snapshot_dict()
        logger_instance.info(f"Successfully pre-fetched data for {ticker}.")
        return json.dumps(data_dict)
    except Exception as e:
        logger_instance.error(f"Failed to pre-fetch data for {ticker}: {str(e)}", exc_info=True)
        error_payload = {
            "error": f"Data pre-fetch failed for '{ticker}': {str(e)}",
            "ticker_symbol": ticker  # Keep original ticker for context
        }
        return json.dumps(error_payload)

def _run_analysis_and_log_results(
    agent: Agent, 
    input_json_str: str, 
    ticker_for_log: str, 
    logger_instance: logging.Logger
) -> None:
    """Runs the analysis agent with the provided input and logs its results.

    Parameters
    ----------
    agent : Agent
        The analysis agent instance to run.
    input_json_str : str
        The JSON string input to be passed to the agent.
    ticker_for_log : str
        The ticker symbol, used for logging context.
    logger_instance : logging.Logger
        The logger instance for recording agent activity and results.
    """
    logger_instance.info(f"Running analysis agent for '{ticker_for_log}' with input: {input_json_str[:500]}...")
    result = agent.run(input_json_str)
    
    print(result.content)


if __name__ == "__main__":
    _setup_logging()
    main_logger = logging.getLogger(__name__)
    main_logger.info("Testing Analysis Agent...")

    TICKER_TO_ANALYZE = "VZ"  # Example ticker

    try:
        _check_api_key(main_logger)

        # analysis_agent = build_analysis_agent()
        
        # # The agent's instructions now expect the prompt to be the pre-fetched JSON data string.
        # input_json_for_agent = _fetch_financial_data_for_agent(TICKER_TO_ANALYZE, main_logger)
        # _run_analysis_and_log_results(analysis_agent, input_json_for_agent, TICKER_TO_ANALYZE, main_logger)
        
        analysis_agent = build_auto_analysis_agent()
        result = analysis_agent.run(TICKER_TO_ANALYZE)
        print(result.content)

    except Exception as e:
        main_logger.error(f"Error during Analysis Agent test: {e}", exc_info=True)
    finally:
        main_logger.info("Analysis Agent test finished.")
