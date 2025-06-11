"""
Pydantic v2 schema for validating stock report outputs.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class StockReport(BaseModel):
    """
    Structured financial report for a single company.

    Attributes
    ----------
    ticker : str
        The stock ticker symbol (e.g. AAPL).
    pe_ratio : float, optional
        Price-to-Earnings ratio.
    revenue_growth : float, optional
        Year-over-year revenue growth as a percentage.
    debt_to_equity : float, optional
        Debt-to-equity ratio.
    recommendation : Literal["Buy", "Hold", "Sell"]
        Analyst recommendation.
    summary : str
        Short narrative summarizing the financial health.
    """

    ticker: str = Field(..., description="Stock ticker")
    pe_ratio: Optional[float] = Field(None, description="Price-to-Earnings ratio")
    revenue_growth: Optional[float] = Field(None, description="YOY revenue growth")
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-equity ratio")
    recommendation: Literal["Buy", "Hold", "Sell"] = Field(
        ..., description="Analyst consensus"
    )
    summary: str = Field(..., description="Natural language summary of the company")
