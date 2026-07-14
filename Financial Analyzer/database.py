"""
database.py
Handles SQLite storage for extracted KPIs and generated reports.
Keeps a simple schema: one table for company reports, one for KPI values.
"""

import sqlite3
from datetime import datetime

DB_PATH = "financial_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            file_name TEXT,
            year TEXT,
            summary TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kpis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            kpi_name TEXT,
            kpi_value REAL,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    """)

    conn.commit()
    conn.close()


def save_report(company_name, file_name, year, summary, kpis: dict):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO reports (company_name, file_name, year, summary, created_at) VALUES (?, ?, ?, ?, ?)",
        (company_name, file_name, year, summary, datetime.now().isoformat()),
    )
    report_id = cur.lastrowid

    for name, value in kpis.items():
        cur.execute(
            "INSERT INTO kpis (report_id, kpi_name, kpi_value) VALUES (?, ?, ?)",
            (report_id, name, value),
        )

    conn.commit()
    conn.close()
    return report_id


def get_all_reports():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, company_name, file_name, year, created_at FROM reports ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_kpis_for_report(report_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT kpi_name, kpi_value FROM kpis WHERE report_id = ?", (report_id,))
    rows = cur.fetchall()
    conn.close()
    return {name: value for name, value in rows}


def get_report_summary(report_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT summary FROM reports WHERE id = ?", (report_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
