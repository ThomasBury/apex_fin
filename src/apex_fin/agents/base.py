from typing import Any, List, Optional
from pydantic import BaseModel 
from typing import Optional, Any
from agno.agent import Agent
from agno.models.litellm import LiteLLM
from apex_fin.prompts.risk_instructions import RISK_PROMPT_TEMPLATE
from apex_fin.config import settings


def create_agent(
    name: Optional[str] = None, 
    tools: List[Any] | None = None,
    description: str = "",
    instructions: List[str] | None = None,
    markdown: bool = True,
    show_tool_calls: bool = True,
    response_model: type[BaseModel] | None = None,
) -> Agent:
    """
    Create and configure a standardized `agno.agent.Agent` instance.

    This factory function simplifies the creation of agents by providing
    a default LiteLLM model configuration (Gemini, using settings from
    the `config` module) and common agent parameters.

    Parameters
    ----------
    name : str, optional
        The name of the agent. Defaults to None, in which case the agent
        might be unnamed or receive a default name from the framework.
    tools : List[Any], optional
        A list of tools to be made available to the agent.
        Defaults to an empty list.
    description : str, optional
        A high-level description of the agent's purpose or capabilities.
        Defaults to an empty string.
    instructions : List[str], optional
        A list of specific instructions or guidelines for the agent's
        behavior and response generation. Defaults to an empty list.
    markdown : bool, optional
        If True, the agent is configured to prefer Markdown in its output.
        Defaults to True.
    show_tool_calls : bool, optional
        If True, tool invocation details will be included in the agent's
        logging or output, aiding in debugging and transparency.
        Defaults to True.
    response_model : type[BaseModel] | None, optional
        A Pydantic BaseModel class that defines the expected structure
        of the agent's response. If provided, the agent will attempt to
        format its output according to this schema. Defaults to None.

    Returns
    -------
    Agent
        An instance of `agno.agent.Agent` configured with the specified
        parameters and a default LiteLLM (Gemini) model.
    """
    model = LiteLLM(
        id=settings.LLM_MODEL,
        api_key=settings.GEMINI_API_KEY,
        name="Gemini",
        # api_base=settings.BASE_URL,
    )

    return Agent(
        name=name,
        model=model,
        tools=tools if tools is not None else [],
        description=description,
        instructions=instructions if instructions is not None else [],
        markdown=markdown,
        show_tool_calls=show_tool_calls,
        response_model=response_model,
    )


def build_base_risk_agent(
    risk_name: str,
    context: str,
    tools: Optional[list[Any]] = None,
    instructions: Optional[List[str]] = None,
) -> Agent:
    """
    Build a standardized risk assessment agent for the given risk type.

    Parameters
    ----------
    risk_name : str
        The risk type (e.g., "macroeconomic", "esg") to be assessed.
    context : str
        Markdown-formatted financial summary. Used if instructions are not provided,
        but providing pre-rendered instructions is preferred.
    tools : Optional[list[Any]]
        Optional list of tools to provide to the agent.
    instructions : Optional[List[str]]
        Pre-rendered instructions for the agent. If provided, these are used directly.

    Returns
    -------
    Agent
        An Agent instance configured for the specified risk.
    """
    final_instructions: List[str]
    if instructions:
        final_instructions = instructions
    else:
        # Fallback to generate instructions if not provided (though thinking_agent should provide them)
        guideline = settings.risk_guidelines.get(risk_name)
        if guideline is None or not guideline.strip():
            raise ValueError(
                f"Missing or empty guideline for risk '{risk_name}' in config.risk.guidelines and no pre-rendered instructions provided."
            )
        prompt_content = RISK_PROMPT_TEMPLATE.render(
            risk_name=risk_name, context=context, focus=guideline.strip()
        )
        final_instructions = [prompt_content]

    return create_agent(
        name=risk_name.replace("_", " ").title() + " Agent",
        description=f"{risk_name.title()} Risk Assessment",
        instructions=final_instructions,
        tools=tools or [],
        markdown=True,
    )
