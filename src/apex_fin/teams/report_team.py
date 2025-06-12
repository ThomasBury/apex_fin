import logging
from agno.team.team import Team
from agno.tools.thinking import ThinkingTools
from agno.models.litellm import LiteLLM 

from apex_fin.agents.analysis_agent import build_auto_analysis_agent
from apex_fin.agents.comparison_agent import build_comparison_agent
from apex_fin.agents.news_agent import build_financial_news_agent
from apex_fin.agents.thinking_agent import build_thinking_agent
from apex_fin.agents.evaluation_agent import build_evaluation_agent
from apex_fin.prompts.team_instructions import TEAM_PROMPT
from apex_fin.config import settings
from apex_fin.utils.prompt_loader import load_prompt


logger = logging.getLogger(__name__)

def build_report_team(ticker: str):
    """
    Builds a multi-agent team that coordinates full report generation.

    Parameters
    ----------
    ticker : str
        The stock ticker for which the report is to be generated.
    Returns
    -------
    Team
        Configured Agno Team with orchestrated agents.
    """
    news_agent = build_financial_news_agent()
    news_agent.name = "News Agent"
    news_agent.role = "Fetches, summarizes, and explains recent significant news."
    news_agent.description = (
        "Provides a Markdown section on recent news and developments impacting the company."
    )

    # analysis_agent = build_analysis_agent()
    # analysis_agent.name = "Analysis Agent"
    # analysis_agent.role = "Performs stock price and fundamentals analysis."
    # analysis_agent.description = (
    #     "Generates financial health overview for a given company."
    # )

    comparison_agent = build_comparison_agent()
    comparison_agent.name = "Comparison Agent"
    comparison_agent.role = "Benchmarks company against competitors."
    comparison_agent.description = (
        "Compares P/E ratio, debt, and other financial metrics with similar companies."
    )

    thinking_agent = build_thinking_agent(ticker)
    thinking_agent.name = "Thinking Agent"
    thinking_agent.role = (
        "Performs risk (geopolitical, economic, sector, financial, etc.) assessment."
    )
    thinking_agent.description = (
        "Provides broader context such as supply chain risks and global trends."
    )

    evaluation_agent = build_evaluation_agent()
    evaluation_agent.name = "Evaluation Agent"
    evaluation_agent.role = "Evaluates report quality."
    evaluation_agent.description = (
        "Scores the report using a rubric and highlights weaknesses."
    )
    
    analysis_agent = build_auto_analysis_agent()
    analysis_agent.name = "Financial Analysis Agent"
    analysis_agent.role = "Analyse financial figures."
    analysis_agent.description = (
        "Write a comprehensive financial analysis of the company based on the provided ticker."
    )
    
    # Configure the model for the Team Leader (coordinator)
    team_leader_model = LiteLLM(
        id=settings.LLM_MODEL,
        api_key=settings.GEMINI_API_KEY,
        name="GeminiTeamLeader", 
        # api_base=settings.BASE_URL, # Uncomment if you use a custom base URL
    )

    team = Team(
        name="FullReportTeam",
        model=team_leader_model,
        members=[
            comparison_agent,
            thinking_agent,
            evaluation_agent,
            news_agent,
            analysis_agent,
        ],
        tools=[
            ThinkingTools(),
        ],
        mode="coordinate",
        instructions=[
            load_prompt(settings.prompt_paths.team, TEAM_PROMPT),
        ],
        # Optional: Add this back later if you're retrying evaluation loops
        # success_criteria="The Evaluation Agent assigns a score of 4 or more to the report.",
    )
    return team

def generate_report_with_team(ticker: str) -> str:
    """
    Generates a full financial report by leveraging the Report Team.
    """
    logger.info(f"Building report team for ticker: {ticker}")
    report_team = build_report_team(ticker) # ticker is passed to team builder

    # The prompt for the Project Manager of the team.
    # This should be a high-level instruction that the PM can understand
    # based on its own TEAM_PROMPT.
    pm_instruction = f"Generate a comprehensive investment report for {ticker}."

    logger.info(f"Instructing Report Team to generate report for {ticker}.")
    # The team's .run() method executes the coordination logic.
    # The TEAM_PROMPT should guide the PM to return only the final Markdown.
    result = report_team.run(pm_instruction)

    if hasattr(result, "content") and result.content and isinstance(result.content, str):
        final_report = result.content.strip()
        if not final_report:
            logger.error(f"Report team returned empty content for {ticker}.")
            raise ValueError(f"Report team generated an empty report for {ticker}.")
        logger.info(f"Successfully generated report for {ticker} using the team.")
        return final_report
    else:
        logger.error(f"Report team did not return the expected string content for {ticker}. Result: {result}")
        raise ValueError(f"Failed to get a valid report string from the team for {ticker}.")

if __name__ == "__main__":
    ticker = "MSFT"  # Example ticker
    report = generate_report_with_team(ticker)
    print(report) 