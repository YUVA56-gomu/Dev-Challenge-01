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
