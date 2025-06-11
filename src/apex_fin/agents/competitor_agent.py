"""
Competitor Agent that uses LLM + search tools to return 2–3 relevant competitors
for a given public company or ticker.
"""

from typing import List
import ast  # For safe literal evaluation
from agno.agent import Agent, RunResponse
from agno.tools.duckduckgo import DuckDuckGoTools
from apex_fin.agents.base import create_agent


def build_competitor_agent() -> Agent:
    """
    Constructs an agent to find top public competitors for a given company.

    Returns
    -------
    Agent
        Configured LLM agent with web search capabilities.
    """
    return create_agent(
        tools=[DuckDuckGoTools()],
        instructions=[
            "You are a financial analyst with access to a financial database and the internet.",
            "Given a stock ticker or company name, identify the top 2 direct public competitors.",
            "Only return a Python list of stock tickers or company names.",
            "Always look for the corresponding official stock tickers as referenced on Yahoo Finance.",
            "Format: list[str] such as ['AAPL', 'MSFT']. Do not explain or add commentary.",
        ],
        markdown=False,
        show_tool_calls=True,
    )


def get_competitors(query: str) -> List[str]:
    """
    Queries the competitor agent to return related companies.

    Parameters
    ----------
    query : str
        Stock ticker or company name.

    Returns
    -------
    List[str]
        List of competitor tickers or company names.
    """
    agent = build_competitor_agent()
    response: RunResponse = agent.run(query)

    try:
        # Use ast.literal_eval for safety instead of eval()
        evaluated_content = ast.literal_eval(response.content.strip())
        return evaluated_content if isinstance(evaluated_content, list) else []
    except (SyntaxError, ValueError, TypeError):
        return []


if __name__ == "__main__":
    import logging
    from apex_fin.config import settings

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    main_logger = logging.getLogger(__name__)

    main_logger.info("Testing Competitor Agent (via get_competitors function)...")
    try:
        if not settings.GEMINI_API_KEY:  # The agent uses LiteLLM (Gemini by default)
            main_logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        company_query = "NVIDIA"  # Example query
        main_logger.info(f"Getting competitors for: {company_query}")
        competitors_list = get_competitors(company_query)

        if competitors_list:
            main_logger.info(f"Competitors for {company_query}: {competitors_list}")
        else:
            main_logger.info(
                f"No competitors found or an error occurred for {company_query}."
            )
    except Exception as e:
        main_logger.error(f"Error during Competitor Agent test: {e}", exc_info=True)
    main_logger.info("Competitor Agent test finished.")
