"""
Typer-powered CLI for the Financial Agent application.
Supports modular and team-based report generation workflows.
"""

import typer
import re
import functools
from typing import Optional, Any, Callable

# Agent and Team builders
from apex_fin.agents.analysis_agent import build_auto_analysis_agent, _fetch_financial_data_for_agent
from apex_fin.agents.comparison_agent import compare_company
from apex_fin.agents.full_report_agent import build_full_report
from apex_fin.agents.thinking_agent import build_thinking_agent
from apex_fin.teams.report_team import build_report_team

# Configuration
from apex_fin.config import load_user_config, env_settings, MergedSettings
import logging

app = typer.Typer(help="CLI to run AI-powered financial analysis reports.")

# Helper Functions and Decorators


def sanitize_ticker(ticker: str) -> str:
    """
    Sanitize a stock ticker string for safe use.

    Removes non-alphanumeric characters, converts to uppercase,
    and truncates to a maximum of 10 characters.

    Parameters
    ----------
    ticker : str
        The raw stock ticker string.

    Returns
    -------
    str
        The sanitized stock ticker string.
    """

    return re.sub(r"[^A-Z0-9]", "", ticker.upper())[:10]


# Global configuration override
@app.callback()
def main(
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Optional path to custom YAML configuration file."
    ),
):
    """
    Load optional YAML configuration at CLI startup.

    This callback function is executed before any command. It allows
    users to specify a custom configuration file path, which will
    override the default settings.

    Parameters
    ----------
    config_path : Optional[str], optional
        The path to a custom YAML configuration file.
        If None, default configuration is used.
        Defaults to None.
    """
    global settings
    user_config = load_user_config(config_path)
    settings = MergedSettings(env_settings, user_config)


def _get_content_from_result(result: Any) -> str:
    """
    Extracts string content from an agent's run result or a direct string.

    Handles None results and potential errors during string conversion.
    If the result is an object with a `content` attribute, that is used.
    Otherwise, the result is converted directly to a string.

    Parameters
    ----------
    result : Any
        The result from an agent's run method, or any other value.

    Returns
    -------
    str
        The extracted string content, or an error/placeholder string.
    """
    if result is None:
        # Optionally log a warning here if None is not an expected valid "empty" result
        # import logging
        # logging.warning("Agent returned None result.")
        return "[No content returned]"

    if hasattr(result, "content") and result.content is not None:
        try:
            return str(result.content).strip()
        except Exception as e:
            # import logging
            # logging.error(f"Error converting result.content to string: {e}", exc_info=True)
            return f"[Error extracting content from result.content of type {type(result.content).__name__}]"

    try:
        content = str(result).strip()
        # Heuristic: if the string representation is a generic object repr, it might not be useful.
        # This is a simple check; more robust checks might be needed depending on expected object types.
        if re.match(r"<.* object at 0x[0-9a-fA-F]+>", content) or content == "None":
            # import logging
            # logging.warning(f"Agent returned object with generic string representation: {content}")
            return f"[Received object of type {type(result).__name__}, no specific content extracted]"
        return content
    except Exception as e:
        # import logging
        # logging.error(f"Error converting agent result to string: {e}", exc_info=True)
        return f"[Error extracting content from result of type {type(result).__name__}]"


def handle_cli_errors(func: Callable) -> Callable:
    """
    Decorator to catch exceptions in CLI commands and exit.

    Wraps a CLI command function to provide standardized error handling.
    If an exception occurs during the command's execution, it prints
    an error message to stderr and exits the application with a status code of 1.

    Parameters
    ----------
    func : Callable[..., Any]
        The CLI command function to wrap.

    Returns
    -------
    Callable[..., Any]
        The wrapped function with error handling.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            typer.echo(f"[ERROR] Command failed: {e}", err=True)
            # For more detailed debugging, uncomment the next two lines:
            # import traceback
            # typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=1)

    return wrapper


# CLI Commands


@app.command()
@handle_cli_errors
def analyze(ticker: str) -> None:
    """
    Run a financial health analysis for a given company ticker.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol for the company to analyze.
        Example: "AAPL", "MSFT".
    """
    safe_ticker = sanitize_ticker(ticker)
    typer.echo(f"Fetching financial data for {safe_ticker}...")

    # Setup logger for _fetch_financial_data_for_agent
    cli_logger = logging.getLogger("apex_fin.cli.analyze")
    if not logging.getLogger().hasHandlers(): # Basic config if not already set up
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    input_json_str = _fetch_financial_data_for_agent(safe_ticker, cli_logger)

    # Crude check for error in fetched data; _fetch_financial_data_for_agent returns a JSON string
    if '"error":' in input_json_str and "Data pre-fetch failed" in input_json_str:
        typer.echo(f"Error: Could not fetch financial data for {safe_ticker}. Details: {input_json_str}")
        raise typer.Exit(code=1)

    typer.echo(f"Running analysis for {safe_ticker}...")
    agent = build_auto_analysis_agent()
    response = agent.run(input_json_str) # Pass the pre-fetched JSON data string
    typer.echo(_get_content_from_result(response))


@app.command()
@handle_cli_errors
def compare(ticker: str) -> None:
    """
    Compare a company to its top competitors.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol for the primary company to compare.
        Example: "GOOGL", "TSLA".
    """
    safe_ticker = sanitize_ticker(ticker)
    report = compare_company(safe_ticker)
    typer.echo(_get_content_from_result(report))


@app.command()
@handle_cli_errors
def think(ticker: str) -> None:
    """
    Perform contextual reasoning and policy checks for a stock.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol for which to perform contextual reasoning.
        Example: "NVDA", "VZ".
    """
    safe_ticker = sanitize_ticker(ticker)
    # Directly use the thinking_agent for the 'think' command
    agent = build_thinking_agent(safe_ticker)  # This agent is a Team
    # The prompt here is for the Team's LLM to orchestrate its members.
    # The internal instructions within build_thinking_agent guide the output structure.
    prompt_for_thinking_team = f"Generate a comprehensive risk assessment for {safe_ticker} based on its financial summary."
    response = agent.run(prompt_for_thinking_team)
    typer.echo(_get_content_from_result(response))


@app.command(name="fullreport")
@handle_cli_errors
def full_report(
    ticker: str,
    output: Optional[typer.FileTextWrite] = typer.Option(
        None,
        "--output",
        "-o",
        help="Optional path to write the report as a Markdown file.",
    ),
) -> None:
    """
    Run a complete financial report for a stock.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol for which to generate a full report.
        Example: "JPM", "XOM".
    """
    safe_ticker = sanitize_ticker(ticker)
    report = build_full_report(safe_ticker)
    typer.echo(_get_content_from_result(report))
    if output:
        output.write(report)
        typer.echo(f"Report written to: {output.name}")
    else:
        typer.echo(report)


################################################
# performance not as good than full report
################################################

# @app.command(name="teamreport")
# @handle_cli_errors
# def team_report(
#     ticker: str,
#     output: Optional[typer.FileTextWrite] = typer.Option(
#         None,
#         "--output",
#         "-o",
#         help="Optional path to write the report as a Markdown file.",
#     ),
# ) -> None:
#     """
#     Generate a full risk assessment report using Team orchestration.

#     This command utilizes a pre-defined team of agents to collaboratively
#     produce a comprehensive risk assessment report for the specified stock ticker.

#     Parameters
#     ----------
#     ticker : str
#         The stock ticker symbol for which to generate the team-based report.
#         Example: "AMZN", "DIS".
#     output : Optional[typer.FileTextWrite], optional
#         An optional file path to write the generated Markdown report.
#         If not provided, the report is printed to standard output.
#         Defaults to None.
#     """
#     safe_ticker = sanitize_ticker(ticker)
#     team = build_report_team(safe_ticker)

#     # The input to team.run() is the overall task for the team.
#     # The team's internal TEAM_PROMPT guides its orchestration.
#     team_input_prompt = f"Generate a full investment report for {safe_ticker}."
#     result = team.run(team_input_prompt)

#     report_markdown = _get_content_from_result(result)
#     # Ensure a top-level title if the team didn't provide one.
#     # Ideally, the team's prompt should ensure this.
#     if not report_markdown.startswith("#"):
#         report_markdown = (
#             f"# Full Investment Report: {safe_ticker}\n\n{report_markdown}"
#         )

#     if output:
#         output.write(report_markdown)
#         typer.echo(f"Report written to: {output.name}")
#     else:
#         typer.echo(report_markdown)

if __name__ == "__main__":
    app()
