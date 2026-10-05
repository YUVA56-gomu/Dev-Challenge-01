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

    # --- Legacy Compatibility Tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id TEXT PRIMARY KEY,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        group_name TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chapters (
        id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        chapter_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'not_started',
        notes TEXT DEFAULT '',
        FOREIGN KEY (subject_id) REFERENCES subjects(id)
    );
    """)

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_streak INTEGER NOT NULL DEFAULT 1,
        last_active_date TEXT,
        total_focus_minutes INTEGER NOT NULL DEFAULT 0
    );
    """)

    # --- Phase 2: Full CA Syllabus Hierarchy ---
    # 1. Stages (Foundation, Intermediate, Final)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_stages (
        id TEXT PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        syllabus_version TEXT NOT NULL DEFAULT 'ICAI New Scheme 2024-2025'
    );
    """)

    # 2. Groups (e.g. Group 1, Group 2)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_groups (
        id TEXT PRIMARY KEY,
        stage_id TEXT NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (stage_id) REFERENCES ca_stages(id)
    );
    """)

    # 3. Papers (e.g. Paper 1: Advanced Accounting)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_papers (
        id TEXT PRIMARY KEY,
        group_id TEXT NOT NULL,
        stage_id TEXT NOT NULL,
        paper_num INTEGER NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        total_marks INTEGER DEFAULT 100,
        FOREIGN KEY (group_id) REFERENCES ca_groups(id),
        FOREIGN KEY (stage_id) REFERENCES ca_stages(id)
    );
    """)

    # 4. Modules
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_modules (
        id TEXT PRIMARY KEY,
        paper_id TEXT NOT NULL,
        module_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        FOREIGN KEY (paper_id) REFERENCES ca_papers(id)
    );
    """)

    # 5. Chapters (Scalable syllabus entity with progress & pedagogical metadata)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_chapters (
        id TEXT PRIMARY KEY,
        module_id TEXT NOT NULL,
        paper_id TEXT NOT NULL,
        chapter_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        learning_objective TEXT,
        estimated_minutes INTEGER DEFAULT 120,
        prerequisites TEXT,
        statutory_reference TEXT,
        status TEXT NOT NULL DEFAULT 'not_started', -- not_started, in_progress, completed, needs_revision
        confidence_score INTEGER DEFAULT 3,         -- 1 to 5
        revision_count INTEGER DEFAULT 0,
        last_studied TIMESTAMP,
        last_revised TIMESTAMP,
        notes TEXT DEFAULT '',
        questions_attempted INTEGER DEFAULT 0,
        questions_correct INTEGER DEFAULT 0,
        weak_areas TEXT DEFAULT '',
        FOREIGN KEY (module_id) REFERENCES ca_modules(id),
        FOREIGN KEY (paper_id) REFERENCES ca_papers(id)
    );
    """)

    # 6. Topics (Granular section-level breakdown for RAG & Ask Sathi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_topics (
        id TEXT PRIMARY KEY,
        chapter_id TEXT NOT NULL,
        topic_num INTEGER NOT NULL,
        title TEXT NOT NULL,
        statutory_section TEXT,
        learning_objective TEXT,
        estimated_minutes INTEGER DEFAULT 45,
        exam_weightage TEXT DEFAULT 'Medium', -- High, Medium, Low
        status TEXT NOT NULL DEFAULT 'not_started',
        confidence_score INTEGER DEFAULT 3,
        notes TEXT DEFAULT '',
        FOREIGN KEY (chapter_id) REFERENCES ca_chapters(id)
    );
    """)

    # 7. Semantic Memories (Phase 2J: Local semantic/episodic memory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semantic_memories (
        id TEXT PRIMARY KEY,
        student_id TEXT DEFAULT 'pooja',
        memory_text TEXT NOT NULL,
        memory_type TEXT DEFAULT 'preference', -- preference, struggle, habit, topic_interest
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # =========================================================================
    # PHASE 3: EXAM PRACTICE & ANSWER EVALUATION ENGINE TABLES
    # =========================================================================

    # 8. Questions Library
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        stage_id TEXT NOT NULL,
        group_id TEXT,
        paper_id TEXT NOT NULL,
        chapter_id TEXT NOT NULL,
        topic_id TEXT,
        difficulty TEXT NOT NULL DEFAULT 'Medium', -- Easy, Medium, Hard
        question_type TEXT NOT NULL DEFAULT 'Theory', -- MCQ, Short Answer, Theory, Numerical, Practical
        marks INTEGER NOT NULL DEFAULT 5,
        expected_time_minutes INTEGER DEFAULT 10,
        source TEXT NOT NULL DEFAULT 'Sathi AI Practice Question',
        source_document TEXT,
        source_page INTEGER,
        question_text TEXT NOT NULL,
        options TEXT, -- JSON array string for MCQs, e.g. ["A...", "B..."]
        correct_answer TEXT,
        solution TEXT NOT NULL,
        marking_scheme TEXT,
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 9. Question Attempts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_attempts (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        question_id TEXT NOT NULL,
        user_answer TEXT NOT NULL,
        score REAL NOT NULL DEFAULT 0,
        max_score REAL NOT NULL DEFAULT 5,
        is_correct INTEGER NOT NULL DEFAULT 0, -- 1 for full/substantive pass, 0 for incorrect/partial
        time_spent_seconds INTEGER DEFAULT 0,
        evaluation_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)

    # 10. Answer Evaluations (Structured AI Marking Engine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answer_evaluations (
        id TEXT PRIMARY KEY,
        attempt_id TEXT NOT NULL,
        question_id TEXT NOT NULL,
        score REAL NOT NULL,
        max_score REAL NOT NULL,
        concept_score_pct REAL DEFAULT 0,
        calculation_score_pct REAL DEFAULT 0,
        presentation_score_pct REAL DEFAULT 0,
        is_ai_assisted INTEGER DEFAULT 1,
        strengths TEXT DEFAULT '[]', -- JSON array
        mistakes TEXT DEFAULT '[]', -- JSON array
        missing_concepts TEXT DEFAULT '[]', -- JSON array
        step_feedback TEXT DEFAULT '[]', -- JSON array of { step, feedback, marks_awarded, max_marks }
        ideal_answer TEXT,
        revision_topics TEXT DEFAULT '[]', -- JSON array
        spoken_explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (attempt_id) REFERENCES question_attempts(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)

    # 11. Topic Performance Profile (Weak topic detection)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS topic_performance (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        topic_id TEXT NOT NULL,
        chapter_id TEXT NOT NULL,
        paper_id TEXT NOT NULL,
        questions_attempted INTEGER DEFAULT 0,
        questions_correct INTEGER DEFAULT 0,
        questions_incorrect INTEGER DEFAULT 0,
        total_score_earned REAL DEFAULT 0,
        total_max_score REAL DEFAULT 0,
        accuracy_pct REAL DEFAULT 0,
        average_score_pct REAL DEFAULT 0,
        repeated_mistakes TEXT DEFAULT '[]', -- JSON array of strings
        status TEXT DEFAULT 'Needs Revision', -- Mastered, Proficient, Needs Revision, Critical Weak Area
        last_attempted TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_revised TIMESTAMP,
        UNIQUE(student_id, topic_id)
    );
    """)

    # 12. Spaced Revision Schedule (Day 1, Day 3, Day 7, Day 14, Day 30)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS revision_schedule (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        topic_id TEXT NOT NULL,
        chapter_id TEXT NOT NULL,
        paper_id TEXT NOT NULL,
        interval_day INTEGER DEFAULT 1,
        scheduled_date DATE NOT NULL,
        is_completed INTEGER DEFAULT 0,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 13. Exam Mode Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_sessions (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        title TEXT NOT NULL,
        paper_id TEXT NOT NULL,
        total_questions INTEGER NOT NULL,
        total_marks INTEGER NOT NULL,
        time_limit_minutes INTEGER NOT NULL,
        time_spent_seconds INTEGER DEFAULT 0,
        score_obtained REAL DEFAULT 0,
        accuracy_pct REAL DEFAULT 0,
        status TEXT DEFAULT 'in_progress', -- in_progress, completed, abandoned
        strong_areas TEXT DEFAULT '[]',
        weak_areas TEXT DEFAULT '[]',
        recommended_steps TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """)

    # 14. Exam Session Answers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_answers (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        question_id TEXT NOT NULL,
        user_answer TEXT DEFAULT '',
        score REAL DEFAULT 0,
        max_score REAL DEFAULT 0,
        is_correct INTEGER DEFAULT 0,
        feedback TEXT DEFAULT '',
        FOREIGN KEY (session_id) REFERENCES exam_sessions(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """)

    # Phase 4 questions schema migration
    existing_cols = [c[1] for c in cursor.execute("PRAGMA table_info(questions);").fetchall()]
    if "module_id" not in existing_cols:
        cursor.execute("ALTER TABLE questions ADD COLUMN module_id TEXT;")
    if "source_type" not in existing_cols:
        cursor.execute("ALTER TABLE questions ADD COLUMN source_type TEXT DEFAULT 'ICAI_STUDY_MATERIAL';")
    if "source_year" not in existing_cols:
        cursor.execute("ALTER TABLE questions ADD COLUMN source_year TEXT;")
    if "model_solution" not in existing_cols:
        cursor.execute("ALTER TABLE questions ADD COLUMN model_solution TEXT;")
    if "is_official" not in existing_cols:
        cursor.execute("ALTER TABLE questions ADD COLUMN is_official INTEGER DEFAULT 1;")

    # 15. Sanctuary: Reflections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanctuary_reflections (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        reflection_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 16. Sanctuary: Mood / Check-ins
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanctuary_checkins (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        mood TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 17. Sanctuary: Focus Sessions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanctuary_focus_sessions (
        id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL DEFAULT 'pooja',
        duration_minutes INTEGER NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 18. Ingested Documents Registry (Phase 4 Document Ingestion Engine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingested_documents (
        document_id TEXT PRIMARY KEY,
        file_name TEXT NOT NULL,
        file_path TEXT,
        file_format TEXT NOT NULL,
        file_hash TEXT UNIQUE NOT NULL,
        document_title TEXT NOT NULL,
        source_type TEXT NOT NULL,
        issuing_body TEXT NOT NULL,
        stage TEXT NOT NULL,
        group_name TEXT,
        paper TEXT NOT NULL,
        module TEXT,
        chapter TEXT,
        total_pages INTEGER NOT NULL DEFAULT 1,
        total_chunks INTEGER NOT NULL DEFAULT 0,
        document_version TEXT,
        effective_date TEXT,
        ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 16. Knowledge Chunks with Provenance & Hashes (Phase 4 Knowledge Store)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_chunks (
        chunk_id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL REFERENCES ingested_documents(document_id) ON DELETE CASCADE,
        document_title TEXT NOT NULL,
        source_type TEXT NOT NULL,
        issuing_body TEXT NOT NULL,
        stage TEXT NOT NULL,
        group_name TEXT,
        paper TEXT NOT NULL,
        module TEXT,
        chapter TEXT NOT NULL,
        topic TEXT,
        statutory_reference TEXT,
        page_number INTEGER NOT NULL,
        document_version TEXT,
        effective_date TEXT,
        content TEXT NOT NULL,
        content_hash TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Performance Indexes for Knowledge Chunks
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_doc ON knowledge_chunks(document_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_paper ON knowledge_chunks(paper);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_statutory ON knowledge_chunks(statutory_reference);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kchunks_hash ON knowledge_chunks(content_hash);")

    # Knowledge FTS5 Virtual Table
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
        chunk_id UNINDEXED,
        document_title,
        statutory_reference,
        topic,
        chapter,
        paper,
        content,
        tokenize = 'porter unicode61'
    );
    """)

    # Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_paper_chap ON questions(paper_id, chapter_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON question_attempts(student_id, created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic_perf_student ON topic_performance(student_id, topic_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_revision_sched ON revision_schedule(student_id, scheduled_date, is_completed);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_sessions_student ON exam_sessions(student_id, created_at);")

    # Seed initial stats if empty
    cursor.execute("SELECT COUNT(*) FROM stats WHERE id = 1;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (id, current_streak, last_active_date, total_focus_minutes) VALUES (1, 1, DATE('now'), 0);")

    # Seed legacy subjects if empty
    cursor.execute("SELECT COUNT(*) FROM subjects;")
    if cursor.fetchone()[0] == 0:
        _seed_sample_syllabus(cursor)

    # Seed full hierarchical syllabus if empty
    cursor.execute("SELECT COUNT(*) FROM ca_stages;")
    if cursor.fetchone()[0] == 0:
        _seed_full_ca_syllabus(cursor)

    # Seed practice questions (seed or upgrade to full Phase 4 corpus if count < 20)
    cursor.execute("SELECT COUNT(*) FROM questions;")
    if cursor.fetchone()[0] < 20:
        _seed_practice_questions(cursor)

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


def _seed_full_ca_syllabus(cursor):
    """
    Populates official ICAI syllabus hierarchy for CA Foundation, Intermediate, and Final,
    focusing on CA Intermediate Group 1 & 2 for student Pooja.
    Source: ICAI New Scheme of Education and Training (2024-2025).
    """
    # 1. Stages
    stages = [
        ("stage_foundation", "FOUNDATION", "CA Foundation", "Entry-level foundation examination covering accounting, business laws, quantitative aptitude, and economics.", "ICAI New Scheme 2024-2025"),
        ("stage_intermediate", "INTERMEDIATE", "CA Intermediate", "First core professional examination comprising Group 1 and Group 2 (6 Papers).", "ICAI New Scheme 2024-2025"),
        ("stage_final", "FINAL", "CA Final", "Final examination stage covering advanced corporate laws, strategic financial management, advanced taxation, and multidisciplinary case study.", "ICAI New Scheme 2024-2025"),
    ]
    for s in stages:
        cursor.execute("INSERT INTO ca_stages (id, code, name, description, syllabus_version) VALUES (?, ?, ?, ?, ?);", s)

    # 2. Groups (Intermediate)
    groups = [
        ("grp_inter_1", "stage_intermediate", "Group 1", "CA Intermediate Group 1 (Papers 1, 2, 3)"),
        ("grp_inter_2", "stage_intermediate", "Group 2", "CA Intermediate Group 2 (Papers 4, 5, 6)"),
    ]
    for g in groups:
        cursor.execute("INSERT INTO ca_groups (id, stage_id, code, name) VALUES (?, ?, ?, ?);", g)

    # 3. Papers
    papers = [
        ("paper_inter_1", "grp_inter_1", "stage_intermediate", 1, "Paper 1", "Advanced Accounting", 100),
        ("paper_inter_2", "grp_inter_1", "stage_intermediate", 2, "Paper 2", "Corporate and Other Laws", 100),
        ("paper_inter_3", "grp_inter_1", "stage_intermediate", 3, "Paper 3", "Taxation (Income Tax & GST)", 100),
        ("paper_inter_4", "grp_inter_2", "stage_intermediate", 4, "Paper 4", "Cost and Management Accounting", 100),
        ("paper_inter_5", "grp_inter_2", "stage_intermediate", 5, "Paper 5", "Auditing and Ethics", 100),
        ("paper_inter_6", "grp_inter_2", "stage_intermediate", 6, "Paper 6", "Financial Management and Strategic Management", 100),
    ]
    for p in papers:
        cursor.execute("INSERT INTO ca_papers (id, group_id, stage_id, paper_num, code, name, total_marks) VALUES (?, ?, ?, ?, ?, ?, ?);", p)

    # 4. Modules
    modules = [
        ("mod_acc_1", "paper_inter_1", 1, "Accounting Standards & Framework"),
        ("mod_acc_2", "paper_inter_1", 2, "Company Accounts & Reconstruction"),
        ("mod_law_1", "paper_inter_2", 1, "Company Law (Companies Act, 2013)"),
        ("mod_law_2", "paper_inter_2", 2, "Other Laws (General Clauses & FEMA)"),
        ("mod_tax_1", "paper_inter_3", 1, "Direct Tax (Income-tax Act, 1961)"),
        ("mod_tax_2", "paper_inter_3", 2, "Indirect Tax (Goods & Services Tax)"),
        ("mod_cost_1", "paper_inter_4", 1, "Cost Accounting Fundamentals"),
        ("mod_audit_1", "paper_inter_5", 1, "Standards on Auditing & Evidence"),
        ("mod_audit_2", "paper_inter_5", 2, "Company Audit & Auditor Duties"),
        ("mod_fm_1", "paper_inter_6", 1, "Financial Management"),
    ]
    for m in modules:
        cursor.execute("INSERT INTO ca_modules (id, paper_id, module_num, title) VALUES (?, ?, ?, ?);", m)

    # 5. Chapters (with progress & pedagogical metadata)
    chapters = [
        # Paper 1
        ("ch_acc_as10", "mod_acc_1", "paper_inter_1", 1, "Property, Plant and Equipment (AS 10)",
         "Accounting for tangible non-current assets, depreciation allocation, and revaluation model.",
         "Understand initial recognition, component depreciation, and disposal accounting under AS 10.",
         90, "Financial accounting fundamentals", "AS 10 (Revised)", "in_progress", 3, 2, "2026-10-02", "2026-10-02",
         "Focus on component depreciation and revaluation surplus treatment.", 5, 4, "De-recognition on early sale"),

        ("ch_acc_sched3", "mod_acc_2", "paper_inter_1", 2, "Financial Statements of Companies (Schedule III)",
         "Presentation of balance sheet and statement of profit and loss under Schedule III to the Companies Act, 2013.",
         "Draft corporate balance sheet with proper classification of current and non-current items.",
         120, "Company accounting basics", "Schedule III, Companies Act, 2013", "not_started", 3, 0, None, None,
         "", 0, 0, ""),

        # Paper 2
        ("ch_law_audit", "mod_law_1", "paper_inter_2", 1, "Audit and Auditors (Sections 139 to 148)",
         "Statutory provisions on appointment, qualifications, disqualifications, and duties of auditors.",
         "Master statutory rules for auditor appointment (Sec 139), rotation, ceiling limits, and disqualifications (Sec 141).",
         120, "Company management concepts", "Sections 139 to 148 Companies Act, 2013", "in_progress", 3, 1, "2026-10-01", "2026-10-01",
         "Section 139(6) vs 139(7) first auditor rules are high-frequency exam questions.", 8, 6, "Casual vacancy by resignation vs disqualification"),

        ("ch_law_meetings", "mod_law_1", "paper_inter_2", 2, "Management & Administration (Sections 88 to 122)",
         "Registers, annual returns, general meetings, notices, quorum, and voting rights.",
         "Analyze quorum requirements under Section 103 and valid resolutions passed at AGMs and EGMs.",
         90, "Preliminary company concepts", "Sections 88-122 Companies Act, 2013", "completed", 4, 2, "2026-09-28", "2026-09-30",
         "Quorum formulas: 5/15/30 for public companies depending on total members.", 10, 9, ""),

        # Paper 3
        ("ch_tax_itc", "mod_tax_2", "paper_inter_3", 1, "Input Tax Credit (Sections 16, 17, 18)",
         "Mechanics of claiming ITC under GST and statutory restrictions under Section 17(5).",
         "Compute eligible and ineligible ITC, apply Section 17(5) blocked credit provisions with precision.",
         150, "Concept of Supply (Sec 7)", "Sections 16, 17, 18 CGST Act, 2017", "in_progress", 2, 2, "2026-10-03", "2026-10-03",
         "Section 17(5) blocked credits frequently tested. High probability area.", 12, 7, "Motor vehicles passenger capacity exceptions and food/beverage credit"),

        ("ch_tax_salaries", "mod_tax_1", "paper_inter_3", 2, "Heads of Income - Salaries (Sections 15 to 17)",
         "Taxation of employment income, standard deduction, perquisite valuations, and exemptions.",
         "Calculate gross salary, perquisite values under Rule 3, and taxable salary.",
         120, "Residential status", "Sections 15-17 Income-tax Act, 1961", "completed", 4, 3, "2026-09-25", "2026-10-01",
         "Standard deduction ₹50,000 / ₹75,000 under new tax regime.", 15, 13, ""),

        # Paper 5
        ("ch_audit_sa200", "mod_audit_1", "paper_inter_5", 1, "Overall Objectives of the Independent Auditor (SA 200)",
         "Foundational standard establishing professional skepticism, reasonable assurance, and audit limitations.",
         "State auditor's two overall objectives and explain inherent limitations of an audit.",
         80, "Auditing basics", "SA 200 issued by ICAI", "completed", 5, 3, "2026-09-22", "2026-09-29",
         "Mnemonic: Inherent limitations arise from nature of financial reporting, nature of audit procedures, and timeliness.", 10, 10, ""),

        ("ch_audit_evidence", "mod_audit_1", "paper_inter_5", 2, "Audit Documentation & Evidence (SA 230 & SA 500)",
         "Sufficient appropriate audit evidence, documentation retention, and working papers ownership.",
         "Evaluate reliability of evidence (external > internal, written > oral, original > photocopies).",
         100, "SA 200 concepts", "SA 230 & SA 500", "in_progress", 3, 1, "2026-10-02", "2026-10-02",
         "SQC 1 retention period: minimum 7 years.", 6, 5, "Management representation limitations"),
    ]

    for ch in chapters:
        cursor.execute("""
        INSERT INTO ca_chapters (
            id, module_id, paper_id, chapter_num, title, description, learning_objective,
            estimated_minutes, prerequisites, statutory_reference, status, confidence_score,
            revision_count, last_studied, last_revised, notes, questions_attempted, questions_correct, weak_areas
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, ch)

    # 6. Topics (Granular section breakdown)
    topics = [
        # Topics for AS 10
        ("top_acc_as10_1", "ch_acc_as10", 1, "Recognition Criteria & Initial Measurement", "AS 10 para 7-14",
         "Determine items eligible for capitalization as PPE.", 45, "High", "completed", 4, "Purchase price + directly attributable costs - trade discounts."),
        ("top_acc_as10_2", "ch_acc_as10", 2, "Depreciation & Useful Life Allocation", "AS 10 para 58-62",
         "Systematic allocation over useful life, review of residual values and depreciation methods.", 50, "High", "in_progress", 3, "Useful life review is an accounting estimate change (prospective)."),
        ("top_acc_as10_3", "ch_acc_as10", 3, "Disposal and Early Sale of Assets", "AS 10 para 67-72",
         "Calculate profit or loss on disposal when an asset is sold before useful life ends.", 40, "Medium", "not_started", 2, "Difference between net disposal proceeds and carrying amount."),

        # Topics for Company Audit (Sec 139-148)
        ("top_law_sec139", "ch_law_audit", 1, "Appointment of First and Subsequent Auditors (Section 139)", "Section 139 Companies Act 2013",
         "Distinguish appointment in government vs non-government companies.", 60, "High", "in_progress", 3, "Non-govt first auditor: BOD within 30 days, else EGM within 90 days."),
        ("top_law_sec140", "ch_law_audit", 2, "Removal, Resignation of Auditor & Special Notice (Section 140)", "Section 140 Companies Act 2013",
         "Procedure for auditor removal before term (Central Govt approval required) and resignation filing Form ADT-3.", 45, "Medium", "not_started", 3, ""),
        ("top_law_sec141", "ch_law_audit", 3, "Eligibility, Qualifications and Disqualifications (Section 141)", "Section 141 Companies Act 2013",
         "Memorize statutory disqualifications: body corporate, officer/employee, partner, indebtedness > 5 lakhs, business relationship.", 60, "High", "not_started", 2, "Ceiling limit: 20 companies per partner excluding dormant/OPC/small/pvt < 100 cr."),

        # Topics for ITC (Sec 16-18)
        ("top_tax_sec16", "ch_tax_itc", 1, "Eligibility & 4 Golden Conditions for ITC (Section 16)", "Section 16 CGST Act 2017",
         "4 conditions: tax invoice, received goods/services, tax paid to govt, return filed under Sec 39.", 45, "High", "completed", 4, "Payment to supplier within 180 days rule."),
        ("top_tax_sec17_5", "ch_tax_itc", 2, "Blocked Credits under Section 17(5)", "Section 17(5) CGST Act 2017",
         "Identify blocked items: motor vehicles <= 13 persons unless used for further supply/training, food & beverages, personal consumption, lost/written off.", 75, "High", "in_progress", 2, "Weak area: Motor vehicles seating capacity test & mandatory employee services."),
        ("top_tax_sec18", "ch_tax_itc", 3, "Credit in Special Circumstances (Section 18)", "Section 18 CGST Act 2017",
         "ITC on inputs held in stock on applying for registration or switching from composition to normal levy.", 45, "Medium", "not_started", 3, ""),

        # Topics for SA 200
        ("top_audit_sa200_1", "ch_audit_sa200", 1, "Overall Objectives & Reasonable Assurance", "SA 200 para 11",
         "Two objectives: obtain reasonable assurance (high but not absolute level) and report on financial statements.", 40, "High", "completed", 5, "Reasonable assurance is high, but not an absolute guarantee."),
        ("top_audit_sa200_2", "ch_audit_sa200", 2, "Inherent Limitations of an Audit", "SA 200 para A45-A52",
         "Nature of financial reporting, nature of audit procedures, timeliness and balance between benefit and cost.", 40, "High", "completed", 5, "Fundamental concept tested in almost every alternate exam!"),
    ]

    for t in topics:
        cursor.execute("""
        INSERT INTO ca_topics (
            id, chapter_id, topic_num, title, statutory_section, learning_objective,
            estimated_minutes, exam_weightage, status, confidence_score, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, t)

    # 7. Semantic Memories (Pooja's student learning profile)
    memories = [
        ("mem_1", "pooja", "Student prefers clear simple real-world examples before jumping into statutory language.", "preference"),
        ("mem_2", "pooja", "Student struggled with motor vehicle passenger capacity exceptions under Section 17(5) blocked credits.", "struggle"),
        ("mem_3", "pooja", "Student asked for depreciation and AS 10 mnemonics for exam revision.", "topic_interest"),
        ("mem_4", "pooja", "Student prepares best with calm encouraging tone, practical exam examples, and 45-minute focus intervals.", "habit"),
    ]
    for m in memories:
        cursor.execute("INSERT INTO semantic_memories (id, student_id, memory_text, memory_type) VALUES (?, ?, ?, ?);", m)


def _seed_practice_questions(cursor):
    """
    Seeds verified practice questions with explicit source provenance
    (ICAI RTP, MTP, Past Exams, or clearly labeled Sathi AI Practice Questions).
    Covers CA Foundation, CA Intermediate, and CA Final.
    """
    questions = [
        # --- CA INTERMEDIATE: TAXATION (PAPER 3 / GST) ---
        (
            "q_tax_itc_1", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_2", "ch_tax_itc", "top_tax_sec17_5",
            "Medium", "Practical", 5, 12, "ICAI RTP — May 2026", "ICAI Study Material Paper 4: Taxation (GST)", 142,
            "RTP", "2026",
            "XYZ Ltd., a registered manufacturer in Pune, purchased the following motor vehicles and related services during August:\n(i) A motor car for transportation of its directors with seating capacity of 5 persons costing ₹12,00,000 (GST paid ₹2,16,000).\n(ii) A mini-bus for transportation of factory employees with seating capacity of 22 persons costing ₹25,00,000 (GST paid ₹4,50,000).\n(iii) General insurance policy taken for the motor car mentioned in (i) above (GST paid ₹18,000).\nDetermine the eligible Input Tax Credit (ITC) available to XYZ Ltd. under Section 17(5) of the CGST Act, 2017, giving reasons for each item.",
            None,
            "Total Eligible ITC = ₹4,50,000 (mini-bus only; car and its insurance are blocked).",
            "(i) Motor car for directors (seating capacity 5 <= 13): ITC is BLOCKED under Section 17(5)(a) of the CGST Act, 2017, as motor vehicles for transportation of persons having approved seating capacity <= 13 persons are ineligible unless used for further supply, passenger transport, or training. Eligible ITC = Nil.\n(ii) Mini-bus for employees (seating capacity 22 > 13): ITC is FULLY ELIGIBLE under Section 17(5)(a), since the seating capacity exceeds 13 persons. Eligible ITC = ₹4,50,000.\n(iii) General insurance for motor car: ITC is BLOCKED under Section 17(5)(ab) since insurance, servicing, and repair relating to motor vehicles where ITC is blocked under clause (a) are also ineligible. Eligible ITC = Nil.\nTotal Eligible ITC = ₹4,50,000.",
            "(i) Motor car for directors (seating capacity 5 <= 13): ITC is BLOCKED under Section 17(5)(a) of the CGST Act, 2017, as motor vehicles for transportation of persons having approved seating capacity <= 13 persons are ineligible unless used for further supply, passenger transport, or training. Eligible ITC = Nil.\n(ii) Mini-bus for employees (seating capacity 22 > 13): ITC is FULLY ELIGIBLE under Section 17(5)(a), since the seating capacity exceeds 13 persons. Eligible ITC = ₹4,50,000.\n(iii) General insurance for motor car: ITC is BLOCKED under Section 17(5)(ab) since insurance, servicing, and repair relating to motor vehicles where ITC is blocked under clause (a) are also ineligible. Eligible ITC = Nil.\nTotal Eligible ITC = ₹4,50,000.",
            "1. Citing Section 17(5)(a) threshold (<=13 blocked) for car: 1.5 Marks\n2. Identifying Nil credit for car: 0.5 Mark\n3. Citing eligibility for 22-seater bus (>13 persons): 1.5 Marks\n4. Citing blocked insurance under Section 17(5)(ab): 1.5 Marks",
            "Under Section 17(5)(a) of the CGST Act, 2017, ITC on motor vehicles for transportation of persons is restricted to vehicles with approved seating capacity > 13 persons. Ancillary services like insurance follow the taxability of the underlying vehicle under Section 17(5)(ab).",
            1
        ),
        (
            "q_tax_sec16_1", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_2", "ch_tax_itc", "top_tax_sec16",
            "Medium", "Theory", 5, 12, "ICAI Past Exam — Nov 2023", "ICAI Study Material Paper 4: Taxation (GST)", 135,
            "PAST_EXAM", "2023",
            "State the four primary statutory conditions that a registered person must satisfy to become entitled to claim Input Tax Credit (ITC) under Section 16(2) of the CGST Act, 2017.",
            None,
            "1. Possession of tax invoice/debit note; 2. Receipt of goods or services; 3. Tax actually paid to government; 4. Filing of return under Section 39.",
            "Under Section 16(2) of the CGST Act, 2017, a registered person is entitled to ITC only if:\n1. Possession of tax invoice or debit note issued by a registered supplier, or other taxpaying document prescribed under Section 31.\n2. Details of the invoice have been communicated to the recipient in Form GSTR-2B under Section 38.\n3. The registered person has actually received the goods or services or both.\n4. The tax charged in respect of such supply has been actually paid to the Government, either in cash or through utilization of eligible ITC.\n5. The registered person has furnished the valid return under Section 39 (Form GSTR-3B).",
            "Under Section 16(2) of the CGST Act, 2017, a registered person is entitled to ITC only if:\n1. Possession of tax invoice or debit note issued by a registered supplier, or other taxpaying document prescribed under Section 31.\n2. Details of the invoice have been communicated to the recipient in Form GSTR-2B under Section 38.\n3. The registered person has actually received the goods or services or both.\n4. The tax charged in respect of such supply has been actually paid to the Government, either in cash or through utilization of eligible ITC.\n5. The registered person has furnished the valid return under Section 39 (Form GSTR-3B).",
            "1. Tax invoice/debit note possession: 1 Mark\n2. GSTR-2B communication: 1 Mark\n3. Actual receipt of goods/services: 1 Mark\n4. Tax paid to Government: 1 Mark\n5. Furnishing return under Section 39: 1 Mark",
            "Section 16(2) conditions are mandatory and cumulative. If any single condition is not met, ITC cannot be legally availed.",
            1
        ),
        (
            "q_tax_sec10_1", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_2", "ch_tax_itc", "top_tax_sec10",
            "Medium", "Theory", 4, 10, "ICAI Study Material Paper 4: Taxation (GST)", "ICAI Study Material Paper 4: Taxation (GST)", 78,
            "ICAI_STUDY_MATERIAL", "2024",
            "Explain the threshold limits for opting into the Composition Scheme under Section 10(1) and 10(2) of the CGST Act, 2017 for manufacturers and traders. Name two categories of suppliers who are disqualified from opting for composition levy.",
            None,
            "Threshold is ₹1.5 Crore aggregate turnover in preceding financial year (₹75 Lakhs for Special Category States). Ineligible: service providers (except restaurant), suppliers of non-taxable goods, interstate suppliers, e-commerce operators.",
            "1. Threshold Limit: Under Section 10(1) of the CGST Act, 2017, a registered person whose aggregate turnover in the preceding financial year did not exceed ₹1.5 Crore (₹75 Lakhs for 8 Special Category States: Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura, Uttarakhand) may opt for the composition scheme.\n2. Disqualified Suppliers: Persons ineligible under Section 10(2) include:\n- Suppliers of goods not leviable to tax under GST (e.g. alcoholic liquor, petroleum products).\n- Persons making any inter-state outward supplies of goods.\n- Persons supplying goods through an Electronic Commerce Operator (ECO) required to collect tax under Section 52.\n- Manufacturers of notified goods (ice cream, pan masala, tobacco, aerated water).",
            "1. Threshold Limit: Under Section 10(1) of the CGST Act, 2017, a registered person whose aggregate turnover in the preceding financial year did not exceed ₹1.5 Crore (₹75 Lakhs for 8 Special Category States: Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura, Uttarakhand) may opt for the composition scheme.\n2. Disqualified Suppliers: Persons ineligible under Section 10(2) include:\n- Suppliers of goods not leviable to tax under GST (e.g. alcoholic liquor, petroleum products).\n- Persons making any inter-state outward supplies of goods.\n- Persons supplying goods through an Electronic Commerce Operator (ECO) required to collect tax under Section 52.\n- Manufacturers of notified goods (ice cream, pan masala, tobacco, aerated water).",
            "1. Stating ₹1.5 Crore aggregate turnover limit: 1 Mark\n2. Stating ₹75 Lakhs for Special Category States: 1 Mark\n3. Identifying 2 disqualified categories with Section 10(2) reasons: 2 Marks",
            "Section 10 composition scheme is an alternative tax method for small domestic taxpayers without interstate sales.",
            1
        ),
        (
            "q_tax_sec44ad_mcq", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_1", "ch_tax_itc", "top_tax_sec44ad",
            "Easy", "MCQ", 2, 3, "ICAI RTP — May 2026", "ICAI Study Material Paper 3: Income Tax", 198,
            "RTP", "2026",
            "Under Section 44AD of the Income-tax Act, 1961, the maximum turnover threshold for declaring presumptive business profits at 8% (or 6% for digital receipts) stands increased to ₹3 Crore provided:",
            '["Net profit margin is at least 12%", "Cash receipts do not exceed 5% of total turnover", "The assessee is a private limited company", "The assessee maintains audited books under Section 44AB"]',
            "Cash receipts do not exceed 5% of total turnover",
            "Under the amended proviso to Section 44AD(1), the turnover limit is enhanced from ₹2 Crore to ₹3 Crore where aggregate cash receipts during the previous year do not exceed 5% of total turnover.",
            "Under the amended proviso to Section 44AD(1), the turnover limit is enhanced from ₹2 Crore to ₹3 Crore where aggregate cash receipts during the previous year do not exceed 5% of total turnover.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "Finance Act amendment enhanced the Section 44AD ceiling to ₹3 Crore specifically to encourage non-cash digital banking transactions (>= 95% digital).",
            1
        ),
        (
            "q_tax_sec17_5_mcq", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_2", "ch_tax_itc", "top_tax_sec17_5",
            "Easy", "MCQ", 2, 3, "Sathi AI Practice Question", "ICAI Study Material Paper 4: Taxation (GST)", 142,
            "SATHI_GENERATED", "2026",
            "Under Section 17(5)(a) of the CGST Act, 2017, input tax credit is blocked on motor vehicles for transportation of persons having approved seating capacity of:",
            '["Up to 10 persons", "Up to 13 persons (including driver)", "Up to 15 persons", "All motor vehicles regardless of seating capacity"]',
            "Up to 13 persons (including driver)",
            "Section 17(5)(a) of the CGST Act, 2017 specifies that ITC is blocked on motor vehicles for transportation of persons having approved seating capacity of not more than 13 persons (including the driver), subject to exceptions for further supply, passenger transport, and driving training.",
            "Section 17(5)(a) of the CGST Act, 2017 specifies that ITC is blocked on motor vehicles for transportation of persons having approved seating capacity of not more than 13 persons (including the driver), subject to exceptions for further supply, passenger transport, and driving training.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "Remember the statutory threshold: approved seating capacity <= 13 persons (including the driver). If seating capacity > 13 persons (like a 22-seater mini bus), it is outside the blocked credit clause.",
            0
        ),
        (
            "q_sathi_ai_case_1", "stage_intermediate", "grp_inter_1", "paper_tax", "mod_tax_2", "ch_tax_itc", "top_tax_sec17_5",
            "Medium", "Practical", 5, 12, "Sathi AI Practice Question", "ICAI Study Material Paper 4: Taxation (GST)", 144,
            "SATHI_GENERATED", "2026",
            "Zenith Textiles Ltd. employs 320 factory workers. Under the mandatory provisions of Section 46 of the Factories Act, 1948, the company is statutorily required to provide an in-house canteen. During October, Zenith Ltd. incurred GST of ₹90,000 on outdoor catering services for this factory canteen and ₹35,000 on catering for a corporate diwali party for its executives. Examine the eligibility of ITC on both catering expenses under Section 17(5)(b) of the CGST Act, 2017.",
            None,
            "Canteen catering: Eligible ₹90,000 (statutory obligation proviso); Executive party: Blocked ₹35,000.",
            "1. Statutory Obligation Proviso: Under Section 17(5)(b)(i) of the CGST Act, 2017, ITC on food and beverages, outdoor catering is generally blocked. However, the proviso to Section 17(5)(b) states that ITC in respect of such goods or services shall be available where it is obligatory for an employer to provide the same to its employees under any law for the time being in force.\n2. Factory Canteen Catering: Since Zenith Textiles Ltd. employs more than 250 workers, providing a canteen is obligatory under Section 46 of the Factories Act, 1948. Therefore, ITC of ₹90,000 is FULLY ELIGIBLE.\n3. Executive Diwali Party: Not provided under any statutory obligation. ITC of ₹35,000 is BLOCKED under Section 17(5)(b)(i).\nTotal Eligible ITC = ₹90,000.",
            "1. Statutory Obligation Proviso: Under Section 17(5)(b)(i) of the CGST Act, 2017, ITC on food and beverages, outdoor catering is generally blocked. However, the proviso to Section 17(5)(b) states that ITC in respect of such goods or services shall be available where it is obligatory for an employer to provide the same to its employees under any law for the time being in force.\n2. Factory Canteen Catering: Since Zenith Textiles Ltd. employs more than 250 workers, providing a canteen is obligatory under Section 46 of the Factories Act, 1948. Therefore, ITC of ₹90,000 is FULLY ELIGIBLE.\n3. Executive Diwali Party: Not provided under any statutory obligation. ITC of ₹35,000 is BLOCKED under Section 17(5)(b)(i).\nTotal Eligible ITC = ₹90,000.",
            "1. Citing Section 17(5)(b) statutory obligation proviso: 2 Marks\n2. Applying Factories Act Section 46 to allow ₹90,000 credit: 2 Marks\n3. Blocking ₹35,000 diwali party catering: 1 Mark",
            "The statutory obligation proviso overrides the general block on food, beverages, and catering services.",
            0
        ),

        # --- CA INTERMEDIATE: CORPORATE AND OTHER LAWS (PAPER 2) ---
        (
            "q_law_audit_1", "stage_intermediate", "grp_inter_1", "paper_law", "mod_law_1", "ch_law_audit", "top_law_sec139",
            "Medium", "Theory", 4, 10, "ICAI Past Exam — May 2024", "ICAI Study Material Paper 2: Corporate and Other Laws", 118,
            "PAST_EXAM", "2024",
            "Explain the statutory provisions of the Companies Act, 2013 regarding the appointment of the first auditor of a non-government company. What is the legal consequence if the Board of Directors fails to make the appointment within the prescribed period?",
            None,
            "Board must appoint within 30 days of registration; on failure, members appoint within 90 days at an EGM.",
            "1. Appointment by Board of Directors: Under Section 139(6) of the Companies Act, 2013, the first auditor of a company (other than a Government company) shall be appointed by the Board of Directors within 30 days from the date of registration of the company.\n2. Failure of the Board: In the event of failure of the Board to appoint the first auditor within 30 days, the Board shall inform the members of the company.\n3. Appointment by Members: The members shall within 90 days at an Extraordinary General Meeting (EGM) appoint the first auditor.\n4. Tenure: The first auditor so appointed shall hold office until the conclusion of the first Annual General Meeting (AGM).",
            "1. Appointment by Board of Directors: Under Section 139(6) of the Companies Act, 2013, the first auditor of a company (other than a Government company) shall be appointed by the Board of Directors within 30 days from the date of registration of the company.\n2. Failure of the Board: In the event of failure of the Board to appoint the first auditor within 30 days, the Board shall inform the members of the company.\n3. Appointment by Members: The members shall within 90 days at an Extraordinary General Meeting (EGM) appoint the first auditor.\n4. Tenure: The first auditor so appointed shall hold office until the conclusion of the first Annual General Meeting (AGM).",
            "1. Stating Section 139(6) and Board's 30-day timeline: 1.5 Marks\n2. Board informing members upon failure: 0.5 Mark\n3. Members' appointment within 90 days at EGM: 1 Mark\n4. Tenure until conclusion of 1st AGM: 1 Mark",
            "Section 139(6) governs first auditor appointment in non-government companies. Note that the 90 days for members starts from the date of information by the Board, and tenure is strictly up to the first AGM.",
            1
        ),
        (
            "q_law_audit_2", "stage_intermediate", "grp_inter_1", "paper_law", "mod_law_1", "ch_law_audit", "top_law_sec141",
            "Easy", "MCQ", 2, 3, "ICAI MTP — Nov 2025", "ICAI Study Material Paper 2: Corporate and Other Laws", 130,
            "MTP", "2025",
            "Under Section 141(3)(d)(i) of the Companies Act, 2013 read with relevant rules, a relative of an auditor may hold securities or interest in the company of face value not exceeding which of the following thresholds?",
            '["₹10,000", "₹50,000", "₹1,00,000", "₹5,00,000"]',
            "₹1,00,000",
            "Under the proviso to Section 141(3)(d)(i) read with Rule 10 of Companies (Audit and Auditors) Rules, 2014, a relative may hold security or interest in the company of face value not exceeding ₹1,00,000.",
            "Under the proviso to Section 141(3)(d)(i) read with Rule 10 of Companies (Audit and Auditors) Rules, 2014, a relative may hold security or interest in the company of face value not exceeding ₹1,00,000.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "The statutory threshold is face value of ₹1,00,000 for relatives only (not the auditor themselves or their partner). If the relative exceeds ₹1,00,000, a grace period of 60 days is allowed to correct the holding.",
            1
        ),
        (
            "q_law_sec140_1", "stage_intermediate", "grp_inter_1", "paper_law", "mod_law_1", "ch_law_audit", "top_law_sec140",
            "Medium", "Practical", 5, 12, "ICAI RTP — May 2025", "ICAI Study Material Paper 2: Corporate and Other Laws", 125,
            "RTP", "2025",
            "The Board of Directors of Apex Solar Ltd. decided in a meeting held on 10th July to remove their statutory auditor, CA Raman, whose 5-year tenure has not yet expired. The Board passed a resolution at the Board meeting and immediately served a termination notice to CA Raman. Examine whether the removal is legally valid under Section 140(1) of the Companies Act, 2013.",
            None,
            "Removal is legally INVALID. Board must obtain prior approval of Central Government in Form ADT-2 and pass a Special Resolution in general meeting.",
            "Under Section 140(1) of the Companies Act, 2013 read with Rule 7 of Companies (Audit and Auditors) Rules, 2014:\n1. The auditor appointed under Section 139 may be removed from office before the expiry of his term only by a Special Resolution of the company, after obtaining the prior approval of the Central Government (Regional Director).\n2. Application to Central Government: The company must file Form ADT-2 within 30 days of passing the Board resolution.\n3. General Meeting: The company shall hold a general meeting within 60 days of receiving Central Government approval to pass the special resolution.\n4. Reasonable Opportunity: The auditor must be given a reasonable opportunity of being heard.\nConclusion: Apex Solar Ltd. did not obtain Central Government approval nor passed a special resolution. Hence, the removal is void ab initio.",
            "Under Section 140(1) of the Companies Act, 2013 read with Rule 7 of Companies (Audit and Auditors) Rules, 2014:\n1. The auditor appointed under Section 139 may be removed from office before the expiry of his term only by a Special Resolution of the company, after obtaining the prior approval of the Central Government (Regional Director).\n2. Application to Central Government: The company must file Form ADT-2 within 30 days of passing the Board resolution.\n3. General Meeting: The company shall hold a general meeting within 60 days of receiving Central Government approval to pass the special resolution.\n4. Reasonable Opportunity: The auditor must be given a reasonable opportunity of being heard.\nConclusion: Apex Solar Ltd. did not obtain Central Government approval nor passed a special resolution. Hence, the removal is void ab initio.",
            "1. Stating requirement of Central Government prior approval (Form ADT-2 within 30 days): 2 Marks\n2. Stating requirement of Special Resolution within 60 days of approval: 1.5 Marks\n3. Stating right of being heard: 0.5 Mark\n4. Conclusion that removal is invalid: 1 Mark",
            "Removal before expiry of term is heavily restricted under Section 140(1) to protect auditor independence from board intimidation.",
            1
        ),
        (
            "q_law_sec103_mcq", "stage_intermediate", "grp_inter_1", "paper_law", "mod_law_1", "ch_law_meetings", "top_law_sec103",
            "Easy", "MCQ", 2, 3, "ICAI Past Exam — May 2024", "ICAI Study Material Paper 2: Corporate and Other Laws", 92,
            "PAST_EXAM", "2024",
            "Under Section 103 of the Companies Act, 2013, what is the statutory quorum for a public company general meeting if the total number of members on the date of meeting is 2,450?",
            '["5 members personally present", "15 members personally present", "30 members personally present", "50 members personally present"]',
            "15 members personally present",
            "Under Section 103(1)(a)(ii) of the Companies Act, 2013, for a public company, if the number of members is more than 1,000 but up to 5,000, the quorum is 15 members personally present.",
            "Under Section 103(1)(a)(ii) of the Companies Act, 2013, for a public company, if the number of members is more than 1,000 but up to 5,000, the quorum is 15 members personally present.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "Statutory Quorum for Public Companies: Up to 1000 members = 5; 1001 to 5000 = 15; Exceeding 5000 = 30 members personally present.",
            1
        ),
        (
            "q_law_sec88_1", "stage_intermediate", "grp_inter_1", "paper_law", "mod_law_1", "ch_law_meetings", "top_law_sec88",
            "Easy", "Short Answer", 3, 6, "ICAI Study Material Paper 2: Corporate and Other Laws", "ICAI Study Material Paper 2: Corporate and Other Laws", 85,
            "ICAI_STUDY_MATERIAL", "2024",
            "List the statutory registers required to be maintained by every company under Section 88 of the Companies Act, 2013.",
            None,
            "Register of members (MGT-1), Register of debenture holders (MGT-2), Register of other security holders (MGT-2), and Foreign Register.",
            "Under Section 88(1) of the Companies Act, 2013, every company shall keep and maintain the following registers:\n1. Register of members separately for equity and preference shares (Form MGT-1).\n2. Register of debenture-holders (Form MGT-2).\n3. Register of any other security-holders (Form MGT-2).\n4. Foreign register of members, debenture-holders or other security-holders residing outside India (Section 88(4)).",
            "Under Section 88(1) of the Companies Act, 2013, every company shall keep and maintain the following registers:\n1. Register of members separately for equity and preference shares (Form MGT-1).\n2. Register of debenture-holders (Form MGT-2).\n3. Register of any other security-holders (Form MGT-2).\n4. Foreign register of members, debenture-holders or other security-holders residing outside India (Section 88(4)).",
            "1. Register of members: 1 Mark\n2. Register of debenture-holders & other security holders: 1 Mark\n3. Foreign register mention: 1 Mark",
            "Section 88 registers are permanent company records kept at the registered office unless approved by special resolution for keeping at another place.",
            1
        ),

        # --- CA INTERMEDIATE: ADVANCED ACCOUNTING (PAPER 1) ---
        (
            "q_acc_as10_1", "stage_intermediate", "grp_inter_1", "paper_adv_acc", "mod_acc_1", "ch_acc_as10", "top_acc_as10_1",
            "Hard", "Numerical", 6, 15, "ICAI Past Exam — Nov 2024", "ICAI Study Material Paper 1: Advanced Accounting", 85,
            "PAST_EXAM", "2024",
            "PQR Ltd. acquired a heavy manufacturing plant on 1st April 2024. The following expenses were incurred:\n1. Purchase price as per supplier invoice: ₹50,00,000\n2. Trade discount allowed by supplier: ₹2,00,000\n3. Non-refundable import duties: ₹5,00,000\n4. Site preparation costs: ₹3,00,000\n5. Initial delivery and handling charges: ₹1,50,000\n6. Professional consultancy fees for installation: ₹2,50,000\n7. Cost of testing whether the plant is functioning properly: ₹1,00,000\n8. Initial operating losses incurred before full capacity: ₹4,00,000\nCalculate the initial cost of Property, Plant and Equipment to be capitalized as per AS 10 (Revised).",
            None,
            "Total Capitalized Cost = ₹61,00,000 (Initial operating losses of ₹4,00,000 are expensed).",
            "As per AS 10 (Revised) 'Property, Plant and Equipment':\nCapitalized Cost Components:\n- Purchase price less trade discount (₹50,00,000 - ₹2,00,000) = ₹48,00,000\n- Non-refundable import duties = ₹5,00,000\n- Directly attributable costs:\n  * Site preparation = ₹3,00,000\n  * Delivery & handling = ₹1,50,000\n  * Installation & professional fees = ₹2,50,000\n  * Testing costs = ₹1,00,000\nTotal Capitalized Cost = ₹48,00,000 + ₹5,00,000 + ₹3,00,000 + ₹1,50,000 + ₹2,50,000 + ₹1,00,000 = ₹61,00,000.\nNote: Initial operating losses of ₹4,00,000 are NOT capitalized as they are incurred after the asset is capable of operating in the intended manner.",
            "As per AS 10 (Revised) 'Property, Plant and Equipment':\nCapitalized Cost Components:\n- Purchase price less trade discount (₹50,00,000 - ₹2,00,000) = ₹48,00,000\n- Non-refundable import duties = ₹5,00,000\n- Directly attributable costs:\n  * Site preparation = ₹3,00,000\n  * Delivery & handling = ₹1,50,000\n  * Installation & professional fees = ₹2,50,000\n  * Testing costs = ₹1,00,000\nTotal Capitalized Cost = ₹48,00,000 + ₹5,00,000 + ₹3,00,000 + ₹1,50,000 + ₹2,50,000 + ₹1,00,000 = ₹61,00,000.\nNote: Initial operating losses of ₹4,00,000 are NOT capitalized as they are incurred after the asset is capable of operating in the intended manner.",
            "1. Correct net purchase price calculation: 1 Mark\n2. Inclusion of non-refundable import duties: 1 Mark\n3. Inclusion of directly attributable costs (site, delivery, installation, testing): 2.5 Marks\n4. Proper exclusion of initial operating losses with AS 10 reasoning: 1.5 Marks",
            "AS 10 paragraph 17 explicitly excludes costs incurred while an item capable of operating in the manner intended by management has yet to be brought into use or is operated at less than full capacity.",
            1
        ),
        (
            "q_acc_as2_1", "stage_intermediate", "grp_inter_1", "paper_adv_acc", "mod_acc_1", "ch_acc_as10", "top_acc_as2",
            "Medium", "Numerical", 5, 12, "ICAI RTP — May 2026", "ICAI Study Material Paper 1: Advanced Accounting", 52,
            "RTP", "2026",
            "On 31st March 2025, Galaxy Ltd. holds 1,000 units of raw material 'R' purchased at ₹120 per unit. Replacement cost of 'R' is ₹100 per unit. The finished product 'F' in which 'R' is incorporated is expected to sell at ₹250 per unit. The further cost of processing 'R' into 'F' is ₹110 per unit.\n(a) Determine the value of inventory of raw material 'R' under AS 2.\n(b) How would your answer change if the finished product 'F' is expected to sell at ₹210 per unit?",
            None,
            "(a) Raw material valued at cost ₹120,000; (b) Raw material valued at replacement cost ₹100,000.",
            "Under AS 2 'Valuation of Inventories':\nMaterials and other supplies held for use in the production of inventories are not written down below cost if the finished products in which they will be incorporated are expected to be sold at or above cost.\n(a) Total cost of finished product 'F' = Raw material cost (₹120) + Processing cost (₹110) = ₹230.\nExpected selling price = ₹250 (which exceeds cost ₹230).\nTherefore, raw material 'R' should NOT be written down and is valued at COST = 1,000 * ₹120 = ₹1,20,000.\n(b) If selling price is ₹210, it is below total cost ₹230 (loss of ₹20 per unit).\nHere, raw material 'R' must be written down to its REPLACEMENT COST = 1,000 * ₹100 = ₹1,00,000.",
            "Under AS 2 'Valuation of Inventories':\nMaterials and other supplies held for use in the production of inventories are not written down below cost if the finished products in which they will be incorporated are expected to be sold at or above cost.\n(a) Total cost of finished product 'F' = Raw material cost (₹120) + Processing cost (₹110) = ₹230.\nExpected selling price = ₹250 (which exceeds cost ₹230).\nTherefore, raw material 'R' should NOT be written down and is valued at COST = 1,000 * ₹120 = ₹1,20,000.\n(b) If selling price is ₹210, it is below total cost ₹230 (loss of ₹20 per unit).\nHere, raw material 'R' must be written down to its REPLACEMENT COST = 1,000 * ₹100 = ₹1,00,000.",
            "1. Citing the AS 2 rule on raw materials valuation: 1.5 Marks\n2. Case (a) valuation at cost with comparison: 1.5 Marks\n3. Case (b) write down to replacement cost when finished goods sell at loss: 2 Marks",
            "Key principle in AS 2 paragraph 24: Raw materials are never written down unless the finished product is expected to be sold at a loss.",
            1
        ),
        (
            "q_acc_sched3_1", "stage_intermediate", "grp_inter_1", "paper_adv_acc", "mod_acc_2", "ch_acc_sched3", "top_acc_sched3",
            "Medium", "Practical", 5, 12, "ICAI Past Exam — Nov 2024", "ICAI Study Material Paper 1: Advanced Accounting", 112,
            "PAST_EXAM", "2024",
            "Vortex Ltd. has an operating cycle of 16 months. The company has trade receivables amounting to ₹15,00,000 due for recovery after 14 months from the reporting date, and another ₹8,00,000 due for recovery after 18 months. Classify each of these trade receivables as Current or Non-Current as per Schedule III to the Companies Act, 2013, giving reasons.",
            None,
            "₹15,00,000 is Current Asset (within operating cycle of 16 months); ₹8,00,000 is Non-Current Asset (exceeds operating cycle).",
            "As per Schedule III (Division I) to the Companies Act, 2013, an asset shall be classified as Current when it satisfies any of the following criteria:\n(a) It is expected to be realized in, or is intended for sale or consumption in, the company's normal operating cycle; or\n(b) It is held primarily for the purpose of being traded; or\n(c) It is expected to be realized within twelve months after the reporting date.\nApplication:\n1. Trade Receivables of ₹15,00,000 due after 14 months: Even though realization exceeds 12 months, it is within the company's normal operating cycle of 16 months. Hence, it is a CURRENT ASSET.\n2. Trade Receivables of ₹8,00,000 due after 18 months: Realization period (18 months) exceeds both 12 months and the operating cycle (16 months). Hence, it is a NON-CURRENT ASSET.",
            "As per Schedule III (Division I) to the Companies Act, 2013, an asset shall be classified as Current when it satisfies any of the following criteria:\n(a) It is expected to be realized in, or is intended for sale or consumption in, the company's normal operating cycle; or\n(b) It is held primarily for the purpose of being traded; or\n(c) It is expected to be realized within twelve months after the reporting date.\nApplication:\n1. Trade Receivables of ₹15,00,000 due after 14 months: Even though realization exceeds 12 months, it is within the company's normal operating cycle of 16 months. Hence, it is a CURRENT ASSET.\n2. Trade Receivables of ₹8,00,000 due after 18 months: Realization period (18 months) exceeds both 12 months and the operating cycle (16 months). Hence, it is a NON-CURRENT ASSET.",
            "1. Stating Schedule III criteria for Current Assets: 1.5 Marks\n2. Classifying ₹15 Lakhs as Current with 16-month cycle rationale: 2 Marks\n3. Classifying ₹8 Lakhs as Non-Current: 1.5 Marks",
            "Schedule III explicitly prioritizes the operating cycle for trade receivables and inventory over the standard 12-month calendar cutoff.",
            1
        ),
        (
            "q_acc_as16_mcq", "stage_intermediate", "grp_inter_1", "paper_adv_acc", "mod_acc_1", "ch_acc_as10", "top_acc_as16",
            "Easy", "MCQ", 2, 3, "ICAI MTP — Nov 2025", "ICAI Study Material Paper 1: Advanced Accounting", 95,
            "MTP", "2025",
            "Under AS 16 'Borrowing Costs', a qualifying asset is an asset that necessarily takes which period of time to get ready for its intended use or sale?",
            '["More than 3 months", "More than 6 months", "A substantial period of time (ordinarily 12 months or more)", "Exactly 24 months"]',
            "A substantial period of time (ordinarily 12 months or more)",
            "AS 16 defines a qualifying asset as an asset that necessarily takes a substantial period of time to get ready for its intended use or sale. In practice and judicial precedents, a period of 12 months or more is ordinarily considered substantial.",
            "AS 16 defines a qualifying asset as an asset that necessarily takes a substantial period of time to get ready for its intended use or sale. In practice and judicial precedents, a period of 12 months or more is ordinarily considered substantial.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "Borrowing costs directly attributable to qualifying assets are capitalized, while those for non-qualifying assets are expensed immediately.",
            1
        ),
        (
            "q_sathi_ai_num_1", "stage_intermediate", "grp_inter_1", "paper_adv_acc", "mod_acc_1", "ch_acc_as10", "top_acc_as16",
            "Medium", "Numerical", 5, 12, "Sathi AI Practice Question", "ICAI Study Material Paper 1: Advanced Accounting", 98,
            "SATHI_GENERATED", "2026",
            "On 1st April 2024, Sun Ltd. borrowed ₹20,00,000 at 12% p.a. specifically to construct a commercial warehouse (qualifying asset). Construction commenced on 1st April and continued until 31st December 2024, when the warehouse was ready for use. During this period, idle funds were invested in short-term bank fixed deposits earning interest income of ₹30,000. Calculate the borrowing cost eligible for capitalization under AS 16.",
            None,
            "Borrowing cost capitalized = ₹1,50,000 (Interest cost ₹1,80,000 - Interest income ₹30,000).",
            "As per AS 16 'Borrowing Costs':\n1. Period of Capitalization: 1st April 2024 to 31st December 2024 = 9 months.\n2. Total Borrowing Cost Incurred = ₹20,00,000 * 12% * (9/12) = ₹1,80,000.\n3. Temporary Investment Income: Under AS 16 paragraph 10, any investment income earned on the temporary investment of specific borrowings should be deducted from borrowing costs incurred.\nNet Borrowing Cost Capitalized = ₹1,80,000 - ₹30,000 = ₹1,50,000.\nInterest after 31st December 2024 (remaining 3 months = ₹60,000) must be charged to the Statement of Profit and Loss.",
            "As per AS 16 'Borrowing Costs':\n1. Period of Capitalization: 1st April 2024 to 31st December 2024 = 9 months.\n2. Total Borrowing Cost Incurred = ₹20,00,000 * 12% * (9/12) = ₹1,80,000.\n3. Temporary Investment Income: Under AS 16 paragraph 10, any investment income earned on the temporary investment of specific borrowings should be deducted from borrowing costs incurred.\nNet Borrowing Cost Capitalized = ₹1,80,000 - ₹30,000 = ₹1,50,000.\nInterest after 31st December 2024 (remaining 3 months = ₹60,000) must be charged to the Statement of Profit and Loss.",
            "1. Determining 9-month capitalization period: 1 Mark\n2. Calculating 9-month interest (₹1,80,000): 1.5 Marks\n3. Deducting temporary investment income (₹30,000): 1.5 Marks\n4. Net capitalized amount ₹1,50,000 and expensing remaining ₹60,000: 1 Mark",
            "Capitalization must cease when substantially all activities necessary to prepare the qualifying asset for intended use are complete.",
            0
        ),

        # --- CA INTERMEDIATE: AUDITING AND ETHICS (PAPER 5) ---
        (
            "q_audit_sa200_1", "stage_intermediate", "grp_inter_2", "paper_audit", "mod_audit_1", "ch_audit_sa200", "top_audit_sa200_1",
            "Medium", "Theory", 5, 12, "ICAI RTP — May 2026", "ICAI Study Material Paper 5: Auditing and Ethics", 45,
            "RTP", "2026",
            "'An audit does not provide an absolute guarantee that the financial statements are free from material misstatement.' Discuss this statement in light of SA 200, highlighting the inherent limitations of an audit.",
            None,
            "Auditor obtains reasonable assurance, not absolute assurance, due to inherent limitations of an audit.",
            "Under SA 200 'Overall Objectives of the Independent Auditor', the auditor is required to obtain reasonable assurance, which is a high, but not absolute, level of assurance.\nAbsolute assurance is unattainable due to the inherent limitations of an audit:\n1. Nature of Financial Reporting: Involves judgment by management in applying financial reporting frameworks and subjective estimates.\n2. Nature of Audit Procedures: Management or third parties may not provide complete information; fraud may involve sophisticated concealment; statutory audit is not an official investigation.\n3. Balance between Benefit and Cost: The audit needs to be conducted within a reasonable period of time and at a reasonable cost.\n4. Future Events: Events that may cause the entity to cease to continue as a going concern cannot be predicted with certainty.",
            "Under SA 200 'Overall Objectives of the Independent Auditor', the auditor is required to obtain reasonable assurance, which is a high, but not absolute, level of assurance.\nAbsolute assurance is unattainable due to the inherent limitations of an audit:\n1. Nature of Financial Reporting: Involves judgment by management in applying financial reporting frameworks and subjective estimates.\n2. Nature of Audit Procedures: Management or third parties may not provide complete information; fraud may involve sophisticated concealment; statutory audit is not an official investigation.\n3. Balance between Benefit and Cost: The audit needs to be conducted within a reasonable period of time and at a reasonable cost.\n4. Future Events: Events that may cause the entity to cease to continue as a going concern cannot be predicted with certainty.",
            "1. Defining reasonable vs absolute assurance under SA 200: 1.5 Marks\n2. Inherent limitations - Nature of financial reporting: 1 Mark\n3. Inherent limitations - Nature of audit procedures & fraud: 1 Mark\n4. Inherent limitations - Balance of benefit/cost and future events: 1.5 Marks",
            "SA 200 paragraph 11 and A45-A52 explicitly outline that an audit is not an official investigation and the auditor's opinion is not an absolute guarantee of future viability.",
            1
        ),
        (
            "q_audit_sa230_1", "stage_intermediate", "grp_inter_2", "paper_audit", "mod_audit_1", "ch_audit_sa230", "top_audit_sa230",
            "Medium", "Theory", 4, 10, "ICAI Past Exam — Nov 2024", "ICAI Study Material Paper 5: Auditing and Ethics", 68,
            "PAST_EXAM", "2024",
            "Explain the statutory rules governing the assembly of the final audit file and the minimum retention period of audit documentation as prescribed under SA 230 and SQC 1.",
            None,
            "Assembly of final audit file ordinarily not more than 60 days after auditor's report date; retention period is minimum 7 years.",
            "Under SA 230 'Audit Documentation' read with SQC 1 'Quality Control for Firms':\n1. Assembly of the Final Audit File: The auditor shall assemble the audit documentation in an audit file and complete the administrative process of assembling the final audit file on a timely basis after the date of the auditor's report. An appropriate time limit for completing the assembly is ordinarily not more than 60 days after the date of the auditor's report.\n2. Retention Period: The firm shall establish policies and procedures for the retention of engagement documentation. Under SQC 1, the retention period ordinarily is no shorter than seven years from the date of the auditor's report (or group auditor's report if later).\n3. Confidentiality and Custody: Audit documentation is the property of the auditor.",
            "Under SA 230 'Audit Documentation' read with SQC 1 'Quality Control for Firms':\n1. Assembly of the Final Audit File: The auditor shall assemble the audit documentation in an audit file and complete the administrative process of assembling the final audit file on a timely basis after the date of the auditor's report. An appropriate time limit for completing the assembly is ordinarily not more than 60 days after the date of the auditor's report.\n2. Retention Period: The firm shall establish policies and procedures for the retention of engagement documentation. Under SQC 1, the retention period ordinarily is no shorter than seven years from the date of the auditor's report (or group auditor's report if later).\n3. Confidentiality and Custody: Audit documentation is the property of the auditor.",
            "1. Stating 60-day limit for assembly after report date: 1.5 Marks\n2. Stating minimum 7-year retention period under SQC 1: 1.5 Marks\n3. Auditor ownership and confidentiality rule: 1 Mark",
            "Important distinction: 60 days is for administrative file assembly (no new audit work may be performed), and retention is strictly 7 years.",
            1
        ),
        (
            "q_audit_sa500_1", "stage_intermediate", "grp_inter_2", "paper_audit", "mod_audit_1", "ch_audit_sa230", "top_audit_sa500",
            "Medium", "Theory", 5, 12, "ICAI Study Material Paper 5: Auditing and Ethics", "ICAI Study Material Paper 5: Auditing and Ethics", 82,
            "ICAI_STUDY_MATERIAL", "2024",
            "Distinguish between 'Sufficiency' and 'Appropriateness' of audit evidence under SA 500. Discuss three general rules regarding the reliability of audit evidence.",
            None,
            "Sufficiency is measure of quantity; Appropriateness is measure of quality (relevance and reliability). External evidence is more reliable than internal.",
            "Under SA 500 'Audit Evidence':\n1. Sufficiency: The measure of the quantity of audit evidence. It is influenced by the auditor's assessment of the risks of material misstatement and the quality of such audit evidence.\n2. Appropriateness: The measure of the quality of audit evidence; that is, its relevance and its reliability in providing support for the conclusions on which the auditor's opinion is based.\n3. General Rules on Reliability:\n- External evidence obtained from independent sources outside the entity is more reliable than evidence generated internally.\n- Internal evidence is more reliable when the related controls imposed by the entity are effective.\n- Evidence obtained directly by the auditor (e.g. physical observation) is more reliable than evidence obtained indirectly or by inference.\n- Written documentary evidence is more reliable than oral representations.\n- Original documents are more reliable than photocopies or faxes.",
            "Under SA 500 'Audit Evidence':\n1. Sufficiency: The measure of the quantity of audit evidence. It is influenced by the auditor's assessment of the risks of material misstatement and the quality of such audit evidence.\n2. Appropriateness: The measure of the quality of audit evidence; that is, its relevance and its reliability in providing support for the conclusions on which the auditor's opinion is based.\n3. General Rules on Reliability:\n- External evidence obtained from independent sources outside the entity is more reliable than evidence generated internally.\n- Internal evidence is more reliable when the related controls imposed by the entity are effective.\n- Evidence obtained directly by the auditor (e.g. physical observation) is more reliable than evidence obtained indirectly or by inference.\n- Written documentary evidence is more reliable than oral representations.\n- Original documents are more reliable than photocopies or faxes.",
            "1. Defining Sufficiency (quantity) and risk factor: 1.5 Marks\n2. Defining Appropriateness (quality: relevance & reliability): 1.5 Marks\n3. Explaining 3 rules of evidence reliability: 2 Marks",
            "Sufficiency and appropriateness are interrelated. Merely obtaining more evidence cannot compensate for its poor quality.",
            1
        ),
        (
            "q_audit_caro_mcq", "stage_intermediate", "grp_inter_2", "paper_audit", "mod_audit_2", "ch_audit_sa200", "top_audit_caro",
            "Easy", "MCQ", 2, 3, "ICAI MTP — May 2025", "ICAI Study Material Paper 5: Auditing and Ethics", 140,
            "MTP", "2025",
            "Under Clause (ii)(a) of CARO 2020, reporting is mandatory if discrepancies of what magnitude were noticed during physical verification of inventory?",
            '["5% or more in aggregate for each class of inventory", "10% or more in aggregate for each class of inventory", "Exceeding ₹10 Lakhs irrespective of percentage", "Any discrepancy exceeding 1%"]',
            "10% or more in aggregate for each class of inventory",
            "CARO 2020 Clause (ii)(a) requires the auditor to report whether any discrepancies of 10% or more in the aggregate for each class of inventory were noticed and if so, whether they have been properly dealt with in the books of account.",
            "CARO 2020 Clause (ii)(a) requires the auditor to report whether any discrepancies of 10% or more in the aggregate for each class of inventory were noticed and if so, whether they have been properly dealt with in the books of account.",
            "Correct choice: 2 Marks. Incorrect: 0 Marks.",
            "Under CARO 2020, the quantitative threshold of 10% or more in aggregate for each class of inventory is a distinct reporting trigger.",
            1
        ),

        # --- CA INTERMEDIATE: COSTING & FINANCIAL MANAGEMENT (PAPERS 4 & 6) ---
        (
            "q_cost_eoq_1", "stage_intermediate", "grp_inter_2", "paper_cost", "mod_cost_1", "ch_cost_material", "top_cost_eoq",
            "Medium", "Numerical", 6, 15, "ICAI Past Exam — May 2024", "ICAI Study Material Paper 4: Cost and Management Accounting", 42,
            "PAST_EXAM", "2024",
            "A manufacturing company provides the following data regarding its primary raw material:\n- Annual Demand (A) = 10,000 units\n- Ordering Cost per order (O) = ₹160\n- Purchase price per unit = ₹40\n- Carrying Cost per unit per annum (C) = 20% of purchase price\n- Lead time: Minimum 4 days, Average 6 days, Maximum 8 days\n- Daily consumption: Minimum 30 units, Average 40 units, Maximum 50 units\nCalculate:\n1. Economic Order Quantity (EOQ)\n2. Re-order Level\n3. Minimum Stock Level",
            None,
            "EOQ = 632 units; Re-order Level = 400 units; Minimum Stock Level = 160 units.",
            "1. Economic Order Quantity (EOQ) = sqrt((2 * A * O) / C)\nCarrying Cost (C) = 20% of ₹40 = ₹8 per unit per annum.\nEOQ = sqrt((2 * 10,000 * 160) / 8) = sqrt(4,00,000) = 632.45 or 632 units.\n2. Re-order Level = Maximum consumption * Maximum lead time\n= 50 units * 8 days = 400 units.\n3. Minimum Stock Level = Re-order Level - (Average consumption * Average lead time)\n= 400 units - (40 units * 6 days) = 400 - 240 = 160 units.",
            "1. Economic Order Quantity (EOQ) = sqrt((2 * A * O) / C)\nCarrying Cost (C) = 20% of ₹40 = ₹8 per unit per annum.\nEOQ = sqrt((2 * 10,000 * 160) / 8) = sqrt(4,00,000) = 632.45 or 632 units.\n2. Re-order Level = Maximum consumption * Maximum lead time\n= 50 units * 8 days = 400 units.\n3. Minimum Stock Level = Re-order Level - (Average consumption * Average lead time)\n= 400 units - (40 units * 6 days) = 400 - 240 = 160 units.",
            "1. Correct carrying cost and EOQ formula calculation: 2 Marks\n2. Re-order level calculation (Max * Max): 2 Marks\n3. Minimum stock level calculation: 2 Marks",
            "Re-order level formula uses maximum values to prevent stockout under extreme demand/lead time conditions.",
            1
        ),
        (
            "q_cost_var_1", "stage_intermediate", "grp_inter_2", "paper_cost", "mod_cost_1", "ch_cost_material", "top_cost_variance",
            "Medium", "Numerical", 5, 12, "ICAI RTP — May 2026", "ICAI Study Material Paper 4: Cost and Management Accounting", 88,
            "RTP", "2026",
            "Standard material required for producing 1 unit of finished product is 5 kg at ₹20 per kg. During September, 2,000 units of finished output were produced using 10,800 kg of material at ₹19 per kg. Calculate:\n1. Material Cost Variance (MCV)\n2. Material Price Variance (MPV)\n3. Material Usage Variance (MUV)",
            None,
            "MCV = ₹5,200 (A); MPV = ₹10,800 (F); MUV = ₹16,000 (A).",
            "Standard Quantity for actual output (SQ) = 2,000 units * 5 kg = 10,000 kg.\nStandard Price (SP) = ₹20 per kg.\nActual Quantity (AQ) = 10,800 kg.\nActual Price (AP) = ₹19 per kg.\n1. Material Cost Variance (MCV) = (SQ * SP) - (AQ * AP)\n= (10,000 * ₹20) - (10,800 * ₹19) = ₹2,00,000 - ₹2,05,200 = ₹5,200 (Adverse).\n2. Material Price Variance (MPV) = AQ * (SP - AP)\n= 10,800 * (₹20 - ₹19) = ₹10,800 (Favourable).\n3. Material Usage Variance (MUV) = SP * (SQ - AQ)\n= ₹20 * (10,000 - 10,800) = ₹16,000 (Adverse).\nVerification: MCV = MPV + MUV -> 10,800 (F) - 16,000 (A) = 5,200 (A).",
            "Standard Quantity for actual output (SQ) = 2,000 units * 5 kg = 10,000 kg.\nStandard Price (SP) = ₹20 per kg.\nActual Quantity (AQ) = 10,800 kg.\nActual Price (AP) = ₹19 per kg.\n1. Material Cost Variance (MCV) = (SQ * SP) - (AQ * AP)\n= (10,000 * ₹20) - (10,800 * ₹19) = ₹2,00,000 - ₹2,05,200 = ₹5,200 (Adverse).\n2. Material Price Variance (MPV) = AQ * (SP - AP)\n= 10,800 * (₹20 - ₹19) = ₹10,800 (Favourable).\n3. Material Usage Variance (MUV) = SP * (SQ - AQ)\n= ₹20 * (10,000 - 10,800) = ₹16,000 (Adverse).\nVerification: MCV = MPV + MUV -> 10,800 (F) - 16,000 (A) = 5,200 (A).",
            "1. Standard quantity calculation for actual output: 1 Mark\n2. MCV calculation: 1.5 Marks\n3. MPV and MUV calculations: 2 Marks\n4. Reconciliation check: 0.5 Mark",
            "Always calculate Standard Quantity based on ACTUAL production output, not budgeted output.",
            1
        ),
        (
            "q_fm_ratio_1", "stage_intermediate", "grp_inter_2", "paper_fm", "mod_fm_1", "ch_fm_ratios", "top_fm_ratios",
            "Medium", "Numerical", 5, 12, "ICAI Past Exam — May 2024", "ICAI Study Material Paper 6: Financial Management", 54,
            "PAST_EXAM", "2024",
            "Given the following data for Delta Ltd.:\n- Current Ratio = 2.5\n- Quick Ratio (Acid-Test) = 1.5\n- Working Capital (Current Assets - Current Liabilities) = ₹1,80,000\nCalculate:\n1. Current Assets\n2. Current Liabilities\n3. Value of Inventory (assuming no other quick asset exclusions)",
            None,
            "Current Assets = ₹3,00,000; Current Liabilities = ₹1,20,000; Inventory = ₹1,20,000.",
            "1. Working Capital = Current Assets (CA) - Current Liabilities (CL)\nGiven Current Ratio = CA / CL = 2.5 -> CA = 2.5 * CL.\nWorking Capital = 2.5 * CL - CL = 1.5 * CL = ₹1,80,000.\nCurrent Liabilities (CL) = ₹1,80,000 / 1.5 = ₹1,20,000.\n2. Current Assets (CA) = 2.5 * ₹1,20,000 = ₹3,00,000.\n3. Quick Ratio = Quick Assets / CL = 1.5 -> Quick Assets = 1.5 * ₹1,20,000 = ₹1,80,000.\nInventory = Current Assets - Quick Assets = ₹3,00,000 - ₹1,80,000 = ₹1,20,000.",
            "1. Working Capital = Current Assets (CA) - Current Liabilities (CL)\nGiven Current Ratio = CA / CL = 2.5 -> CA = 2.5 * CL.\nWorking Capital = 2.5 * CL - CL = 1.5 * CL = ₹1,80,000.\nCurrent Liabilities (CL) = ₹1,80,000 / 1.5 = ₹1,20,000.\n2. Current Assets (CA) = 2.5 * ₹1,20,000 = ₹3,00,000.\n3. Quick Ratio = Quick Assets / CL = 1.5 -> Quick Assets = 1.5 * ₹1,20,000 = ₹1,80,000.\nInventory = Current Assets - Quick Assets = ₹3,00,000 - ₹1,80,000 = ₹1,20,000.",
            "1. Derivation of Current Liabilities (₹1,20,000): 2 Marks\n2. Derivation of Current Assets (₹3,00,000): 1.5 Marks\n3. Derivation of Inventory (₹1,20,000): 1.5 Marks",
            "Quick Assets exclude inventory and prepaid expenses because they cannot be liquidated immediately without loss.",
            1
        ),

        # --- CA FOUNDATION ---
        (
            "q_found_acc_1", "stage_foundation", None, "paper_found_1", "mod_found_1", "ch_found_brs", "top_found_brs",
            "Medium", "Practical", 5, 12, "ICAI Study Material CA Foundation Paper 1", "ICAI Study Material CA Foundation Paper 1", 62,
            "ICAI_STUDY_MATERIAL", "2024",
            "On 31st March 2025, the Cash Book of Aryan showed a debit balance of ₹15,000. On comparing it with the Bank Passbook, the following discrepancies were noticed:\n1. Cheques issued for ₹6,000 on 28th March were presented to the bank on 4th April.\n2. Cheques paid into bank for ₹4,000 on 29th March were credited by bank on 5th April.\n3. Bank charges of ₹150 debited by bank only in the passbook.\nPrepare a Bank Reconciliation Statement (BRS) as on 31st March 2025 and determine the balance as per Passbook.",
            None,
            "Balance as per Passbook (Credit/Favourable) = ₹16,850.",
            "Bank Reconciliation Statement as on 31st March 2025:\nDebit Balance as per Cash Book = ₹15,000\nAdd: Cheques issued but not yet presented for payment (Cash book decreased, pass book not yet deducted) = +₹6,000\nLess: Cheques deposited but not yet cleared/credited by bank = -₹4,000\nLess: Bank charges debited in passbook not entered in cash book = -₹150\nBalance as per Bank Passbook (Credit) = ₹15,000 + ₹6,000 - ₹4,000 - ₹150 = ₹16,850.",
            "Bank Reconciliation Statement as on 31st March 2025:\nDebit Balance as per Cash Book = ₹15,000\nAdd: Cheques issued but not yet presented for payment (Cash book decreased, pass book not yet deducted) = +₹6,000\nLess: Cheques deposited but not yet cleared/credited by bank = -₹4,000\nLess: Bank charges debited in passbook not entered in cash book = -₹150\nBalance as per Bank Passbook (Credit) = ₹15,000 + ₹6,000 - ₹4,000 - ₹150 = ₹16,850.",
            "1. Proper format of BRS: 1 Mark\n2. Treatment of unpresented cheques (+₹6,000): 1.5 Marks\n3. Treatment of uncredited cheques (-₹4,000): 1.5 Marks\n4. Final Passbook balance calculation (₹16,850): 1 Mark",
            "Starting from debit balance in Cash Book: Items that cause Passbook to be higher are ADDED; items that cause Passbook to be lower are DEDUCTED.",
            1
        ),

        # --- CA FINAL ---
        (
            "q_final_law_1", "stage_final", "grp_final_1", "paper_final_3", "mod_final_1", "ch_final_oppression", "top_final_oppression",
            "Hard", "Practical", 8, 20, "ICAI Past Exam Final — Nov 2024", "ICAI Study Material CA Final Paper 3: Advanced Corporate Laws", 145,
            "PAST_EXAM", "2024",
            "A public company has a paid-up share capital of ₹10 Crores divided into 10,00,000 equity shares of ₹100 each held by 800 members. A petition alleging oppression and mismanagement was filed before the National Company Law Tribunal (NCLT) under Section 241 of the Companies Act, 2013 by 75 members holding an aggregate of 85,000 equity shares.\n(a) Examine whether the petition is maintainable under Section 244 of the Companies Act, 2013.\n(b) Can the NCLT waive the statutory qualification requirements under Section 244(1)?",
            None,
            "(a) Petition is NOT maintainable as neither condition (100 members or 1/10th of total members) is satisfied; (b) NCLT has power to waive requirements upon application.",
            "(a) Maintainability under Section 244(1)(a) of the Companies Act, 2013:\nIn the case of a company having a share capital, the members who have a right to apply under Section 241 shall be:\n1. Not less than 100 members, OR not less than one-tenth of the total number of members, whichever is less; OR\n2. Any member or members holding not less than one-tenth of the issued share capital of the company, provided that the applicant(s) have paid all calls and other sums due on their shares.\nApplication to Facts:\n- Criteria 1: One-tenth of 800 members = 80 members. The petition is signed by 75 members (< 80 members and < 100 members). Condition not met.\n- Criteria 2: Issued shares = 10,00,000 shares. One-tenth = 1,00,000 shares. The petitioners hold 85,000 shares (< 1,00,000 shares). Condition not met.\nConclusion: The petition is NOT maintainable as neither threshold is met.\n(b) Power of Tribunal to Waive:\nUnder the proviso to Section 244(1), the Tribunal (NCLT) may, on an application made to it in this behalf, waive all or any of the requirements specified in clause (a) or clause (b) so as to enable the members to apply under Section 241.",
            "(a) Maintainability under Section 244(1)(a) of the Companies Act, 2013:\nIn the case of a company having a share capital, the members who have a right to apply under Section 241 shall be:\n1. Not less than 100 members, OR not less than one-tenth of the total number of members, whichever is less; OR\n2. Any member or members holding not less than one-tenth of the issued share capital of the company, provided that the applicant(s) have paid all calls and other sums due on their shares.\nApplication to Facts:\n- Criteria 1: One-tenth of 800 members = 80 members. The petition is signed by 75 members (< 80 members and < 100 members). Condition not met.\n- Criteria 2: Issued shares = 10,00,000 shares. One-tenth = 1,00,000 shares. The petitioners hold 85,000 shares (< 1,00,000 shares). Condition not met.\nConclusion: The petition is NOT maintainable as neither threshold is met.\n(b) Power of Tribunal to Waive:\nUnder the proviso to Section 244(1), the Tribunal (NCLT) may, on an application made to it in this behalf, waive all or any of the requirements specified in clause (a) or clause (b) so as to enable the members to apply under Section 241.",
            "1. Stating Section 244(1)(a) numeric criteria (100 members or 1/10th): 2.5 Marks\n2. Stating share capital criteria (1/10th of issued capital): 2 Marks\n3. Application to facts (75 < 80 members, 85k < 100k shares): 2 Marks\n4. Stating NCLT waiver power under Section 244 proviso: 1.5 Marks",
            "Section 244 numerical hurdles prevent vexatious litigation by isolated minority shareholders, but NCLT holds equitable waiver powers.",
            1
        )
    ]

    for q in questions:
        cursor.execute("""
        INSERT OR REPLACE INTO questions (
            id, stage_id, group_id, paper_id, module_id, chapter_id, topic_id,
            difficulty, question_type, marks, expected_time_minutes, source,
            source_document, source_page, source_type, source_year,
            question_text, options, correct_answer, solution, model_solution,
            marking_scheme, explanation, is_official
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, q)


