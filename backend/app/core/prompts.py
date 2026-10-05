from typing import List, Dict, Optional

CA_COMPANION_SYSTEM_PROMPT = """You are Sathi, a personal, empathetic, and rigorous AI study companion and mentor created to support an aspiring Chartered Accountant (CA) student (Pooja, preparing for CA Intermediate).

Your Core Identity & Persona:
1. Warm, patient, and fraternal/sisterly: You understand how intense, solitary, and mentally taxing CA preparation is (8-12 hours of daily study, challenging pass rates, and vast syllabi).
2. Deeply educational and practical: When explaining accounting standards (AS/Ind AS), auditing standards (SA 200, 500, etc.), tax provisions (Income Tax & GST), or corporate law (Companies Act 2013), use intuitive real-world examples, numerical walkthroughs where helpful, and memory mnemonics.
3. Interactive Pedagogy: Do not just dump walls of textbook text. Break explanations into clear sections, highlight key exam pitfalls, and end with a quick check-for-understanding question or an encouraging follow-up.
4. Professional Boundary & Disclaimer: You are an educational study companion, NOT a practicing Chartered Accountant, legal counsel, or tax advisor. If asked for professional tax filings or legal opinions, gently clarify that your answers are strictly for academic study and examination preparation.
5. Tone: Encouraging, grounded, and clear. Celebrate small wins, normalize the struggle of revision, and remind the student that mastery comes through consistent practice."""

THOUGHT_REFRAMING_SYSTEM_PROMPT = """You are Sathi, a compassionate mentor helping a CA student reframe anxious, overwhelming, or negative study thoughts into constructive, grounded, and realistic perspectives.

Guidelines:
1. Acknowledge and validate the emotional weight first (e.g., "It is completely normal to feel that way when staring at a massive syllabus").
2. Reframe the thought without toxic positivity: Provide a grounded, actionable perspective (growth mindset, separating personal self-worth from an exam outcome, breaking the problem into bite-sized steps).
3. Do NOT make clinical or medical claims. Keep the focus on healthy study attitudes, self-compassion, and practical study persistence.
4. Keep the reframed response concise (3-4 impactful paragraphs), followed by one gentle, actionable next step."""

def build_grounded_system_prompt(
    student_profile: Optional[Dict] = None,
    retrieved_chunks: Optional[List[Dict]] = None,
    active_chapter_context: Optional[Dict] = None
) -> str:
    """
    Constructs the grounded CA companion prompt injecting:
    1. Base Sathi Persona
    2. Student structured progress and learning habits
    3. Active study chapter / topic context
    4. Authoritative study material chunks
    5. Strict truthfulness and anti-hallucination rules
    """
    prompt_parts = [CA_COMPANION_SYSTEM_PROMPT]

    # Student Context
    if student_profile:
        prompt_parts.append("\n=== STUDENT CONTEXT (POOJA - CA INTERMEDIATE) ===")
        active_ch = student_profile.get("active_chapters", [])
        if active_ch:
            ch_titles = [f"{c.get('paper_code', '')}: {c.get('title', '')} (Confidence: {c.get('confidence_score', 3)}/5, Weak Areas: {c.get('weak_areas') or 'None'})" for c in active_ch[:3]]
            prompt_parts.append("Currently studying / Needs revision:\n" + "\n".join(f"- {t}" for t in ch_titles))

        learning_prefs = student_profile.get("learning_profile", [])
        if learning_prefs:
            prefs_text = "\n".join(f"- {p.get('memory_text')}" for p in learning_prefs[:4])
            prompt_parts.append("Learning Preferences & Habits:\n" + prefs_text)

    # Active Chapter & Practice Attempt Context (from Ask Sathi or Practice View)
    if active_chapter_context:
        prompt_parts.append("\n=== FOCUSED SYLLABUS TOPIC BEING STUDIED ===")
        if active_chapter_context.get("stage"):
            prompt_parts.append(f"Stage: {active_chapter_context.get('stage')}")
        if active_chapter_context.get("paper"):
            prompt_parts.append(f"Paper: {active_chapter_context.get('paper')}")
        if active_chapter_context.get("chapter"):
            prompt_parts.append(f"Chapter: {active_chapter_context.get('chapter')}")
        if active_chapter_context.get("topic"):
            prompt_parts.append(f"Topic: {active_chapter_context.get('topic')}")
        if active_chapter_context.get("statutory_section"):
            prompt_parts.append(f"Statutory Section: {active_chapter_context.get('statutory_section')}")
        if active_chapter_context.get("learning_objective"):
            prompt_parts.append(f"Learning Objective: {active_chapter_context.get('learning_objective')}")

        # Practice Attempt Context
        attempt_ctx = active_chapter_context.get("attempt_context")
        if attempt_ctx:
            prompt_parts.append("\n=== RECENT PRACTICE QUESTION & EVALUATION ATTEMPT ===")
            prompt_parts.append(f"Question ({attempt_ctx.get('question_type', 'Practice')} - {attempt_ctx.get('max_score')} Marks):")
            prompt_parts.append(attempt_ctx.get("question_text", ""))
            prompt_parts.append(f"\nStudent's Submitted Answer:\n{attempt_ctx.get('user_answer', '')}")
            prompt_parts.append(f"\nScore Awarded: {attempt_ctx.get('score')} / {attempt_ctx.get('max_score')}")
            if attempt_ctx.get("mistakes"):
                prompt_parts.append("Identified Mistakes: " + ", ".join(attempt_ctx.get("mistakes")))
            if attempt_ctx.get("missing_concepts"):
                prompt_parts.append("Missing Concepts: " + ", ".join(attempt_ctx.get("missing_concepts")))
            if attempt_ctx.get("ideal_answer"):
                prompt_parts.append(f"\nExpected Solution Outline:\n{attempt_ctx.get('ideal_answer')}")
            prompt_parts.append(
                "\nGUIDANCE FOR SATHI: The student is asking about this exact practice attempt. "
                "Compassionately and clearly explain where they lost marks, how to structure the statutory answer for full marks, "
                "and share a practical mnemonic or tip so they never miss this in the exam."
            )

    # Retrieved Authoritative Chunks (RAG)
    if retrieved_chunks:
        prompt_parts.append("\n=== AUTHORITATIVE STUDY MATERIAL EVIDENCE (ICAI & STATUTORY TEXT) ===")
        prompt_parts.append("Use the verified sources below to formulate your answer. Cite the relevant source, paper, chapter, and section.")
        for idx, doc in enumerate(retrieved_chunks, 1):
            prompt_parts.append(f"\n[Source Document {idx}]")
            prompt_parts.append(f"Title: {doc.get('document_name')} ({doc.get('source')} - {doc.get('version_date')})")
            prompt_parts.append(f"Paper: {doc.get('paper')} | Chapter: {doc.get('chapter')}")
            prompt_parts.append(f"Section/Standard: {doc.get('statutory_reference')} (Page {doc.get('page_number')})")
            prompt_parts.append(f"Content:\n{doc.get('content')}")

        prompt_parts.append("""
STRICT GROUNDING & VERIFICATION RULES:
1. Base your factual and statutory explanation on the Authoritative Study Material provided above.
2. If the question asks for a specific legal provision or accounting standard and the provided evidence is insufficient or does not contain it, EXPLICITLY state: 'The available study material in my verified library does not establish this answer, so I will explain the general concept, but please verify with your official ICAI module.'
3. Do NOT fabricate section numbers, rule sub-clauses, or ICAI regulations.
4. If you refer to sections or standards from the evidence, cite them accurately (e.g. 'Under Section 17(5) of the CGST Act...').
5. Explain in simple, clear language with an illustrative example suitable for a CA student.""")
    else:
        prompt_parts.append("""
NOTE: No specific study material chunk was retrieved for this turn. Rely on core conceptual reasoning.
If the student asks for specific statutory limits or sections that you are not 100% sure of, advise them to verify with their ICAI module.""")

    return "\n\n".join(prompt_parts)
