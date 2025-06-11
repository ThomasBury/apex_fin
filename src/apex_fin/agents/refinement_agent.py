"""
Refinement Agent that runs a generation-evaluation loop to improve output quality.
"""

import logging
from typing import Callable
from agno.agent import RunResponse, Agent
from apex_fin.agents.analysis_agent import build_analysis_agent
from apex_fin.agents.evaluation_agent import build_evaluation_agent, EvaluationFeedback

logger = logging.getLogger(__name__)


def run_agent(agent: Agent, prompt: str) -> str:
    """
    Execute a given agent with a prompt and return its stringified content.

    This is a utility function to encapsulate the common pattern of running an
    agent and extracting the textual content from its response.

    Parameters
    ----------
    agent : Agent
        An agent object that conforms to the Agno agent interface,
        specifically, it must have a `.run()` method that accepts a prompt
        and returns a `RunResponse` object.
    prompt : str
        Prompt to send to the agent.

    Returns
    -------
    str
        The content of the agent's response, converted to a string and stripped
        of leading/trailing whitespace.
    """
    response: RunResponse = agent.run(prompt)
    return str(response.content).strip()


def generate_refined_section(
    ticker: str,
    generator_fn: Callable[[str], str] = None,
    section_name: str = "company analysis",
    max_retries: int = 2,
) -> str:
    """
    Generate a report section through an iterative refinement loop.

    This function attempts to produce a high-quality section of a report
    by first generating an initial draft using a specified `generator_fn`
    (or a default analysis agent). It then uses an evaluation agent to
    assess the draft. If the evaluation indicates a need for improvement,
    the process can be repeated up to `max_retries` times.
    The intent is to improve the output quality through a
    generation-evaluation cycle.

    Parameters
    ----------
    ticker : str
        The stock ticker symbol (e.g., 'AAPL') for which the section
        is being generated. This is typically passed to the `generator_fn`.
    generator_fn : Callable[[str], str], optional
        A function that takes a ticker string as input and returns a string
        representing the generated report section. If None, a default
        markdown analysis agent (`build_analysis_agent()`)
        will be used. Defaults to None.
    section_name : str, optional
        A descriptive name for the section being generated (e.g.,
        "company analysis", "competitor overview"). This is used in
        console output during the refinement process. Defaults to "company analysis".
    max_retries : int, optional
        The maximum number of generation and evaluation attempts.
        Defaults to 2.

    Returns
    -------
    str
        The content of the generated section. This will be the first version
        that passes evaluation, or the latest version if `max_retries`
        is reached without passing.
    """
    # Default to markdown version of the analysis agent
    analysis_agent = build_analysis_agent()
    evaluation_agent = build_evaluation_agent()

    generator = generator_fn or (lambda ticker: run_agent(analysis_agent, ticker))

    latest_draft = ""
    for attempt in range(1, max_retries + 1):
        logger.info(
            f"Attempt {attempt}/{max_retries} – Generating {section_name} for {ticker}..."
        )
        try:
            latest_draft = generator(ticker)
            if not latest_draft:  # Ensure generator actually produced something
                logger.warning(
                    f"Generator function returned empty content for {ticker} on attempt {attempt}."
                )
                # Decide if to retry or fail, for now, we'll let it go to evaluation
                # or could 'continue' to retry generation if that's desired.
        except Exception as e:
            logger.error(
                f"Error during content generation for {ticker} on attempt {attempt}: {e}",
                exc_info=True,
            )
            if attempt == max_retries:
                logger.error(
                    "Max retries reached after generation error. Returning last known draft or empty."
                )
                return latest_draft  # Or raise the error
            continue  # Try next attempt

        evaluation_prompt = f"""
Evaluate the following {section_name} for quality and completeness.

### Content:
{latest_draft}
"""
        try:
            eval_response = evaluation_agent.run(evaluation_prompt)
            feedback: EvaluationFeedback = eval_response.content

            if not feedback.needs_improvement:
                logger.info(
                    f"Passed evaluation for {ticker} on attempt {attempt}. Score: {feedback.score}/5"
                )
                return latest_draft

            logger.info(
                f"Evaluation for {ticker} (attempt {attempt}) needs improvement. Score: {feedback.score}/5. Summary: {feedback.summary}"
            )
            logger.info(f"Missing elements: {feedback.missing_elements}")
        except Exception as e:
            logger.error(
                f"Error during evaluation for {ticker} on attempt {attempt}: {e}",
                exc_info=True,
            )
            # Fall through to next attempt or max_retries

    logger.warning(
        f"Max retries ({max_retries}) reached for {ticker}. Returning latest version of {section_name}."
    )
    return latest_draft


if __name__ == "__main__":
    from apex_fin.config import settings

    # The module already has `logger = logging.getLogger(__name__)`.
    # Ensure basicConfig is called for standalone execution.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    logger.info("Testing Refinement Agent (via generate_refined_section)...")
    try:
        if not settings.GEMINI_API_KEY:
            logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        ticker_for_refinement = "GOOGL"  # Example ticker
        logger.info(f"Generating refined section for: {ticker_for_refinement}")

        refined_output = generate_refined_section(
            ticker=ticker_for_refinement,
            section_name="company financial overview",
            max_retries=1,  # Keep retries low for a quick test
        )

        if refined_output:
            logger.info(
                f"Refined section for {ticker_for_refinement}:\n{refined_output}"
            )
        else:
            logger.error(
                f"Failed to generate refined section for {ticker_for_refinement}."
            )
    except Exception as e:
        logger.error(f"Error during Refinement Agent test: {e}", exc_info=True)
    logger.info("Refinement Agent test finished.")
