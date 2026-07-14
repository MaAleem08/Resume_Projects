"""
extractor.py
Extracts raw text and tables from financial PDFs (annual reports,
balance sheets, income statements) and computes core KPIs/ratios.
"""

import re
import pdfplumber


def _table_to_text(table) -> str:
    """Flattens a table (list of rows) into plain text lines, e.g.
    ['Total Revenue', '$52,400,000', '$47,900,000'] -> 'Total Revenue $52,400,000 $47,900,000'
    This lets the same regex patterns used on paragraph text also catch
    figures that only appear inside tables."""
    lines = []
    for row in table:
        cells = [str(cell) for cell in row if cell is not None]
        if cells:
            lines.append(" ".join(cells))
    return "\n".join(lines)


def extract_text_and_tables(pdf_path: str):
    """Returns (full_text, list_of_tables) from a PDF file.
    full_text includes both the paragraph text AND the table content
    (flattened to plain text), so figure extraction and vector indexing
    both see numbers that live only inside tables."""
    full_text = ""
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

            for table in page.extract_tables():
                tables.append(table)
                table_text = _table_to_text(table)
                if table_text:
                    full_text += table_text + "\n"

    return full_text, tables


def extract_financial_figures(text: str) -> dict:
    """
    Pulls common financial line items out of report text using pattern
    matching. This is intentionally simple - real filings are messy,
    so the LLM agents refine/validate these numbers afterward.
    """
    patterns = {
        "revenue": r"(?:total revenue|net revenue|revenue)\D{0,15}([\d,]+\.?\d*)",
        "net_income": r"net income\D{0,15}([\d,]+\.?\d*)",
        "total_assets": r"total assets\D{0,15}([\d,]+\.?\d*)",
        "total_liabilities": r"total liabilities\D{0,15}([\d,]+\.?\d*)",
        "operating_expenses": r"operating expenses\D{0,15}([\d,]+\.?\d*)",
        "current_assets": r"current assets\D{0,15}([\d,]+\.?\d*)",
        "current_liabilities": r"current liabilities\D{0,15}([\d,]+\.?\d*)",
    }

    figures = {}
    lower_text = text.lower()

    for key, pattern in patterns.items():
        match = re.search(pattern, lower_text)
        if match:
            value = match.group(1).replace(",", "")
            try:
                figures[key] = float(value)
            except ValueError:
                continue

    return figures


def compute_ratios(figures: dict) -> dict:
    """Derives standard KPIs from raw extracted figures. Skips ratios
    whose inputs weren't found rather than guessing."""
    ratios = {}

    revenue = figures.get("revenue")
    net_income = figures.get("net_income")
    total_assets = figures.get("total_assets")
    total_liabilities = figures.get("total_liabilities")
    current_assets = figures.get("current_assets")
    current_liabilities = figures.get("current_liabilities")

    if revenue and net_income:
        ratios["net_profit_margin_%"] = round((net_income / revenue) * 100, 2)

    if net_income and total_assets:
        ratios["return_on_assets_%"] = round((net_income / total_assets) * 100, 2)

    if total_liabilities and total_assets:
        ratios["debt_to_assets_%"] = round((total_liabilities / total_assets) * 100, 2)

    if current_assets and current_liabilities:
        ratios["current_ratio"] = round(current_assets / current_liabilities, 2)

    return {**figures, **ratios}