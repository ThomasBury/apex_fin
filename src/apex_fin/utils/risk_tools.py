from typing import Any
from apex_fin.config import settings
from agno.tools.duckduckgo import DuckDuckGoTools  # Corrected import
from agno.tools.yfinance import YFinanceTools  # Corrected import
from agno.tools.thinking import ThinkingTools  # Corrected import

# Mapping of tool names to actual classes or factory callables
TOOL_REGISTRY: dict[str, Any] = {
    "DuckDuckGoTools": DuckDuckGoTools,
    "ThinkingTools": ThinkingTools,
    "YFinanceTools": lambda: YFinanceTools(company_info=True),
}


def get_tools_for_risk(risk_name: str) -> list[Any]:
    """
    Dynamically loads tools from YAML-configured list of tool names.

    Parameters
    ----------
    risk_name : str

    Returns
    -------
    list[Any]
        Instantiated tool objects
    """
    tool_names = settings.risk_tools.get(risk_name, [])
    tools = []

    for name in tool_names:
        factory = TOOL_REGISTRY.get(name)
        if not factory:
            raise ValueError(f"Unknown tool '{name}' for risk '{risk_name}' in config.")
        tools.append(factory())

    return tools
