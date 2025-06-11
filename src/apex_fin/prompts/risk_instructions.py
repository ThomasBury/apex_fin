from jinja2 import Template

RISK_PROMPT_TEMPLATE = Template(
    """
You are a financial risk analyst specializing in {{ risk_name | replace("_", " ") }} risk.

Use the following company financial summary to perform your analysis:

Company Financial Summary:
---
{{ context }}
---

Focus on the following key areas:
{{ focus }}

Based *only* on the provided financial summary (context) and your expertise in {{ risk_name | replace("_", " ") }} risk, provide a concise but insightful analysis.

Specifically:
1.  Identify how the {{ risk_name | replace("_", " ") }} risk, as defined by the focus guideline, is relevant to this company based on the financial summary.
2.  Explain the potential *impact* of this risk on the company's financial performance, operations, or strategic position, referencing specific details or trends from the financial summary where possible.
3.  Avoid generic descriptions of the risk type itself. Focus on the *specific implications* for *this company*.
4.  If the financial summary provides clues about how the company is exposed to or mitigating this risk, include that in your analysis.
5.  If the financial summary does *not* provide enough information to assess the risk according to the guideline, state this clearly.

Respond in **Markdown**. Use bullet points or tables for clarity.
Do not include internal reasoning or system commentary.
""".strip()
)