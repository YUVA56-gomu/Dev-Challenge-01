from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.ai_provider import get_ai_provider
from app.core.voice_provider import get_voice_provider
from app.core.prompts import (
    CA_COMPANION_SYSTEM_PROMPT,
    THOUGHT_REFRAMING_SYSTEM_PROMPT,
    build_grounded_system_prompt
)
from app.core.rag.vector_store import get_vector_store
from app.core.rag.query_router import route_query
from app.core.memory.memory_provider import get_memory_provider
from app.repositories.study_repository import StudyRepository
from app.repositories.practice_repository import PracticeRepository
from app.core.practice_evaluator import evaluate_student_answer, generate_grounded_practice_question

router = APIRouter(prefix="/api")

# --- Schemas ---

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[MessageItem]] = None
    study_context: Optional[Dict[str, Any]] = None  # Stage, Group, Paper, Chapter, Topic context

class CitationItem(BaseModel):
    source: str
    document_name: str
    paper: Optional[str] = ""
    chapter: Optional[str] = ""
    topic: Optional[str] = ""
    statutory_reference: Optional[str] = ""
    page_number: int = 1
    snippet: str
    source_type: Optional[str] = "ICAI_STUDY_MATERIAL"
    is_official: Optional[bool] = True
    provenance_label: Optional[str] = "🏛️ Official ICAI Source"

class ChatResponse(BaseModel):
    reply: str
    spoken_reply: Optional[str] = None
    model: str
    provider: str
    is_rag_grounded: bool = False
    citations: Optional[List[CitationItem]] = None
    routing: Optional[Dict[str, Any]] = None

class CAChapterUpdateRequest(BaseModel):
    status: Optional[str] = None
    confidence_score: Optional[int] = None
    notes: Optional[str] = None
    weak_areas: Optional[str] = None
    increment_revision: Optional[bool] = False

class CATopicUpdateRequest(BaseModel):
    status: Optional[str] = None
    confidence_score: Optional[int] = None
    notes: Optional[str] = None

class CustomChapterCreateRequest(BaseModel):
    paper_id: str
    title: str
    estimated_hours: Optional[int] = 6
    difficulty: Optional[str] = "Medium"
    learning_objective: Optional[str] = ""

class MemoryCreateRequest(BaseModel):
    student_id: Optional[str] = "pooja"
    memory_text: str
    memory_type: Optional[str] = "preference"

class PracticeSubmitRequest(BaseModel):
    question_id: str
    student_id: Optional[str] = "pooja"
    user_answer: str
    time_spent_seconds: Optional[int] = 0

class PracticeGenerateRequest(BaseModel):
    paper_id: str
    chapter_id: str
    topic_id: Optional[str] = None
    difficulty: Optional[str] = "Medium"
    question_type: Optional[str] = "Theory"

class ExamStartRequest(BaseModel):
    student_id: Optional[str] = "pooja"
    paper_id: Optional[str] = None
    stage_id: Optional[str] = None
    chapter_id: Optional[str] = None
    title: Optional[str] = None
    num_questions: Optional[int] = 5
    time_limit_minutes: Optional[int] = 30
    difficulty: Optional[str] = None
    question_type: Optional[str] = None
    exclude_ids: Optional[List[str]] = None

class ExamSubmitRequest(BaseModel):
    answers: Dict[str, str] # question_id -> user_answer
    time_spent_seconds: Optional[int] = 0

class KnowledgeIngestRequest(BaseModel):
    file_path: str
    document_title: Optional[str] = None
    source_type: Optional[str] = "ICAI_STUDY_MATERIAL"
    issuing_body: Optional[str] = "ICAI"
    stage: Optional[str] = "Intermediate"
    group_name: Optional[str] = "Group 1"
    paper: Optional[str] = "Taxation"
    module: Optional[str] = None
    chapter: Optional[str] = "General"
    document_version: Optional[str] = "2024"
    effective_date: Optional[str] = "May 2024 onwards"

class KnowledgeSearchRequest(BaseModel):
    query: str
    paper: Optional[str] = None
    chapter: Optional[str] = None
    source_type: Optional[str] = None
    top_k: Optional[int] = 5


class VoiceStatusResponse(BaseModel):
    provider: str
    available: bool
    voice_id: str
    cached_files: int
    fallback: str

class VoiceSynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

class ReframeRequest(BaseModel):
    thought: str

class ReframeResponse(BaseModel):
    reframed: str
    model: str

class ChapterUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    subject_id: Optional[str] = None


def clean_spoken_text(text: str) -> str:
    """
    Creates a concise, natural, voice-friendly spoken text from written CA explanations.
    Strips markdown formatting, bullet markers, table pipes, and keeps the first 2-3 impactful sentences.
    """
    if not text:
        return ""
    import re
    # Remove code blocks and tables
    cleaned = re.sub(r'```[\s\S]*?```', '', text)
    cleaned = re.sub(r'\|[^\n]+\|', '', cleaned)
    # Strip markdown symbols
    cleaned = re.sub(r'[#*_`~>-]', '', cleaned)
    cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)
    cleaned = cleaned.replace("₹", "Rupees ")
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    if not sentences:
        return cleaned[:250]

    # Accumulate first 2-3 sentences up to ~280 characters
    spoken_parts = []
    total_len = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if total_len + len(s) > 300 and spoken_parts:
            break
        spoken_parts.append(s)
        total_len += len(s)
        if len(spoken_parts) >= 3:
            break

    result = " ".join(spoken_parts).strip()
    return result if result else cleaned[:250]

@router.get("/health")
async def health_check():
    ai = get_ai_provider()
    voice = get_voice_provider()
    ai_status = await ai.check_health()
    return {
        "status": "ok",
        "ai_provider": {
            "provider": ai.__class__.__name__,
            "model_target": getattr(ai, "model", "gemma2:2b"),
            "connected": ai_status.get("connected", False),
            "model_available": ai_status.get("model_available", False),
            "details": ai_status,
        },
        "voice_provider": {
            "provider": voice.__class__.__name__,
            "available": voice.is_available(),
            "voice_id": getattr(voice, "default_voice_id", "21m00Tcm4TlvDq8ikWAM"),
        },
        "details": ai_status,
    }


@router.get("/voice/status", response_model=VoiceStatusResponse)
async def get_voice_status():

    voice_provider = get_voice_provider()
    stats = {}
    if hasattr(voice_provider, "get_cache_stats"):
        stats = voice_provider.get_cache_stats()
    
    return VoiceStatusResponse(
        provider=voice_provider.__class__.__name__,
        available=voice_provider.is_available(),
        voice_id=getattr(voice_provider, "default_voice_id", "21m00Tcm4TlvDq8ikWAM"),
        cached_files=stats.get("file_count", 0),
        fallback="Browser SpeechSynthesis (Web Speech API)",
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    provider = get_ai_provider()

    # 1. Intelligent Query Routing (Fast Path vs Deep Path)
    path, routing_info = route_query(request.message, active_context=request.study_context)

    # 2. Hybrid RAG Retrieval (when routed to Deep Path)
    retrieved_chunks = []
    citations = []

    if path == "deep":
        try:
            from app.knowledge.retriever import get_knowledge_retriever
            k_retriever = get_knowledge_retriever()
            # If explicit study context is present, enhance query
            search_query = request.message
            if request.study_context:
                ctx_hint = f"{request.study_context.get('paper', '')} {request.study_context.get('chapter', '')} {request.study_context.get('topic', '')} {request.study_context.get('statutory_section', '')}"
                search_query = f"{search_query} {ctx_hint}".strip()

            retrieved_chunks = k_retriever.hybrid_search(search_query, limit=2)
            
            for chunk in retrieved_chunks:
                snippet = chunk.get("content", "")[:200] + "..."
                citations.append(CitationItem(
                    source=chunk.get("source_type") or chunk.get("source", "ICAI Official Study Material"),
                    document_name=chunk.get("document_title") or chunk.get("document_name", "ICAI Study Material"),
                    paper=chunk.get("paper", ""),
                    chapter=chunk.get("chapter", ""),
                    topic=chunk.get("topic", ""),
                    statutory_reference=chunk.get("statutory_reference", ""),
                    page_number=chunk.get("page_number", 1),
                    snippet=snippet,
                    source_type=chunk.get("source_type", "ICAI_STUDY_MATERIAL"),
                    is_official=chunk.get("is_official", True),
                    provenance_label=chunk.get("provenance_label", "🏛️ Official ICAI Source")
                ))
        except Exception as e:
            print(f"[RAG] Warning: Knowledge retrieval notice ({e}), trying fallback.")
            try:
                vector_store = get_vector_store()
                retrieved_chunks = vector_store.hybrid_search(search_query, limit=2)
                for chunk in retrieved_chunks:
                    snippet = chunk.get("content", "")[:200] + "..."
                    citations.append(CitationItem(
                        source=chunk.get("source", "ICAI Official Study Material"),
                        document_name=chunk.get("document_name", "ICAI Study Material"),
                        paper=chunk.get("paper", ""),
                        chapter=chunk.get("chapter", ""),
                        topic=chunk.get("topic", ""),
                        statutory_reference=chunk.get("statutory_reference", ""),
                        page_number=chunk.get("page_number", 1),
                        snippet=snippet,
                    ))
            except Exception:
                pass

    # 3. Student Profile & Recommendations from SQLite
    try:
        student_profile = StudyRepository.get_student_study_recommendations("pooja")
    except Exception as e:
        student_profile = {}

    # 4. Build Grounded Prompt
    system_prompt = build_grounded_system_prompt(
        student_profile=student_profile,
        retrieved_chunks=retrieved_chunks,
        active_chapter_context=request.study_context
    )

    # 5. Build conversation history
    messages = []
    if request.history:
        for h in request.history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": request.message})

    try:
        reply = await provider.chat(messages=messages, system_prompt=system_prompt)
        spoken = clean_spoken_text(reply)
        return ChatResponse(
            reply=reply,
            spoken_reply=spoken,
            model=getattr(provider, "model", "gemma2:2b"),
            provider=provider.__class__.__name__,
            is_rag_grounded=len(citations) > 0,
            citations=citations if citations else None,
            routing={"path": path, **routing_info},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    provider = get_ai_provider()
    path, routing_info = route_query(request.message, active_context=request.study_context)
    retrieved_chunks = []
    citations = []

    if path == "deep":
        try:
            from app.knowledge.retriever import get_knowledge_retriever
            k_retriever = get_knowledge_retriever()
            search_query = request.message
            if request.study_context:
                ctx_hint = f"{request.study_context.get('paper', '')} {request.study_context.get('chapter', '')} {request.study_context.get('topic', '')} {request.study_context.get('statutory_section', '')}"
                search_query = f"{search_query} {ctx_hint}".strip()

            retrieved_chunks = k_retriever.hybrid_search(search_query, limit=2)
            
            for chunk in retrieved_chunks:
                snippet = chunk.get("content", "")[:200] + "..."
                citations.append(CitationItem(
                    source=chunk.get("source_type") or chunk.get("source", "ICAI Official Study Material"),
                    document_name=chunk.get("document_title") or chunk.get("document_name", "ICAI Study Material"),
                    paper=chunk.get("paper", ""),
                    chapter=chunk.get("chapter", ""),
                    topic=chunk.get("topic", ""),
                    statutory_reference=chunk.get("statutory_reference", ""),
                    page_number=chunk.get("page_number", 1),
                    snippet=snippet,
                    source_type=chunk.get("source_type", "ICAI_STUDY_MATERIAL"),
                    is_official=chunk.get("is_official", True),
                    provenance_label=chunk.get("provenance_label", "🏛️ Official ICAI Source")
                ))
        except Exception as e:
            try:
                vector_store = get_vector_store()
                retrieved_chunks = vector_store.hybrid_search(search_query, limit=2)
                for chunk in retrieved_chunks:
                    snippet = chunk.get("content", "")[:200] + "..."
                    citations.append(CitationItem(
                        source=chunk.get("source", "ICAI Official Study Material"),
                        document_name=chunk.get("document_name", "ICAI Study Material"),
                        paper=chunk.get("paper", ""),
                        chapter=chunk.get("chapter", ""),
                        topic=chunk.get("topic", ""),
                        statutory_reference=chunk.get("statutory_reference", ""),
                        page_number=chunk.get("page_number", 1),
                        snippet=snippet,
                    ))
            except Exception:
                pass

    try:
        student_profile = StudyRepository.get_student_study_recommendations("pooja")
    except Exception as e:
        student_profile = {}

    system_prompt = build_grounded_system_prompt(
        student_profile=student_profile,
        retrieved_chunks=retrieved_chunks,
        active_chapter_context=request.study_context
    )

    messages = []
    if request.history:
        for h in request.history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": request.message})

    async def event_stream():
        import json
        
        # 1. Send metadata first
        meta = {
            "type": "metadata",
            "model": getattr(provider, "model", "gemma2:2b"),
            "provider": provider.__class__.__name__,
            "is_rag_grounded": len(citations) > 0,
            "citations": [c.model_dump() for c in citations] if citations else None,
            "routing": {"path": path, **routing_info},
        }
        yield f"data: {json.dumps(meta)}\n\n"
        
        # 2. Stream the chunks
        full_reply = ""
        try:
            async for chunk in provider.chat_stream(messages=messages, system_prompt=system_prompt):
                full_reply += chunk
                chunk_data = {"type": "chunk", "content": chunk}
                yield f"data: {json.dumps(chunk_data)}\n\n"
        except Exception as e:
            err_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(err_data)}\n\n"
        
        # 3. Send final spoken text for ElevenLabs fallback if needed
        spoken = clean_spoken_text(full_reply)
        done_data = {"type": "done", "spoken_reply": spoken}
        yield f"data: {json.dumps(done_data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/voice/synthesize")
async def synthesize_voice(req: VoiceSynthesizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    voice_provider = get_voice_provider()
    if not voice_provider.is_available():
        return {
            "status": "fallback_to_browser",
            "message": "ElevenLabs is not configured; using browser speech synthesis.",
        }

    # Clean text to avoid reading markdown punctuation
    clean_text = clean_spoken_text(req.text)

    try:
        audio_bytes = await voice_provider.synthesize(text=clean_text, voice_id=req.voice_id)
        if not audio_bytes:
            return {
                "status": "fallback_to_browser",
                "message": "Empty audio generated; falling back to browser speech synthesis.",
            }
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        return {
            "status": "fallback_to_browser",
            "error": str(e),
            "message": "ElevenLabs call failed; falling back to browser speech synthesis.",
        }

@router.post("/wellness/reframe", response_model=ReframeResponse)
async def reframe_thought(request: ReframeRequest):
    if not request.thought.strip():
        raise HTTPException(status_code=400, detail="Thought cannot be empty.")

    provider = get_ai_provider()
    user_prompt = f"The student is experiencing this negative/anxious thought: \"{request.thought}\". Please provide an empathetic, constructive reframing following your guidelines."

    try:
        reframed_text = await provider.generate(
            prompt=user_prompt,
            system_prompt=THOUGHT_REFRAMING_SYSTEM_PROMPT
        )
        return ReframeResponse(
            reframed=reframed_text,
            model=getattr(provider, "model", "gemma2:2b"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Study & Progress Endpoints ---

@router.get("/study/subjects")
async def get_subjects():
    return StudyRepository.get_subjects_with_chapters()

@router.patch("/study/chapters/{chapter_id}")
async def update_chapter(chapter_id: str, req: ChapterUpdateRequest):
    success = StudyRepository.update_chapter(chapter_id, status=req.status, notes=req.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Chapter not found or no changes made.")
    return {"status": "success", "chapter_id": chapter_id}

@router.get("/study/tasks")
async def get_tasks():
    return StudyRepository.get_tasks()

@router.post("/study/tasks")
async def create_task(req: TaskCreateRequest):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty.")
    return StudyRepository.add_task(req.title, req.subject_id)

@router.patch("/study/tasks/{task_id}/toggle")
async def toggle_task(task_id: str):
    new_state = StudyRepository.toggle_task(task_id)
    if new_state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"status": "success", "task_id": task_id, "completed": new_state}

@router.delete("/study/tasks/{task_id}")
async def delete_task(task_id: str):
    success = StudyRepository.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"status": "success", "task_id": task_id}

@router.get("/study/progress")
async def get_progress():
    return StudyRepository.get_progress_summary()

# --- Phase 2: Scalable CA Syllabus Hierarchy Endpoints ---

@router.get("/study/stages")
async def get_stages():
    return StudyRepository.get_stages()

@router.get("/study/hierarchy")
async def get_hierarchy(stage_id: str = "stage_intermediate"):
    hierarchy = StudyRepository.get_hierarchy(stage_id)
    if not hierarchy:
        raise HTTPException(status_code=404, detail="Stage hierarchy not found.")
    return hierarchy

@router.patch("/study/ca-chapters/{chapter_id}")
async def update_ca_chapter(chapter_id: str, req: CAChapterUpdateRequest):
    success = StudyRepository.update_ca_chapter(
        chapter_id,
        status=req.status,
        confidence_score=req.confidence_score,
        notes=req.notes,
        weak_areas=req.weak_areas,
        increment_revision=bool(req.increment_revision)
    )
    if not success:
        raise HTTPException(status_code=404, detail="Chapter not found or no changes made.")
    return {"status": "success", "chapter_id": chapter_id}

@router.patch("/study/ca-topics/{topic_id}")
async def update_ca_topic(topic_id: str, req: CATopicUpdateRequest):
    success = StudyRepository.update_ca_topic(
        topic_id,
        status=req.status,
        confidence_score=req.confidence_score,
        notes=req.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found or no changes made.")
    return {"status": "success", "topic_id": topic_id}

@router.post("/study/custom-chapter")
async def create_custom_chapter(req: CustomChapterCreateRequest):
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Chapter title cannot be empty.")
    
    est_mins = (req.estimated_hours or 6) * 60
    created = StudyRepository.add_custom_chapter(
        paper_id=req.paper_id,
        title=req.title.strip(),
        estimated_minutes=est_mins,
        difficulty=req.difficulty or "Medium",
        learning_objective=req.learning_objective or ""
    )
    return {"status": "success", "chapter": created}

@router.get("/study/recommendations")
async def get_study_recommendations(student_id: str = "pooja"):
    return StudyRepository.get_student_study_recommendations(student_id)

# --- Phase 2: Semantic Memory Endpoints ---

@router.get("/memory/profile")
async def get_memory_profile(student_id: str = "pooja"):
    memory = get_memory_provider()
    memories = memory.retrieve_memory(student_id, limit=10)
    summary = memory.summarize_memory(student_id)
    return {
        "student_id": student_id,
        "summary": summary,
        "memories": memories,
        "provider": memory.__class__.__name__,
    }

@router.post("/memory")
async def add_memory(req: MemoryCreateRequest):
    if not req.memory_text.strip():
        raise HTTPException(status_code=400, detail="Memory text cannot be empty.")
    memory = get_memory_provider()
    mem_id = memory.save_memory(req.student_id or "pooja", req.memory_text, req.memory_type or "preference")
    return {"status": "success", "memory_id": mem_id}


# =========================================================================
# PHASE 3: EXAM PRACTICE & ANSWER EVALUATION ENGINE ENDPOINTS
# =========================================================================

@router.get("/practice/questions")
async def get_practice_questions(
    stage_id: Optional[str] = None,
    paper_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None,
    source_type: Optional[str] = None,
    is_official: Optional[bool] = None,
    limit: int = 20
):
    questions = PracticeRepository.get_questions(
        stage_id=stage_id,
        paper_id=paper_id,
        chapter_id=chapter_id,
        topic_id=topic_id,
        difficulty=difficulty,
        question_type=question_type,
        source_type=source_type,
        is_official=is_official,
        limit=limit
    )
    return questions


@router.get("/practice/questions/{question_id}")
async def get_question(question_id: str):
    q = PracticeRepository.get_question_by_id(question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")
    return q


@router.post("/practice/questions/generate")
async def generate_question(req: PracticeGenerateRequest):
    generated = await generate_grounded_practice_question(
        paper_id=req.paper_id,
        chapter_id=req.chapter_id,
        topic_id=req.topic_id,
        difficulty=req.difficulty or "Medium",
        question_type=req.question_type or "Theory"
    )
    # Save newly generated question into questions library
    qid = PracticeRepository.create_question(generated)
    generated["id"] = qid
    return generated


@router.post("/practice/submit")
async def submit_practice_answer(req: PracticeSubmitRequest):
    question = PracticeRepository.get_question_by_id(req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # 1. AI or deterministic answer evaluation
    eval_res = await evaluate_student_answer(
        question=question,
        user_answer=req.user_answer,
        time_spent_seconds=req.time_spent_seconds or 0
    )

    # 2. Record student attempt in SQLite
    is_correct = bool(eval_res.get("correct", False))
    score = float(eval_res.get("score", 0.0))
    max_score = float(eval_res.get("max_score", question.get("marks", 5)))

    attempt_id = PracticeRepository.save_attempt(
        student_id=req.student_id or "pooja",
        question_id=req.question_id,
        user_answer=req.user_answer,
        score=score,
        max_score=max_score,
        is_correct=is_correct,
        time_spent_seconds=req.time_spent_seconds or 0
    )

    # 3. Save evaluation details
    eval_id = PracticeRepository.save_evaluation(
        attempt_id=attempt_id,
        question_id=req.question_id,
        eval_data=eval_res
    )
    eval_res["evaluation_id"] = eval_id
    eval_res["attempt_id"] = attempt_id

    # 4. Update topic performance (detect weak areas)
    topic_id = question.get("topic_id") or question.get("chapter_id")
    PracticeRepository.update_topic_performance(
        student_id=req.student_id or "pooja",
        topic_id=topic_id,
        chapter_id=question.get("chapter_id"),
        paper_id=question.get("paper_id"),
        is_correct=is_correct,
        score=score,
        max_score=max_score,
        mistakes=eval_res.get("mistakes", [])
    )

    # 5. Spaced revision scheduling if answer was incorrect/needs revision
    revision_scheduled = False
    if not is_correct or score < max_score:
        PracticeRepository.schedule_spaced_revision(
            student_id=req.student_id or "pooja",
            topic_id=topic_id,
            chapter_id=question.get("chapter_id"),
            paper_id=question.get("paper_id")
        )
        revision_scheduled = True

    return {
        "status": "success",
        "attempt_id": attempt_id,
        "evaluation_id": eval_id,
        "score": score,
        "max_score": max_score,
        "is_correct": is_correct,
        "revision_scheduled": revision_scheduled,
        "evaluation": eval_res,
        "question": question
    }


@router.get("/practice/stats")
async def get_practice_statistics(student_id: str = "pooja"):
    return PracticeRepository.get_practice_stats(student_id)


@router.get("/practice/weak-areas")
async def get_weak_areas(student_id: str = "pooja", limit: int = 5):
    return PracticeRepository.get_weak_topics(student_id, limit=limit)


@router.get("/practice/revisions")
async def get_due_revisions(student_id: str = "pooja"):
    return PracticeRepository.get_due_revisions(student_id)


@router.post("/practice/revisions/{revision_id}/complete")
async def complete_revision(revision_id: str):
    success = PracticeRepository.complete_revision(revision_id)
    if not success:
        raise HTTPException(status_code=404, detail="Revision entry not found.")
    return {"status": "success", "revision_id": revision_id}


# --- Exam Mode Endpoints ---

@router.post("/practice/exam/start")
async def start_exam_session(req: ExamStartRequest):
    # Select balanced questions honoring filters and avoiding excluded/repeated questions
    selected_q = PracticeRepository.select_exam_questions(
        stage_id=req.stage_id,
        paper_id=req.paper_id,
        chapter_id=req.chapter_id,
        count=req.num_questions or 5,
        difficulty=req.difficulty,
        question_type=req.question_type,
        exclude_ids=req.exclude_ids or []
    )
    if not selected_q:
        raise HTTPException(status_code=400, detail="No questions available for the selected filters.")

    total_marks = sum(q.get("marks", 5) for q in selected_q)
    paper_title = req.paper_id.replace('paper_', '').title() if req.paper_id else (req.stage_id or "CA Practice")
    title = req.title or f"{paper_title} Timed Simulation"

    session = PracticeRepository.create_exam_session(
        student_id=req.student_id or "pooja",
        title=title,
        paper_id=req.paper_id or "paper_general",
        total_questions=len(selected_q),
        total_marks=total_marks,
        time_limit_minutes=req.time_limit_minutes or 30,
        question_ids=[q["id"] for q in selected_q]
    )
    session["questions"] = selected_q
    return session


@router.get("/practice/exam/{session_id}")
async def get_exam(session_id: str):
    session = PracticeRepository.get_exam_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found.")
    return session


@router.post("/practice/exam/{session_id}/submit")
async def submit_exam(session_id: str, req: ExamSubmitRequest):
    session = PracticeRepository.get_exam_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found.")

    total_score = 0.0
    total_max = session.get("total_marks", 0)
    correct_count = 0
    strong_areas = []
    weak_areas = []
    evaluated_questions = []

    for item in session.get("questions", []):
        qid = item["question_id"]
        user_ans = req.answers.get(qid, "")
        q_obj = PracticeRepository.get_question_by_id(qid)

        if not q_obj:
            continue

        eval_res = await evaluate_student_answer(q_obj, user_ans, 0)
        q_score = float(eval_res.get("score", 0.0))
        q_max = float(eval_res.get("max_score", q_obj.get("marks", 5)))
        total_score += q_score

        is_corr = bool(eval_res.get("correct", False))
        if is_corr:
            correct_count += 1
            if q_obj.get("chapter_id") not in strong_areas:
                strong_areas.append(q_obj.get("chapter_id"))
        else:
            if q_obj.get("chapter_id") not in weak_areas:
                weak_areas.append(q_obj.get("chapter_id"))

        # Save individual attempt
        PracticeRepository.save_attempt(
            student_id=session.get("student_id", "pooja"),
            question_id=qid,
            user_answer=user_ans,
            score=q_score,
            max_score=q_max,
            is_correct=is_corr,
            time_spent_seconds=0
        )

        evaluated_questions.append({
            "question_id": qid,
            "user_answer": user_ans,
            "score": q_score,
            "max_score": q_max,
            "is_correct": is_corr,
            "evaluation": eval_res
        })

    accuracy = round((correct_count / len(evaluated_questions) * 100), 1) if evaluated_questions else 0.0
    recommended_steps = [
        f"Revise key statutory provisions in: {', '.join(weak_areas[:3])}" if weak_areas else "Maintain regular revision cycles.",
        "Practice 5 high-yield scenario questions in low-confidence topics.",
        "Review ICAI suggested answers for optimal step-by-step presentation."
    ]

    PracticeRepository.complete_exam_session(
        session_id=session_id,
        score_obtained=total_score,
        accuracy_pct=accuracy,
        time_spent_seconds=req.time_spent_seconds or 0,
        strong_areas=strong_areas,
        weak_areas=weak_areas,
        recommended_steps=recommended_steps
    )

    return {
        "status": "completed",
        "session_id": session_id,
        "score_obtained": total_score,
        "total_marks": total_max,
        "accuracy_pct": accuracy,
        "time_spent_seconds": req.time_spent_seconds or 0,
        "strong_areas": strong_areas,
        "weak_areas": weak_areas,
        "recommended_steps": recommended_steps,
        "evaluated_questions": evaluated_questions
    }


# =========================================================================
# PHASE 4: DOCUMENT INGESTION & HYBRID RETRIEVAL ENDPOINTS
# =========================================================================

@router.get("/practice/corpus/stats")
async def get_practice_corpus_stats():
    """Returns official vs AI question counts, stages, and indexed knowledge."""
    return PracticeRepository.get_corpus_stats()


@router.post("/knowledge/ingest")
async def ingest_document(req: KnowledgeIngestRequest):
    """
    Production-grade document ingestion pipeline:
    Parses PDF/TXT/MD, extracts pages & sections, creates semantic chunks,
    hashes for deduplication, and indexes into FTS5 + sqlite-vec.
    """
    from app.knowledge.ingestion import get_ingestion_engine
    import os
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"File not found on server: {req.file_path}")

    engine = get_ingestion_engine()
    res = engine.ingest_file(
        file_path=req.file_path,
        document_title=req.document_title,
        source_type=req.source_type or "ICAI_STUDY_MATERIAL",
        issuing_body=req.issuing_body or "ICAI",
        stage=req.stage or "Intermediate",
        group_name=req.group_name or "Group 1",
        paper=req.paper or "Taxation",
        module=req.module,
        chapter=req.chapter or "General",
        document_version=req.document_version or "2024",
        effective_date=req.effective_date or "May 2024 onwards"
    )
    return res


@router.get("/knowledge/documents")
async def list_ingested_documents():
    """Lists all ingested documents with metadata and chunk counts."""
    from app.knowledge.document_store import KnowledgeDocumentStore
    store = KnowledgeDocumentStore()
    return store.list_documents()


@router.get("/knowledge/stats")
async def get_knowledge_corpus_stats():
    """Returns knowledge store statistics (documents, chunks, covered papers)."""
    from app.knowledge.document_store import KnowledgeDocumentStore
    store = KnowledgeDocumentStore()
    return store.get_corpus_stats()


@router.post("/knowledge/search")
async def search_knowledge(req: KnowledgeSearchRequest):
    """
    Hybrid RAG retrieval (BM25 + Dense vector similarity + RRF fusion)
    with statutory query boosting and explicit provenance tagging.
    """
    from app.knowledge.retriever import get_knowledge_retriever
    retriever = get_knowledge_retriever()
    results = retriever.hybrid_search(query=req.query, limit=req.top_k or 5)
    return {
        "query": req.query,
        "count": len(results),
        "results": results
    }





# =========================================================================
# SANCTUARY: Reflections, Mood Check-ins, Focus Sessions
# =========================================================================

class SanctuaryReflectionRequest(BaseModel):
    student_id: Optional[str] = "pooja"
    reflection_text: str

class SanctuaryCheckinRequest(BaseModel):
    student_id: Optional[str] = "pooja"
    mood: str  # "focused" | "okay" | "tired" | "overwhelmed" | "break"

class SanctuaryFocusSessionRequest(BaseModel):
    student_id: Optional[str] = "pooja"
    duration_minutes: int
    completed: Optional[bool] = False


@router.post("/sanctuary/reflections")
async def save_reflection(req: SanctuaryReflectionRequest):
    import uuid
    if not req.reflection_text.strip():
        raise HTTPException(status_code=400, detail="Reflection text cannot be empty.")
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    rid = f"ref_{uuid.uuid4().hex[:8]}"
    cursor.execute(
        "INSERT INTO sanctuary_reflections (id, student_id, reflection_text) VALUES (?, ?, ?);",
        (rid, req.student_id or "pooja", req.reflection_text.strip())
    )
    conn.commit()
    conn.close()
    return {"status": "saved", "id": rid}


@router.get("/sanctuary/reflections")
async def get_reflections(student_id: str = "pooja", limit: int = 10):
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, reflection_text, created_at FROM sanctuary_reflections WHERE student_id = ? ORDER BY created_at DESC LIMIT ?;",
        (student_id, limit)
    )
    rows = [{"id": r["id"], "text": r["reflection_text"], "created_at": r["created_at"]} for r in cursor.fetchall()]
    conn.close()
    return rows


@router.post("/sanctuary/checkin")
async def save_checkin(req: SanctuaryCheckinRequest):
    import uuid
    valid_moods = {"focused", "okay", "tired", "overwhelmed", "break"}
    if req.mood not in valid_moods:
        raise HTTPException(status_code=400, detail=f"Invalid mood. Must be one of: {', '.join(valid_moods)}")
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cid = f"ci_{uuid.uuid4().hex[:8]}"
    cursor.execute(
        "INSERT INTO sanctuary_checkins (id, student_id, mood) VALUES (?, ?, ?);",
        (cid, req.student_id or "pooja", req.mood)
    )
    conn.commit()
    conn.close()
    return {"status": "saved", "id": cid, "mood": req.mood}


@router.get("/sanctuary/checkin/latest")
async def get_latest_checkin(student_id: str = "pooja"):
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mood, created_at FROM sanctuary_checkins WHERE student_id = ? ORDER BY created_at DESC LIMIT 1;",
        (student_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"mood": None, "created_at": None}
    return {"mood": row["mood"], "created_at": row["created_at"]}


@router.post("/sanctuary/focus-session")
async def save_focus_session(req: SanctuaryFocusSessionRequest):
    import uuid
    if req.duration_minutes < 1:
        raise HTTPException(status_code=400, detail="Duration must be at least 1 minute.")
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    sid = f"fs_{uuid.uuid4().hex[:8]}"
    cursor.execute(
        "INSERT INTO sanctuary_focus_sessions (id, student_id, duration_minutes, completed) VALUES (?, ?, ?, ?);",
        (sid, req.student_id or "pooja", req.duration_minutes, 1 if req.completed else 0)
    )
    # Update total_focus_minutes in stats
    if req.completed:
        cursor.execute(
            "UPDATE stats SET total_focus_minutes = total_focus_minutes + ?, last_active_date = DATE('now') WHERE id = 1;",
            (req.duration_minutes,)
        )
    conn.commit()
    conn.close()
    return {"status": "saved", "id": sid}


@router.get("/sanctuary/focus-sessions")
async def get_focus_sessions(student_id: str = "pooja", limit: int = 20):
    from app.db.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, duration_minutes, completed, created_at FROM sanctuary_focus_sessions WHERE student_id = ? ORDER BY created_at DESC LIMIT ?;",
        (student_id, limit)
    )
    rows = [
        {
            "id": r["id"],
            "duration_minutes": r["duration_minutes"],
            "completed": bool(r["completed"]),
            "created_at": r["created_at"]
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return rows


# =========================================================================
# SETTINGS: ElevenLabs key configuration (runtime hot-update)
# =========================================================================

class ElevenLabsConfigRequest(BaseModel):
    api_key: str
    voice_id: Optional[str] = None

@router.post("/settings/elevenlabs")
async def configure_elevenlabs(req: ElevenLabsConfigRequest):
    """
    Hot-updates the ElevenLabs API key at runtime.
    Also writes it to the .env file for persistence across restarts.
    """
    import re
    from app.core.config import settings
    from app.core import voice_provider as vp

    api_key = req.api_key.strip()
    voice_id = (req.voice_id or "").strip() or settings.ELEVENLABS_VOICE_ID

    # Update settings in memory
    settings.ELEVENLABS_API_KEY = api_key
    if voice_id:
        settings.ELEVENLABS_VOICE_ID = voice_id

    # Reset the singleton so next call picks up the new key
    vp._voice_provider_instance = None

    # Persist to .env file
    import os
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
    )
    try:
        if os.path.exists(env_path):
            content = open(env_path).read()
        else:
            content = "OLLAMA_BASE_URL=http://localhost:11434\nOLLAMA_MODEL=gemma2:2b\n"

        # Replace or insert ELEVENLABS_API_KEY
        if re.search(r'^ELEVENLABS_API_KEY=', content, re.MULTILINE):
            content = re.sub(
                r'^ELEVENLABS_API_KEY=.*$', f'ELEVENLABS_API_KEY={api_key}',
                content, flags=re.MULTILINE
            )
        else:
            content += f'\nELEVENLABS_API_KEY={api_key}\n'

        if re.search(r'^ELEVENLABS_VOICE_ID=', content, re.MULTILINE):
            content = re.sub(
                r'^ELEVENLABS_VOICE_ID=.*$', f'ELEVENLABS_VOICE_ID={voice_id}',
                content, flags=re.MULTILINE
            )
        else:
            content += f'ELEVENLABS_VOICE_ID={voice_id}\n'

        with open(env_path, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"Warning: could not persist .env: {e}")

    return {
        "status": "updated",
        "elevenlabs_active": bool(api_key),
        "voice_id": voice_id
    }

@router.get("/settings/voice-status")
async def get_voice_config_status():
    """Returns current voice provider status for the Settings page."""
    from app.core.config import settings
    provider = get_voice_provider()
    return {
        "elevenlabs_configured": provider.is_available(),
        "voice_id": getattr(provider, 'default_voice_id', settings.ELEVENLABS_VOICE_ID),
        "provider": provider.__class__.__name__,
        "cache_stats": provider.get_cache_stats() if hasattr(provider, 'get_cache_stats') else {}
    }
