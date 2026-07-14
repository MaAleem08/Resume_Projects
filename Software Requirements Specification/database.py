import sqlite3
from datetime import datetime

DB_PATH = "requirements.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # without conn.row_factory = sqlite3.Row
    # print(user[0]) ; Output: Alice (You have to remember name is index 0)
    # but with conn.row_factory = sqlite3.Row
    # print(user["name"])  ; Output: Alice (Much easier to read and write!)
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS requirements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            text TEXT NOT NULL,
            req_type TEXT,
            issues TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    """)

    conn.commit()
    conn.close()


def create_project(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, created_at) VALUES (?, ?)",
        (name, datetime.now().isoformat())
    )
    conn.commit()
    project_id = cur.lastrowid
    conn.close()
    return project_id


def save_requirements(project_id, requirements):
    conn = get_connection()
    cur = conn.cursor()
    for r in requirements:
        cur.execute(
            "INSERT INTO requirements (project_id, text, req_type, issues, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, r["text"], r.get("req_type", ""), r.get("issues", ""), datetime.now().isoformat())
        )
    conn.commit()
    conn.close()


def save_document(project_id, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (project_id, content, created_at) VALUES (?, ?, ?)",
        (project_id, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_all_projects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project_requirements(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM requirements WHERE project_id = ?", (project_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project_documents(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE project_id = ? ORDER BY id DESC", (project_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
