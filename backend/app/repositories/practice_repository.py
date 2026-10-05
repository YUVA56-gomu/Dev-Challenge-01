import json
import uuid
from typing import List, Dict, Optional, Any
from app.db.database import get_connection

class PracticeRepository:
    """
    Data access layer for CA Exam Practice, Question Library,
    Evaluation Records, Topic Performance, Spaced Revision, and Exam Mode.
    """

    @staticmethod
    def get_questions(
        stage_id: Optional[str] = None,
        paper_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        source_type: Optional[str] = None,
        is_official: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM questions WHERE 1=1"
        params = []

        if stage_id:
            query += " AND (stage_id = ? OR stage_id LIKE ? OR paper_id IN (SELECT id FROM ca_papers WHERE stage_id = ? OR stage_id LIKE ?))"
            params.extend([stage_id, f"%{stage_id}%", stage_id, f"%{stage_id}%"])
        if paper_id:
            query += " AND paper_id = ?"
            params.append(paper_id)
        if chapter_id:
            query += " AND chapter_id = ?"
            params.append(chapter_id)
        if topic_id:
            query += " AND topic_id = ?"
            params.append(topic_id)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if question_type:
            query += " AND question_type = ?"
            params.append(question_type)
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        if is_official is not None:
            query += " AND is_official = ?"
            params.append(int(is_official))

        query += " ORDER BY is_official DESC, id ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            if r.get("options"):
                try:
                    r["options"] = json.loads(r["options"])
                except Exception:
                    r["options"] = []
            else:
                r["options"] = None

        conn.close()
        return rows


    @staticmethod
    def get_question_by_id(question_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?;", (question_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        res = dict(row)
        if res.get("options"):
            try:
                res["options"] = json.loads(res["options"])
            except Exception:
                res["options"] = []
        return res

    @staticmethod
    def create_question(data: Dict[str, Any]) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        qid = data.get("id") or f"q_gen_{uuid.uuid4().hex[:8]}"

        options_str = None
        if data.get("options"):
            options_str = json.dumps(data["options"]) if isinstance(data["options"], list) else str(data["options"])

        src_type = data.get("source_type", "SATHI_GENERATED")
        is_off = int(data.get("is_official", 0 if src_type == "SATHI_GENERATED" else 1))
        sol = data.get("solution", "")
        model_sol = data.get("model_solution", sol)

        cursor.execute("""
        INSERT INTO questions (
            id, stage_id, group_id, paper_id, module_id, chapter_id, topic_id,
            difficulty, question_type, marks, expected_time_minutes, source,
            source_document, source_page, source_type, source_year,
            question_text, options, correct_answer, solution, model_solution,
            marking_scheme, explanation, is_official
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            qid,
            data.get("stage_id", "stage_intermediate"),
            data.get("group_id", "grp_inter_1"),
            data.get("paper_id", "paper_tax"),
            data.get("module_id"),
            data.get("chapter_id", "ch_tax_itc"),
            data.get("topic_id"),
            data.get("difficulty", "Medium"),
            data.get("question_type", "Theory"),
            int(data.get("marks", 5)),
            int(data.get("expected_time_minutes", 10)),
            data.get("source", "Sathi AI Practice Question"),
            data.get("source_document"),
            data.get("source_page"),
            src_type,
            data.get("source_year", "2026"),
            data["question_text"],
            options_str,
            data.get("correct_answer"),
            sol,
            model_sol,
            data.get("marking_scheme", ""),
            data.get("explanation", ""),
            is_off
        ))

        conn.commit()

        conn.close()
        return qid

    @staticmethod
    def save_attempt(
        student_id: str,
        question_id: str,
        user_answer: str,
        score: float,
        max_score: float,
        is_correct: bool,
        time_spent_seconds: int = 0
    ) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        attempt_id = f"att_{uuid.uuid4().hex[:8]}"

        cursor.execute("""
        INSERT INTO question_attempts (
            id, student_id, question_id, user_answer, score, max_score,
            is_correct, time_spent_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            attempt_id,
            student_id,
            question_id,
            user_answer,
            score,
            max_score,
            1 if is_correct else 0,
            time_spent_seconds
        ))

        # Also update chapter questions stats in ca_chapters
        cursor.execute("""
        UPDATE ca_chapters
        SET questions_attempted = questions_attempted + 1,
            questions_correct = questions_correct + ?
        WHERE id = (SELECT chapter_id FROM questions WHERE id = ?);
        """, (1 if is_correct else 0, question_id))

        conn.commit()
        conn.close()
        return attempt_id

    @staticmethod
    def save_evaluation(attempt_id: str, question_id: str, eval_data: Dict[str, Any]) -> str:
        conn = get_connection()
        cursor = conn.cursor()
        eval_id = f"eval_{uuid.uuid4().hex[:8]}"

        cursor.execute("""
        INSERT INTO answer_evaluations (
            id, attempt_id, question_id, score, max_score,
            concept_score_pct, calculation_score_pct, presentation_score_pct,
            is_ai_assisted, strengths, mistakes, missing_concepts,
            step_feedback, ideal_answer, revision_topics, spoken_explanation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            eval_id,
            attempt_id,
            question_id,
            eval_data.get("score", 0),
            eval_data.get("max_score", 5),
            eval_data.get("concept_score_pct", 0),
            eval_data.get("calculation_score_pct", 0),
            eval_data.get("presentation_score_pct", 0),
            1 if eval_data.get("is_ai_assisted", True) else 0,
            json.dumps(eval_data.get("strengths", [])),
            json.dumps(eval_data.get("mistakes", [])),
            json.dumps(eval_data.get("missing_concepts", [])),
            json.dumps(eval_data.get("step_feedback", [])),
            eval_data.get("ideal_answer", ""),
            json.dumps(eval_data.get("revision_topics", [])),
            eval_data.get("spoken_explanation", "")
        ))

        # Link evaluation_id in attempt
        cursor.execute("UPDATE question_attempts SET evaluation_id = ? WHERE id = ?;", (eval_id, attempt_id))

        conn.commit()
        conn.close()
        return eval_id

    @staticmethod
    def update_topic_performance(
        student_id: str,
        topic_id: str,
        chapter_id: str,
        paper_id: str,
        is_correct: bool,
        score: float,
        max_score: float,
        mistakes: Optional[List[str]] = None
    ):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM topic_performance WHERE student_id = ? AND topic_id = ?;", (student_id, topic_id))
        row = cursor.fetchone()

        if not row:
            perf_id = f"perf_{uuid.uuid4().hex[:8]}"
            att = 1
            corr = 1 if is_correct else 0
            incorr = 0 if is_correct else 1
            tot_score = score
            tot_max = max_score
            acc = round((corr / att) * 100, 1)
            avg_score = round((tot_score / tot_max) * 100, 1) if tot_max > 0 else 0
            status = "Proficient" if acc >= 75 else "Needs Revision" if acc < 60 else "In Progress"
            mistakes_json = json.dumps(mistakes or [])

            cursor.execute("""
            INSERT INTO topic_performance (
                id, student_id, topic_id, chapter_id, paper_id,
                questions_attempted, questions_correct, questions_incorrect,
                total_score_earned, total_max_score, accuracy_pct, average_score_pct,
                repeated_mistakes, status, last_attempted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                perf_id, student_id, topic_id, chapter_id, paper_id,
                att, corr, incorr, tot_score, tot_max, acc, avg_score,
                mistakes_json, status
            ))
        else:
            cur = dict(row)
            att = cur["questions_attempted"] + 1
            corr = cur["questions_correct"] + (1 if is_correct else 0)
            incorr = cur["questions_incorrect"] + (0 if is_correct else 1)
            tot_score = cur["total_score_earned"] + score
            tot_max = cur["total_max_score"] + max_score
            acc = round((corr / att) * 100, 1)
            avg_score = round((tot_score / tot_max) * 100, 1) if tot_max > 0 else 0

            # Accumulate mistakes
            existing_mistakes = []
            if cur.get("repeated_mistakes"):
                try:
                    existing_mistakes = json.loads(cur["repeated_mistakes"])
                except Exception:
                    pass
            if mistakes:
                for m in mistakes:
                    if m not in existing_mistakes:
                        existing_mistakes.append(m)

            if acc >= 80 and att >= 3:
                status = "Mastered"
            elif acc >= 60:
                status = "Proficient"
            elif acc < 40 and att >= 2:
                status = "Critical Weak Area"
            else:
                status = "Needs Revision"

            cursor.execute("""
            UPDATE topic_performance
            SET questions_attempted = ?,
                questions_correct = ?,
                questions_incorrect = ?,
                total_score_earned = ?,
                total_max_score = ?,
                accuracy_pct = ?,
                average_score_pct = ?,
                repeated_mistakes = ?,
                status = ?,
                last_attempted = CURRENT_TIMESTAMP
            WHERE student_id = ? AND topic_id = ?;
            """, (
                att, corr, incorr, tot_score, tot_max, acc, avg_score,
                json.dumps(existing_mistakes[:10]), status, student_id, topic_id
            ))

        conn.commit()
        conn.close()

    @staticmethod
    def schedule_spaced_revision(
        student_id: str,
        topic_id: str,
        chapter_id: str,
        paper_id: str
    ) -> str:
        """
        Schedules next spaced revision step: Day 1 -> Day 3 -> Day 7 -> Day 14 -> Day 30.
        Dynamically adapts interval based on performance: if repeated mistakes exist
        or accuracy < 50%, prioritizes urgent revision (Day 1 or Day 3).
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Check topic performance for struggle indicators
        cursor.execute("""
        SELECT questions_incorrect, accuracy_pct, repeated_mistakes
        FROM topic_performance
        WHERE student_id = ? AND topic_id = ?;
        """, (student_id, topic_id))
        perf = cursor.fetchone()

        is_repeated_struggle = False
        if perf:
            incurr_count = perf[0] or 0
            acc = perf[1] or 0.0
            if incurr_count >= 2 or acc < 50.0:
                is_repeated_struggle = True

        # Find existing completed intervals for this topic
        cursor.execute("""
        SELECT interval_day FROM revision_schedule
        WHERE student_id = ? AND topic_id = ?
        ORDER BY interval_day DESC LIMIT 1;
        """, (student_id, topic_id))
        last_interval_row = cursor.fetchone()

        intervals = [1, 3, 7, 14, 30]
        if is_repeated_struggle:
            # Escalate priority: restart cycle at Day 1 or Day 3 to prevent memory decay
            next_interval = 1 if (not last_interval_row or last_interval_row[0] > 3) else 3
        elif not last_interval_row:
            next_interval = 1
        else:
            last_val = last_interval_row[0]
            try:
                curr_idx = intervals.index(last_val)
                next_interval = intervals[min(curr_idx + 1, len(intervals) - 1)]
            except ValueError:
                next_interval = 1

        sched_id = f"rev_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO revision_schedule (
            id, student_id, topic_id, chapter_id, paper_id,
            interval_day, scheduled_date, is_completed
        ) VALUES (?, ?, ?, ?, ?, ?, DATE('now', '+' || ? || ' days'), 0);
        """, (sched_id, student_id, topic_id, chapter_id, paper_id, next_interval, next_interval))

        conn.commit()
        conn.close()
        return {
            "id": sched_id,
            "student_id": student_id,
            "topic_id": topic_id,
            "chapter_id": chapter_id,
            "paper_id": paper_id,
            "interval_day": next_interval
        }

    @staticmethod
    def get_due_revisions(student_id: str = "pooja") -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT r.*, t.title as topic_title, c.title as chapter_title, p.name as paper_name
        FROM revision_schedule r
        LEFT JOIN ca_topics t ON r.topic_id = t.id
        LEFT JOIN ca_chapters c ON r.chapter_id = c.id
        LEFT JOIN ca_papers p ON r.paper_id = p.id
        WHERE r.student_id = ? AND r.is_completed = 0
        ORDER BY r.scheduled_date ASC;
        """, (student_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def complete_revision(revision_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE revision_schedule
        SET is_completed = 1, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?;
        """, (revision_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success

    @staticmethod
    def get_weak_topics(student_id: str = "pooja", limit: int = 5) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT tp.*, t.title as topic_title, c.title as chapter_title, p.name as paper_name
        FROM topic_performance tp
        LEFT JOIN ca_topics t ON tp.topic_id = t.id
        LEFT JOIN ca_chapters c ON tp.chapter_id = c.id
        LEFT JOIN ca_papers p ON tp.paper_id = p.id
        WHERE tp.student_id = ? AND (
            tp.status IN ('Needs Revision', 'Critical Weak Area') 
            OR tp.accuracy_pct < 75 
            OR tp.average_score_pct < 60
            OR (tp.repeated_mistakes IS NOT NULL AND tp.repeated_mistakes != '[]')
        )
        ORDER BY tp.accuracy_pct ASC, tp.questions_incorrect DESC, tp.questions_attempted DESC
        LIMIT ?;
        """, (student_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]

        # If empty, extract low confidence topics from syllabus as fallback
        if not rows:
            cursor.execute("""
            SELECT t.id as topic_id, t.chapter_id, c.paper_id, t.title as topic_title,
                   c.title as chapter_title, p.name as paper_name,
                   40 as accuracy_pct, 2 as questions_attempted, 'Needs Revision' as status
            FROM ca_topics t
            JOIN ca_chapters c ON t.chapter_id = c.id
            JOIN ca_papers p ON c.paper_id = p.id
            WHERE t.confidence_score <= 2 OR t.status = 'needs_revision'
            LIMIT ?;
            """, (limit,))
            rows = [dict(r) for r in cursor.fetchall()]

        for r in rows:
            if r.get("repeated_mistakes"):
                try:
                    r["repeated_mistakes"] = json.loads(r["repeated_mistakes"])
                except Exception:
                    r["repeated_mistakes"] = []
            else:
                r["repeated_mistakes"] = []

        conn.close()
        return rows


    @staticmethod
    def get_recent_attempts(student_id: str = "pooja", limit: int = 10) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT qa.*, q.question_text, q.question_type, q.paper_id, q.chapter_id, q.source,
               c.title as chapter_title, p.name as paper_name, ae.strengths, ae.mistakes, ae.missing_concepts
        FROM question_attempts qa
        JOIN questions q ON qa.question_id = q.id
        LEFT JOIN ca_chapters c ON q.chapter_id = c.id
        LEFT JOIN ca_papers p ON q.paper_id = p.id
        LEFT JOIN answer_evaluations ae ON qa.id = ae.attempt_id
        WHERE qa.student_id = ?
        ORDER BY qa.created_at DESC
        LIMIT ?;
        """, (student_id, limit))
        rows = [dict(r) for r in cursor.fetchall()]
        for r in rows:
            for field in ["strengths", "mistakes", "missing_concepts"]:
                if r.get(field):
                    try:
                        r[field] = json.loads(r[field])
                    except Exception:
                        r[field] = []
                else:
                    r[field] = []
        conn.close()
        return rows

    @staticmethod
    def get_practice_stats(student_id: str = "pooja") -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), SUM(is_correct), SUM(score), SUM(max_score) FROM question_attempts WHERE student_id = ?;", (student_id,))
        row = cursor.fetchone()
        attempted = row[0] or 0
        correct = row[1] or 0
        score_earned = row[2] or 0.0
        max_possible = row[3] or 0.0

        accuracy_pct = round((correct / attempted * 100), 1) if attempted > 0 else 0
        avg_score_pct = round((score_earned / max_possible * 100), 1) if max_possible > 0 else 0

        # Streak
        cursor.execute("SELECT current_streak FROM stats WHERE id = 1;")
        streak_row = cursor.fetchone()
        streak = streak_row[0] if streak_row else 1

        # Revisions due count
        cursor.execute("SELECT COUNT(*) FROM revision_schedule WHERE student_id = ? AND is_completed = 0;", (student_id,))
        rev_count = cursor.fetchone()[0] or 0

        conn.close()

        weak_topics = PracticeRepository.get_weak_topics(student_id, limit=3)
        recent_attempts = PracticeRepository.get_recent_attempts(student_id, limit=5)

        return {
            "questions_attempted": attempted,
            "questions_correct": correct,
            "accuracy_pct": accuracy_pct,
            "average_score_pct": avg_score_pct,
            "practice_streak": streak,
            "revisions_due": rev_count,
            "weak_topics": weak_topics,
            "recent_attempts": recent_attempts
        }

    @staticmethod
    def create_exam_session(
        student_id: str,
        title: str,
        paper_id: str,
        total_questions: int,
        total_marks: int,
        time_limit_minutes: int,
        question_ids: List[str]
    ) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        session_id = f"exam_{uuid.uuid4().hex[:8]}"

        cursor.execute("""
        INSERT INTO exam_sessions (
            id, student_id, title, paper_id, total_questions, total_marks,
            time_limit_minutes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress');
        """, (session_id, student_id, title, paper_id, total_questions, total_marks, time_limit_minutes))

        for qid in question_ids:
            cursor.execute("""
            INSERT INTO exam_answers (id, session_id, question_id)
            VALUES (?, ?, ?);
            """, (f"ea_{uuid.uuid4().hex[:8]}", session_id, qid))

        conn.commit()
        conn.close()

        return {
            "session_id": session_id,
            "title": title,
            "paper_id": paper_id,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "time_limit_minutes": time_limit_minutes,
            "status": "in_progress"
        }

    @staticmethod
    def get_exam_session(session_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exam_sessions WHERE id = ?;", (session_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        sess = dict(row)

        cursor.execute("""
        SELECT ea.*, q.question_text, q.options, q.marks, q.question_type, q.difficulty,
               q.source, q.chapter_id, c.title as chapter_title
        FROM exam_answers ea
        JOIN questions q ON ea.question_id = q.id
        LEFT JOIN ca_chapters c ON q.chapter_id = c.id
        WHERE ea.session_id = ?;
        """, (session_id,))
        answers = [dict(a) for a in cursor.fetchall()]
        for a in answers:
            if a.get("options"):
                try:
                    a["options"] = json.loads(a["options"])
                except Exception:
                    a["options"] = []
            if a.get("feedback"):
                try:
                    a["feedback"] = json.loads(a["feedback"])
                except Exception:
                    pass

        sess["questions"] = answers
        for field in ["strong_areas", "weak_areas", "recommended_steps"]:
            if sess.get(field):
                try:
                    sess[field] = json.loads(sess[field])
                except Exception:
                    sess[field] = []
            else:
                sess[field] = []

        conn.close()
        return sess

    @staticmethod
    def complete_exam_session(
        session_id: str,
        score_obtained: float,
        accuracy_pct: float,
        time_spent_seconds: int,
        strong_areas: List[str],
        weak_areas: List[str],
        recommended_steps: List[str]
    ) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE exam_sessions
        SET score_obtained = ?,
            accuracy_pct = ?,
            time_spent_seconds = ?,
            status = 'completed',
            strong_areas = ?,
            weak_areas = ?,
            recommended_steps = ?,
            completed_at = CURRENT_TIMESTAMP
        WHERE id = ?;
        """, (
            score_obtained,
            accuracy_pct,
            time_spent_seconds,
            json.dumps(strong_areas),
            json.dumps(weak_areas),
            json.dumps(recommended_steps),
            session_id
        ))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def select_exam_questions(
        stage_id: Optional[str] = None,
        paper_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        count: int = 5,
        difficulty: Optional[str] = None,
        question_type: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Selects balanced exam questions honoring filters and avoiding repeated questions.
        """
        conn = get_connection()
        cursor = conn.cursor()

        exclude_list = exclude_ids or []
        params = []
        conditions = []

        if stage_id:
            conditions.append("(q.stage_id = ? OR p.stage_id = ?)")
            params.extend([stage_id, stage_id])
        if paper_id:
            conditions.append("q.paper_id = ?")
            params.append(paper_id)
        if chapter_id:
            conditions.append("q.chapter_id = ?")
            params.append(chapter_id)
        if difficulty:
            conditions.append("q.difficulty = ?")
            params.append(difficulty)
        if question_type:
            conditions.append("q.question_type = ?")
            params.append(question_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else "WHERE 1=1"

        # First try excluding already attempted / excluded questions
        if exclude_list:
            placeholders = ",".join("?" for _ in exclude_list)
            query_excluding = f"""
            SELECT q.*, c.title as chapter_title, p.name as paper_title
            FROM questions q
            LEFT JOIN ca_chapters c ON q.chapter_id = c.id
            LEFT JOIN ca_papers p ON q.paper_id = p.id
            {where_clause} AND q.id NOT IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT ?;
            """
            cursor.execute(query_excluding, params + exclude_list + [count])
            rows = cursor.fetchall()
            results = [dict(r) for r in rows]
        else:
            results = []

        # If not enough questions found, fill from pool without exclusion
        if len(results) < count:
            remaining = count - len(results)
            already_selected = [r["id"] for r in results]
            if already_selected:
                excl_placeholders = ",".join("?" for _ in already_selected)
                query_fallback = f"""
                SELECT q.*, c.title as chapter_title, p.name as paper_title
                FROM questions q
                LEFT JOIN ca_chapters c ON q.chapter_id = c.id
                LEFT JOIN ca_papers p ON q.paper_id = p.id
                {where_clause} AND q.id NOT IN ({excl_placeholders})
                ORDER BY RANDOM()
                LIMIT ?;
                """
                cursor.execute(query_fallback, params + already_selected + [remaining])
            else:
                query_fallback = f"""
                SELECT q.*, c.title as chapter_title, p.name as paper_title
                FROM questions q
                LEFT JOIN ca_chapters c ON q.chapter_id = c.id
                LEFT JOIN ca_papers p ON q.paper_id = p.id
                {where_clause}
                ORDER BY RANDOM()
                LIMIT ?;
                """
                cursor.execute(query_fallback, params + [remaining])

            results.extend([dict(r) for r in cursor.fetchall()])

        conn.close()

        # Parse options
        for q in results:
            if q.get("options"):
                try:
                    q["options"] = json.loads(q["options"])
                except Exception:
                    q["options"] = []
            else:
                q["options"] = []

        return results

    @staticmethod
    def get_corpus_stats() -> Dict[str, Any]:
        """
        Returns full statistics of official ICAI corpus vs Sathi AI generated corpus,
        including stage breakdowns, question types, and indexed document chunks.
        """
        conn = get_connection()
        cursor = conn.cursor()

        # Total questions
        cursor.execute("SELECT COUNT(*) FROM questions;")
        total_questions = cursor.fetchone()[0]

        # Official vs AI Generated
        cursor.execute("SELECT COUNT(*) FROM questions WHERE is_official = 1;")
        official_questions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM questions WHERE is_official = 0 OR source_type = 'SATHI_GENERATED';")
        ai_generated_questions = cursor.fetchone()[0]

        # By Stage
        cursor.execute("""
        SELECT COALESCE(q.stage_id, p.stage_id, 'Intermediate') as stage, COUNT(*)
        FROM questions q
        LEFT JOIN ca_papers p ON q.paper_id = p.id
        GROUP BY stage;
        """)
        stage_counts = {r[0]: r[1] for r in cursor.fetchall()}

        # By Question Type
        cursor.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type;")
        type_counts = {r[0]: r[1] for r in cursor.fetchall()}

        # By Source Type
        cursor.execute("SELECT source_type, COUNT(*) FROM questions GROUP BY source_type;")
        source_counts = {r[0]: r[1] for r in cursor.fetchall()}

        # By Difficulty
        cursor.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty;")
        difficulty_counts = {r[0]: r[1] for r in cursor.fetchall()}

        # Check knowledge chunks and documents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_chunks';")
        has_kchunks = cursor.fetchone() is not None

        total_knowledge_chunks = 0
        total_ingested_docs = 0
        if has_kchunks:
            cursor.execute("SELECT COUNT(*) FROM knowledge_chunks;")
            total_knowledge_chunks = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ingested_documents;")
            total_ingested_docs = cursor.fetchone()[0]

        conn.close()

        return {
            "total_questions": total_questions,
            "official_questions": official_questions,
            "ai_generated_questions": ai_generated_questions,
            "stage_breakdown": stage_counts,
            "type_breakdown": type_counts,
            "source_breakdown": source_counts,
            "difficulty_breakdown": difficulty_counts,
            "total_knowledge_chunks": total_knowledge_chunks,
            "total_ingested_documents": total_ingested_docs
        }

