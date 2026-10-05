from typing import List, Dict, Optional
import uuid
from app.db.database import get_connection

class StudyRepository:
    """
    Repository providing clean CRUD operations for study syllabus,
    chapter progress, daily tasks, and study streak stats.
    """

    @staticmethod
    def get_subjects_with_chapters() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM subjects ORDER BY code;")
        subjects_rows = cursor.fetchall()
        
        results = []
        for s in subjects_rows:
            cursor.execute("SELECT * FROM chapters WHERE subject_id = ? ORDER BY chapter_num;", (s["id"],))
            chapters_rows = cursor.fetchall()
            
            chapters = []
            completed_count = 0
            for c in chapters_rows:
                if c["status"] == "completed":
                    completed_count += 1
                chapters.append({
                    "id": c["id"],
                    "chapter_num": c["chapter_num"],
                    "title": c["title"],
                    "status": c["status"],
                    "notes": c["notes"] or "",
                })
            
            progress = round((completed_count / len(chapters) * 100) if chapters else 0)
            results.append({
                "id": s["id"],
                "code": s["code"],
                "name": s["name"],
                "group_name": s["group_name"],
                "chapters": chapters,
                "total_chapters": len(chapters),
                "completed_chapters": completed_count,
                "progress_percentage": progress,
            })
            
        conn.close()
        return results

    @staticmethod
    def update_chapter(chapter_id: str, status: Optional[str] = None, notes: Optional[str] = None) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
            
        if not fields:
            conn.close()
            return False
            
        params.append(chapter_id)
        cursor.execute(f"UPDATE chapters SET {', '.join(fields)} WHERE id = ?;", params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    @staticmethod
    def get_tasks() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.title, t.completed, t.created_at, s.name as subject_name 
            FROM tasks t 
            LEFT JOIN subjects s ON t.subject_id = s.id 
            ORDER BY t.completed ASC, t.created_at DESC;
        """)
        rows = cursor.fetchall()
        tasks = [{
            "id": r["id"],
            "title": r["title"],
            "completed": bool(r["completed"]),
            "created_at": r["created_at"],
            "subject_name": r["subject_name"] or "General / Wellness",
        } for r in rows]
        conn.close()
        return tasks

    @staticmethod
    def add_task(title: str, subject_id: Optional[str] = None) -> Dict:
        conn = get_connection()
        cursor = conn.cursor()
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        cursor.execute(
            "INSERT INTO tasks (id, title, subject_id, completed) VALUES (?, ?, ?, 0);",
            (task_id, title, subject_id)
        )
        conn.commit()
        conn.close()
        return {"id": task_id, "title": title, "completed": False}

    @staticmethod
    def toggle_task(task_id: str) -> Optional[bool]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT completed FROM tasks WHERE id = ?;", (task_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        new_val = 0 if row["completed"] else 1
        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?;", (new_val, task_id))
        conn.commit()
        conn.close()
        return bool(new_val)

    @staticmethod
    def delete_task(task_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    @staticmethod
    def get_progress_summary() -> Dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_prog FROM chapters;")
        ch_row = cursor.fetchone()
        total_ch = ch_row["total"] or 0
        comp_ch = ch_row["completed"] or 0
        in_prog_ch = ch_row["in_prog"] or 0
        overall_progress = round((comp_ch / total_ch * 100) if total_ch > 0 else 0)

        cursor.execute("SELECT COUNT(*) as total_tasks, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as comp_tasks FROM tasks;")
        t_row = cursor.fetchone()
        total_tasks = t_row["total_tasks"] or 0
        comp_tasks = t_row["comp_tasks"] or 0

        cursor.execute("SELECT current_streak, last_active_date, total_focus_minutes FROM stats WHERE id = 1;")
        st_row = cursor.fetchone()
        
        conn.close()
        return {
            "overall_progress_percentage": overall_progress,
            "total_chapters": total_ch,
            "completed_chapters": comp_ch,
            "in_progress_chapters": in_prog_ch,
            "not_started_chapters": total_ch - comp_ch - in_prog_ch,
            "tasks_total": total_tasks,
            "tasks_completed": comp_tasks,
            "current_streak_days": st_row["current_streak"] if st_row else 1,
            "last_active_date": st_row["last_active_date"] if st_row else "",
            "total_focus_minutes": st_row["total_focus_minutes"] if st_row else 0,
        }

    # --- Phase 2: Full Hierarchy & Recommendations ---

    @staticmethod
    def get_stages() -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ca_stages ORDER BY id;")
        stages = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return stages

    @staticmethod
    def get_hierarchy(stage_id: str = "stage_intermediate") -> Dict:
        """
        Returns complete Stage -> Groups -> Papers -> Modules -> Chapters -> Topics hierarchy
        with pedagogical metadata, revision counts, confidence scores, and learning objectives.
        """
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ca_stages WHERE id = ?;", (stage_id,))
        stage_row = cursor.fetchone()
        if not stage_row:
            conn.close()
            return {}

        stage = dict(stage_row)

        cursor.execute("SELECT * FROM ca_groups WHERE stage_id = ? ORDER BY code;", (stage_id,))
        groups = [dict(g) for g in cursor.fetchall()]

        for g in groups:
            cursor.execute("SELECT * FROM ca_papers WHERE group_id = ? ORDER BY paper_num;", (g["id"],))
            papers = [dict(p) for p in cursor.fetchall()]

            for p in papers:
                cursor.execute("SELECT * FROM ca_modules WHERE paper_id = ? ORDER BY module_num;", (p["id"],))
                modules = [dict(m) for m in cursor.fetchall()]

                for m in modules:
                    cursor.execute("SELECT * FROM ca_chapters WHERE module_id = ? ORDER BY chapter_num;", (m["id"],))
                    chapters = [dict(c) for c in cursor.fetchall()]

                    for c in chapters:
                        cursor.execute("SELECT * FROM ca_topics WHERE chapter_id = ? ORDER BY topic_num;", (c["id"],))
                        c["topics"] = [dict(t) for t in cursor.fetchall()]

                    m["chapters"] = chapters

                p["modules"] = modules

            g["papers"] = papers

        stage["groups"] = groups
        conn.close()
        return stage

    @staticmethod
    def update_ca_chapter(
        chapter_id: str,
        status: Optional[str] = None,
        confidence_score: Optional[int] = None,
        notes: Optional[str] = None,
        weak_areas: Optional[str] = None,
        increment_revision: bool = False
    ) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if confidence_score is not None:
            fields.append("confidence_score = ?")
            params.append(confidence_score)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if weak_areas is not None:
            fields.append("weak_areas = ?")
            params.append(weak_areas)
        if increment_revision:
            fields.append("revision_count = revision_count + 1")
            fields.append("last_revised = CURRENT_TIMESTAMP")
        if status == "in_progress" or status == "completed":
            fields.append("last_studied = CURRENT_TIMESTAMP")

        if not fields:
            conn.close()
            return False

        params.append(chapter_id)
        cursor.execute(f"UPDATE ca_chapters SET {', '.join(fields)} WHERE id = ?;", params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    @staticmethod
    def update_ca_topic(
        topic_id: str,
        status: Optional[str] = None,
        confidence_score: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        fields = []
        params = []
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if confidence_score is not None:
            fields.append("confidence_score = ?")
            params.append(confidence_score)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)

        if not fields:
            conn.close()
            return False

        params.append(topic_id)
        cursor.execute(f"UPDATE ca_topics SET {', '.join(fields)} WHERE id = ?;", params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    @staticmethod
    def add_custom_chapter(
        paper_id: str,
        title: str,
        estimated_minutes: int = 360,
        difficulty: str = "Medium",
        learning_objective: str = ""
    ) -> Dict:
        conn = get_connection()
        cursor = conn.cursor()

        # Find or create a module for this paper
        cursor.execute("SELECT id FROM ca_modules WHERE paper_id = ? ORDER BY module_num LIMIT 1;", (paper_id,))
        mod_row = cursor.fetchone()
        if mod_row:
            module_id = mod_row["id"]
        else:
            module_id = f"mod_{paper_id}_custom"
            cursor.execute(
                "INSERT OR IGNORE INTO ca_modules (id, paper_id, module_num, title) VALUES (?, ?, 99, 'Custom & Additional Modules');",
                (module_id, paper_id)
            )

        # Get next chapter_num
        cursor.execute("SELECT MAX(chapter_num) as max_num FROM ca_chapters WHERE paper_id = ?;", (paper_id,))
        max_row = cursor.fetchone()
        next_num = (max_row["max_num"] or 0) + 1

        chapter_id = f"custom_ch_{uuid.uuid4().hex[:8]}"

        cursor.execute("""
            INSERT INTO ca_chapters (
                id, module_id, paper_id, chapter_num, title, estimated_minutes, learning_objective, status, confidence_score, revision_count, notes, weak_areas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'not_started', 3, 0, '', '');
        """, (chapter_id, module_id, paper_id, next_num, title, estimated_minutes, learning_objective))

        conn.commit()
        conn.close()

        return {
            "id": chapter_id,
            "paper_id": paper_id,
            "module_id": module_id,
            "chapter_num": next_num,
            "title": title,
            "estimated_minutes": estimated_minutes,
            "status": "not_started",
            "confidence_score": 3
        }

    @staticmethod
    def get_student_study_recommendations(student_id: str = "pooja") -> Dict:
        """
        Inspects actual SQLite database state to generate deterministic study recommendations:
        - Chapters that are 'in_progress' or 'needs_revision'
        - Topics with low confidence (<= 2)
        - Identified weak areas
        - Pending study tasks
        - Semantic memory learning preferences
        """
        conn = get_connection()
        cursor = conn.cursor()

        # 1. In-progress / Needs revision chapters
        cursor.execute("""
            SELECT c.id, c.title, c.status, c.confidence_score, c.weak_areas, p.name as paper_name, p.code as paper_code
            FROM ca_chapters c
            JOIN ca_papers p ON c.paper_id = p.id
            WHERE c.status IN ('in_progress', 'needs_revision') OR c.confidence_score <= 2
            ORDER BY c.confidence_score ASC, c.chapter_num ASC
            LIMIT 4;
        """)
        active_chapters = [dict(r) for r in cursor.fetchall()]

        # 2. Low confidence topics
        cursor.execute("""
            SELECT t.id, t.title, t.statutory_section, t.confidence_score, t.exam_weightage, c.title as chapter_title
            FROM ca_topics t
            JOIN ca_chapters c ON t.chapter_id = c.id
            WHERE t.confidence_score <= 2 OR t.status = 'in_progress'
            ORDER BY t.confidence_score ASC
            LIMIT 3;
        """)
        struggle_topics = [dict(r) for r in cursor.fetchall()]

        # 3. Pending tasks
        cursor.execute("SELECT id, title FROM tasks WHERE completed = 0 ORDER BY created_at DESC LIMIT 3;")
        pending_tasks = [dict(r) for r in cursor.fetchall()]

        # 4. Semantic memories
        cursor.execute("SELECT memory_text, memory_type FROM semantic_memories WHERE student_id = ? ORDER BY created_at DESC LIMIT 5;", (student_id,))
        memories = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            "student_id": student_id,
            "target_stage": "CA Intermediate",
            "active_chapters": active_chapters,
            "priority_topics": struggle_topics,
            "pending_tasks": pending_tasks,
            "learning_profile": memories,
        }

