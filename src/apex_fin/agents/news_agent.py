"""
Financial News Agent that fetches and explains relevant news impacting a company or fund.
"""

import logging
from typing import List

from agno.agent import Agent, RunResponse
from agno.tools.duckduckgo import DuckDuckGoTools
from apex_fin.agents.base import create_agent
from apex_fin.prompts.news_instructions import NEWS_PROMPT
from apex_fin.utils.prompt_loader import load_prompt
from apex_fin.utils.ticker_validation import validate_and_get_ticker # Import the validator
import yfinance as yf # Import yfinance to get company name
from apex_fin.config import settings



logger = logging.getLogger(__name__)

def build_financial_news_agent() -> Agent:
    """
    Constructs and configures a financial news agent.

    This agent uses DuckDuckGoTools to search for recent news related to a
    given stock ticker. It then processes this information to provide summaries
    and explanations of relevance for financial analysis, formatted in Markdown.

    Returns
    -------
    Agent
        An instance of the `agno.agent.Agent` class, configured with
        search tools and specific instructions for news gathering and reporting.
    """

    base_news_prompt = load_prompt(settings.prompt_paths.analysis, NEWS_PROMPT)

    strict_output_instruction = (
        "\n\nIMPORTANT: Your response MUST consist ONLY of the Markdown content. "
        "Do NOT include any introductory phrases, conversational remarks, or any text "
        "outside of the Markdown structure. Start directly with the first Markdown heading "
        "for the first news item, or the 'No significant recent news...' message if applicable."
    )


    instructions = [base_news_prompt + strict_output_instruction]

    return create_agent(
        tools=[DuckDuckGoTools()],
        instructions=instructions,
        markdown=True, # Expecting Markdown output
        show_tool_calls=True, # Best for debugging
        response_model=None, # Output is a Markdown string
    )


def _run_news_agent_and_get_content(
    agent: Agent,
    prompt: str,
    entity_for_log: str, # e.g., "Microsoft (MSFT)"
    logger_instance: logging.Logger
) -> str:
    """Runs the news agent and extracts its string content.

    This function executes the provided news agent with a specific prompt,
    then safely extracts and validates the string content from the agent's
    response. It handles cases where content might be missing or an
    exception occurs during the agent run.

    Parameters
    ----------
    agent : Agent
        The news agent instance to run.
    prompt : str
        The prompt to send to the news agent.
    entity_for_log : str
        A string identifying the entity (e.g., company name and ticker)
        for logging purposes.
    logger_instance : logging.Logger
        The logger instance for recording agent activity and outcomes.

    Returns
    -------
    str
        The string content from the agent's response, or an error/warning
        message if issues occur.
    """
    logger_instance.info(f"Running financial news agent for {entity_for_log} with prompt: '{prompt}'")

    try:
        response: RunResponse = agent.run(prompt)
        if hasattr(response, "content") and response.content is not None:
            # Ensure content is a string and strip any potential extra whitespace
            content_str = str(response.content).strip()
            if not content_str:
                logger_instance.warning(f"Financial news agent returned empty content for {entity_for_log}.")
                return f"No specific news content was generated for {entity_for_log}."
            return content_str
        else:
            logger_instance.error(
                f"Failed to get valid content from financial news agent for {entity_for_log}. Response: {response}"
            )
            return f"Error: Could not retrieve financial news for {entity_for_log}."
    except Exception as e:
        logger_instance.error(
            f"An exception occurred while running financial news agent for {entity_for_log}: {e}",
            exc_info=True,
        )
        return f"Error: An exception occurred while fetching news for {entity_for_log}."

def get_financial_news(ticker_or_company_name: str) -> str:
    """
    Fetches and explains relevant financial news for a given stock ticker.
    The input is first validated to find a corresponding ticker symbol.

    Parameters
    ----------
    ticker_or_company_name : str
        The stock ticker symbol (e.g., "AAPL") or company name (e.g., "Microsoft").

    Returns
    -------
    str
        A Markdown formatted string containing the relevant news,
        their summaries, and explanations of their financial relevance.
        Returns an error message if validation or fetching fails.
    """
    if not ticker_or_company_name or not isinstance(ticker_or_company_name, str):
        logger.error("Invalid input: A non-empty string for ticker or company name must be provided.")
        return "Error: A valid ticker string must be provided."

    logger.info(f"Attempting to validate input for news agent: '{ticker_or_company_name}'")
    validated_ticker = validate_and_get_ticker(ticker_or_company_name)[0]

    if not validated_ticker:
        logger.error(f"Could not validate ticker for input: '{ticker_or_company_name}'.")
        return f"Error: Could not find a valid stock ticker for '{ticker_or_company_name}'."

    # Try to get the company's long name for a more descriptive prompt
    company_display_name = validated_ticker # Default to ticker if name lookup fails
    try:
        ticker_info = yf.Ticker(validated_ticker).info
        company_display_name = ticker_info.get('longName', validated_ticker)
        logger.info(f"Using '{company_display_name}' (Ticker: {validated_ticker}) for news search.")
    except Exception as e:
        logger.warning(f"Could not fetch longName for {validated_ticker}, using ticker symbol. Error: {e}")

    logger.info(f"Building financial news agent for: {company_display_name} ({validated_ticker})")
    agent = build_financial_news_agent()

    # Construct the prompt for the agent
    prompt = f"Fetch and explain relevant financial news for {company_display_name} (Ticker: {validated_ticker}). Follow all previously provided instructions for content and formatting."

    # Run the agent and process the response using the helper function
    return _run_news_agent_and_get_content(agent, prompt, f"{company_display_name} ({validated_ticker})", logger)

if __name__ == "__main__":
    # Configure logging for standalone execution
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    main_logger = logging.getLogger(__name__) # Use the module-level logger

    main_logger.info("Testing Financial News Agent (via get_financial_news function)...")
    try:
        if not settings.GEMINI_API_KEY:
            main_logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        # ticker_to_query = "Apple Inc."  # Example: Apple Inc. by name
        # ticker_to_query = "NVDA" # Example: NVIDIA by ticker
        # ticker_to_query = "SPY" # Example: SPDR S&P 500 ETF Trust
        # ticker_to_query = "NONEXISTENTTICKERXYZ" # Example: Invalid ticker
        ticker_to_query = "Microsoft" # Example: Microsoft by name

        main_logger.info(f"Fetching financial news for ticker: {ticker_to_query}")
        news_report = get_financial_news(ticker_to_query)

        if news_report:
            main_logger.info(f"Financial News Report for {ticker_to_query}:\n{news_report}")
        else:
            main_logger.error(
                f"Failed to get a financial news report for {ticker_to_query} or it was empty."
            )

    except Exception as e:
        main_logger.error(f"Error during Financial News Agent test: {e}", exc_info=True)
    main_logger.info("Financial News Agent test finished.")
