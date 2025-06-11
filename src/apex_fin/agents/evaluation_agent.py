from agno.agent import Agent
from agno.tools.thinking import ThinkingTools
from pydantic import BaseModel, Field
from apex_fin.prompts.evaluation_instructions import EVALUATION_PROMPT
from apex_fin.agents.base import create_agent
from apex_fin.config import settings
from apex_fin.utils.prompt_loader import load_prompt


class EvaluationFeedback(BaseModel):
    """
    Represents structured feedback from an evaluation agent.

    This model defines the expected output format when an agent evaluates
    a piece of content, such as a financial report section. It includes
    a numerical score, a textual summary, a boolean indicating if
    improvement is needed, and a list of any identified missing elements.

    Attributes
    ----------
    score : int
        A numerical score representing the quality of the evaluated content,
        constrained between 1 and 5 (inclusive).
    summary : str
        A textual summary of the evaluation, highlighting key findings
        or overall assessment.
    needs_improvement : bool
        A boolean flag indicating whether the evaluated content requires
        further improvement or revision. True if improvements are needed,
        False otherwise.
    missing_elements : list[str]
        A list of strings, where each string describes an element or piece
        of information that was expected but found to be missing or
        inadequate in the evaluated content.
    """

    score: int = Field(..., ge=1, le=5)
    summary: str
    needs_improvement: bool
    missing_elements: list[str]


def build_evaluation_agent() -> Agent:
    """
    Construct and configure an agent specialized in evaluating financial reports.

    This agent is designed to assess the quality, completeness, and accuracy
    of financial reports or report sections. It utilizes `ThinkingTools` to
    perform a structured reasoning process before providing feedback.
    The agent is instructed to follow specific evaluation prompts (defined in
    `EVALUATION_PROMPT`) and returns its findings as an `EvaluationFeedback` object.

    Returns
    -------
    Agent
        An instance of `agno.agent.Agent` configured with `ThinkingTools`,
        specific evaluation instructions, and set to output an
        `EvaluationFeedback` model.
    """
    return create_agent(
        tools=[ThinkingTools()],
        description="Evaluates investment reports using structured rubric and scratchpad reasoning.",
        instructions=[load_prompt(settings.prompt_paths.evaluation, EVALUATION_PROMPT)],
        response_model=EvaluationFeedback,
        markdown=False,
        show_tool_calls=True,
    )


if __name__ == "__main__":
    import logging

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    main_logger = logging.getLogger(__name__)

    main_logger.info("Testing Evaluation Agent...")
    try:
        if not settings.GEMINI_API_KEY:
            main_logger.warning(
                "GEMINI_API_KEY is not set in settings. Agent calls requiring LLM will likely fail."
            )

        evaluation_agent = build_evaluation_agent()
        sample_content_to_evaluate = """
        ## Company Analysis for XYZ
        XYZ is a company. It has revenues.
        The stock price has seen some changes.
        Financials:
        - Revenue: $2B
        - Profit: $50M
        """
        evaluation_prompt = f"""
        Evaluate the following company analysis for quality, completeness, and clarity.
        Consider if it covers key financial metrics, risks, competitive positioning, and future outlook.

        ### Content:
        {sample_content_to_evaluate}
        """
        main_logger.info("Running evaluation...")
        result = evaluation_agent.run(evaluation_prompt)

        if hasattr(result, "content") and isinstance(
            result.content, EvaluationFeedback
        ):
            feedback: EvaluationFeedback = result.content
            main_logger.info("Evaluation Feedback:")
            main_logger.info(f"  Score: {feedback.score}/5")
            main_logger.info(f"  Summary: {feedback.summary}")
            main_logger.info(f"  Needs Improvement: {feedback.needs_improvement}")
            main_logger.info(f"  Missing Elements: {feedback.missing_elements}")
        else:
            main_logger.error(
                f"Failed to get valid EvaluationFeedback. Result: {result}"
            )
    except Exception as e:
        main_logger.error(f"Error during Evaluation Agent test: {e}", exc_info=True)
    main_logger.info("Evaluation Agent test finished.")
