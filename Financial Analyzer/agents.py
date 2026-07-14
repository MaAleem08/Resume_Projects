"""
agents.py
Defines the CrewAI agent team that turns extracted financial data into
a business-readable report:

  1. KPI Analyst      - validates/interprets the computed ratios
  2. Financial Analyst - identifies trends, risks, red flags
  3. Report Writer      - writes the final executive summary

Extraction itself stays in extractor.py (deterministic code is more
reliable than an LLM for pulling numbers out of text), so the crew
focuses on the reasoning and writing steps.
"""

from crewai import Agent, Task, Crew, Process, LLM

llm = LLM(model="ollama/llama3.2", base_url="http://localhost:11434")


kpi_analyst = Agent(
    role="KPI Analyst",
    goal="Interpret extracted financial figures and validate the computed ratios",
    backstory=(
        "A meticulous financial analyst who specializes in reading raw "
        "balance sheet and income statement data and explaining what each "
        "ratio actually means for the business."
    ),
    llm=llm,
    verbose=True,
)

financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Identify trends, strengths, and risks from the KPIs",
    backstory=(
        "A senior analyst with years of experience spotting red flags in "
        "company financials - declining margins, rising debt, liquidity "
        "issues - and framing them for a non-technical audience."
    ),
    llm=llm,
    verbose=True,
)

report_writer = Agent(
    role="Report Writer",
    goal="Write a clear, structured executive summary of the financial health of the company",
    backstory=(
        "A financial communications specialist who turns analyst notes "
        "into concise executive summaries that leadership can act on."
    ),
    llm=llm,
    verbose=True,
)


def run_financial_analysis(company_name: str, kpis: dict) -> str:
    """Kicks off the crew with the extracted KPIs and returns the final report text."""

    kpi_text = "\n".join(f"- {k}: {v}" for k, v in kpis.items())

    interpret_task = Task(
        description=(
            f"Company: {company_name}\n"
            f"Extracted financial figures and ratios:\n{kpi_text}\n\n"
            "Explain what each ratio indicates about the company's performance."
        ),
        expected_output="A short interpretation for each KPI, in plain language.",
        agent=kpi_analyst,
    )

    trend_task = Task(
        description=(
            "Using the KPI interpretations, identify the company's key strengths, "
            "weaknesses, and any risk indicators (e.g. low current ratio, high debt, "
            "shrinking margins)."
        ),
        expected_output="A bullet list of strengths, weaknesses, and risk flags.",
        agent=financial_analyst,
        context=[interpret_task],
    )

    summary_task = Task(
        description=(
            f"Write a concise executive summary (under 300 words) of {company_name}'s "
            "financial health for a leadership audience, based on the KPI interpretation "
            "and trend analysis."
            "write summary in simple english . Do not use complex words an also do not write it like a documentation level english."
            "You are simplifying and breaking down a financial document , so make it easily understandable."
        ),
        expected_output="A well-structured executive summary in plain business English.",
        agent=report_writer,
        context=[interpret_task, trend_task],
    )

    crew = Crew(
        agents=[kpi_analyst, financial_analyst, report_writer],
        tasks=[interpret_task, trend_task, summary_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
