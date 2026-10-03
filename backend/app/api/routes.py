from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.core.ai_provider import get_ai_provider
from app.core.prompts import CA_COMPANION_SYSTEM_PROMPT, THOUGHT_REFRAMING_SYSTEM_PROMPT
from app.repositories.study_repository import StudyRepository

router = APIRouter(prefix="/api")

# --- Schemas ---

class MessageItem(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[MessageItem]] = None

class ChatResponse(BaseModel):
    reply: str
    model: str
    provider: str

class ReframeRequest(BaseModel):
    thought: str

class ReframeResponse(BaseModel):
    reframed: str
    model: str

class HealthResponse(BaseModel):
    status: str
    ai_provider: dict

class ChapterUpdateRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    subject_id: Optional[str] = None

# --- Endpoints ---

@router.get("/health", response_model=HealthResponse)
async def health_check():
    provider = get_ai_provider()
    health_info = await provider.check_health()
    status = "ok" if health_info.get("connected") else "degraded"
    return HealthResponse(
        status=status,
        ai_provider=health_info,
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    provider = get_ai_provider()

    # Build conversation history
    messages = []
    if request.history:
        for h in request.history:
            messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": request.message})

    try:
        reply = await provider.chat(messages=messages, system_prompt=CA_COMPANION_SYSTEM_PROMPT)
        return ChatResponse(
            reply=reply,
            model=getattr(provider, "model", "gemma2:2b"),
            provider=provider.__class__.__name__,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
