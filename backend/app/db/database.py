import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sathi.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Subjects Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        group_name TEXT NOT NULL
    );
    """)

    # Chapters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chapters (
        id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        chapter_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'not_started', -- not_started, in_progress, completed
        notes TEXT DEFAULT '',
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    );
    """)

    # Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subject_id TEXT,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)

    # Streak & Activity Stats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_streak INTEGER NOT NULL DEFAULT 1,
        last_active_date TEXT,
        total_focus_minutes INTEGER NOT NULL DEFAULT 0
    );
    """)

    # Seed initial stats if empty
    cursor.execute("SELECT COUNT(*) FROM stats WHERE id = 1;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (id, current_streak, last_active_date, total_focus_minutes) VALUES (1, 1, DATE('now'), 0);")

    # Seed realistic CA Intermediate sample subjects & chapters if empty
    cursor.execute("SELECT COUNT(*) FROM subjects;")
    if cursor.fetchone()[0] == 0:
        _seed_sample_syllabus(cursor)

    conn.commit()
    conn.close()

def _seed_sample_syllabus(cursor):
    sample_data = [
        {
            "id": "sub_acc",
            "code": "Paper 1",
            "name": "Advanced Accounting",
            "group": "Group 1",
            "chapters": [
                (1, "Framework for Preparation and Presentation of Financial Statements", "completed", "Important theoretical foundation."),
                (2, "Accounting Standards (AS 1, 2, 3, 10, 11, 12, 13)", "in_progress", "Focus on AS 10 (Property, Plant and Equipment) & AS 2 (Inventories)."),
                (3, "Financial Statements of Companies (Schedule III)", "not_started", ""),
                (4, "Buy Back of Securities & Equity Shares with Differential Rights", "not_started", ""),
                (5, "Amalgamation and Reconstruction of Companies", "not_started", "Heavy weightage chapter."),
                (6, "Accounting for Branches including Foreign Branches", "not_started", ""),
            ]
        },
        {
            "id": "sub_law",
            "code": "Paper 2",
            "name": "Corporate and Other Laws",
            "group": "Group 1",
            "chapters": [
                (1, "Preliminary & Incorporation of Company (Sec 1-22)", "completed", "Revise memorandum and articles clauses."),
                (2, "Prospectus and Allotment of Securities (Sec 23-42)", "in_progress", "Private placement provisions."),
                (3, "Share Capital and Debentures (Sec 43-72)", "not_started", ""),
                (4, "Acceptance of Deposits by Companies (Sec 73-76A)", "not_started", ""),
                (5, "Management & Administration - General Meetings (Sec 88-122)", "not_started", "Crucial for exam scenario questions."),
                (6, "The General Clauses Act, 1897", "not_started", ""),
            ]
        },
        {
            "id": "sub_tax",
            "code": "Paper 3",
            "name": "Taxation (Income Tax & GST)",
            "group": "Group 1",
            "chapters": [
                (1, "Basic Concepts & Residential Status", "completed", "Formula for days of stay in India."),
                (2, "Heads of Income - Salaries", "in_progress", "Standard deduction & perquisites valuation."),
                (3, "Heads of Income - Profits & Gains of Business or Profession (PGBP)", "not_started", "Watch out for Sec 43B disallowances."),
                (4, "Heads of Income - Capital Gains", "not_started", ""),
                (5, "GST - Concept of Supply under CGST Act", "completed", "Schedule I, II, III items."),
                (6, "GST - Input Tax Credit (ITC - Sec 16, 17, 18)", "in_progress", "Section 17(5) blocked credits are high-yield!"),
            ]
        },
        {
            "id": "sub_cost",
            "code": "Paper 4",
            "name": "Cost and Management Accounting",
            "group": "Group 2",
            "chapters": [
                (1, "Material Cost & EOQ Analysis", "completed", "EOQ formula & safety stock levels."),
                (2, "Employee Cost and Direct Expenses", "not_started", ""),
                (3, "Overheads: Absorption Costing Method", "not_started", ""),
                (4, "Cost Sheet Preparation", "in_progress", ""),
                (5, "Standard Costing and Variance Analysis", "not_started", "Material and Labour variances."),
                (6, "Marginal Costing & Break-Even Analysis", "not_started", "P/V ratio and Margin of Safety."),
            ]
        },
        {
            "id": "sub_audit",
            "code": "Paper 5",
            "name": "Auditing and Ethics",
            "group": "Group 2",
            "chapters": [
                (1, "Nature, Objective and Scope of Audit (SA 200)", "completed", "Inherent limitations of audit."),
                (2, "Audit Strategy, Planning and Programming (SA 300)", "not_started", ""),
                (3, "Risk Assessment and Internal Control (SA 315)", "not_started", ""),
                (4, "Audit Documentation and Evidence (SA 230, 500)", "in_progress", "Sufficiency & appropriateness of audit evidence."),
                (5, "Company Audit (Sec 139 to 148)", "not_started", "Auditor appointment & disqualifications (Sec 141)."),
            ]
        },
    ]

    for sub in sample_data:
        cursor.execute("INSERT INTO subjects (id, code, name, group_name) VALUES (?, ?, ?, ?);",
                       (sub["id"], sub["code"], sub["name"], sub["group"]))
        for ch in sub["chapters"]:
            ch_id = f"{sub['id']}_ch{ch[0]}"
            cursor.execute("INSERT INTO chapters (id, subject_id, chapter_num, title, status, notes) VALUES (?, ?, ?, ?, ?, ?);",
                           (ch_id, sub["id"], ch[0], ch[1], ch[2], ch[3]))

    # Seed initial tasks
    initial_tasks = [
        ("task_1", "Practice 3 practical problems on Section 17(5) GST Blocked Credits", "sub_tax", 1),
        ("task_2", "Revise Standard on Auditing (SA) 500 Audit Evidence definitions", "sub_audit", 1),
        ("task_3", "Calculate 5 Variance Analysis problems in Costing", "sub_cost", 0),
        ("task_4", "Complete 20 minutes Box Breathing session", None, 0),
    ]
    for t in initial_tasks:
        cursor.execute("INSERT INTO tasks (id, title, subject_id, completed) VALUES (?, ?, ?, ?);", t)
