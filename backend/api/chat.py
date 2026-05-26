import uuid
import json

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from backend.database import get_db
from backend.models.persona import Persona
from backend.schemas.chat import SessionCreate, SessionResponse, ChatRequest, ChatMessage
from datetime import datetime
from backend.services.persona_service import PersonaService
from backend.services.prompt_builder import build_messages
from backend.services.emotion_service import EmotionService
from backend.services.memory_service import MemoryService
from backend.services.summary_service import SummaryService

router = APIRouter(prefix="/api/v1", tags=["personas"])


@router.get("/personas")
async def list_personas(db: AsyncSession = Depends(get_db)):
    service = PersonaService(db)
    personas = await service.get_all()
    return {
        "success": True,
        "message": "",
        "data": {"personas": [p.model_dump() for p in personas]},
    }


@router.get("/personas/{persona_id}")
async def get_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    service = PersonaService(db)
    persona = await service.get_by_id(persona_id)
    if persona is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Persona not found", "data": None}
        )
    return {
        "success": True,
        "message": "",
        "data": persona.model_dump(),
    }


# In-memory session store (will be migrated to SQLite in Phase 4)
_sessions: dict[str, dict] = {}


@router.post("/chat/session")
async def create_chat_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    service = PersonaService(db)
    persona = await service.get_by_id(body.persona_id)
    if persona is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Persona not found", "data": None},
        )

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "persona_id": body.persona_id,
        "messages": [],
    }

    resp = SessionResponse(
        session_id=session_id,
        persona_id=body.persona_id,
        created_at=datetime.now().isoformat(),
    )
    return {"success": True, "message": "", "data": resp.model_dump()}


@router.post("/chat/send")
async def send_message(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    session = _sessions.get(body.session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )

    service = PersonaService(db)
    persona = await service.get_by_id(body.persona_id)
    if persona is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Persona not found", "data": None},
        )

    persona_dict = persona.model_dump()

    # Get current emotion state for prompt enhancement
    emotion_service = EmotionService(db)
    current_emotion = await emotion_service.get_current_state(body.session_id)
    emotion_state = None
    if current_emotion:
        emotion_state = {
            "favorability": current_emotion.favorability,
            "trust": current_emotion.trust,
            "mood": current_emotion.mood,
            "dependency": current_emotion.dependency,
        }

    # Search relevant memories via RAG
    memory_service = MemoryService(db)
    relevant_memories = await memory_service.search_memories(body.session_id, body.message, top_k=5)
    memory_context = None
    if relevant_memories:
        lines = []
        for i, mem in enumerate(relevant_memories, 1):
            lines.append(f"{i}. {mem.content}")
        memory_context = "\n".join(lines)

    async def stream_generator():
        full_reply = ""
        messages = build_messages(persona_dict, session["messages"], body.message, emotion_state, memory_context)

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            async with client.stream(
                "POST",
                f"{AI_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "content-type": "application/json",
                },
                json={
                    "model": AI_MODEL,
                    "max_tokens": 1024,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'text': content})}\n\n"
                                    full_reply += content
                        except json.JSONDecodeError:
                            pass

        yield f"data: {json.dumps({'text': '', 'done': True})}\n\n"

        session["messages"].append({"role": "user", "content": body.message})
        session["messages"].append({"role": "assistant", "content": full_reply})

        # Record emotion state after this exchange
        await emotion_service.analyze_emotion(body.session_id, body.message, full_reply)

        # Extract and store long-term memories
        extracted = await memory_service.extract_from_conversation(body.message, full_reply)
        for mem in extracted:
            await memory_service.add_memory(
                body.session_id,
                mem["type"],
                mem["content"],
                mem.get("importance", 3),
            )

        # Check if conversation needs summarization
        summary_service = SummaryService(db)
        if await summary_service.should_summarize(session["messages"]):
            summary = await summary_service.generate_summary(session["messages"])
            if summary:
                session["messages"] = summary_service.apply_summary(session["messages"], summary)
                await memory_service.add_memory(body.session_id, "summary", summary, 5)

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/emotion/{session_id}")
async def get_emotion_state(session_id: str, db: AsyncSession = Depends(get_db)):
    if session_id not in _sessions:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )
    service = EmotionService(db)
    state = await service.get_current_state(session_id)
    if state is None:
        return {"success": True, "message": "No emotion data yet", "data": None}
    return {
        "success": True,
        "message": "",
        "data": {
            "session_id": state.session_id,
            "favorability": state.favorability,
            "trust": state.trust,
            "mood": state.mood,
            "dependency": state.dependency,
            "created_at": state.created_at.isoformat() if state.created_at else None,
        },
    }


@router.get("/emotion/{session_id}/history")
async def get_emotion_history(session_id: str, db: AsyncSession = Depends(get_db)):
    if session_id not in _sessions:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )
    service = EmotionService(db)
    history = await service.get_history(session_id)
    return {
        "success": True,
        "message": "",
        "data": {
            "history": [
                {
                    "session_id": e.session_id,
                    "favorability": e.favorability,
                    "trust": e.trust,
                    "mood": e.mood,
                    "dependency": e.dependency,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in history
            ]
        },
    }


@router.get("/memories/{session_id}")
async def get_memories(session_id: str, type: str | None = None, db: AsyncSession = Depends(get_db)):
    service = MemoryService(db)
    if type:
        memories = await service.get_by_type(session_id, type)
    else:
        memories = await service.get_by_session(session_id)
    return {
        "success": True,
        "message": "",
        "data": {
            "memories": [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "type": m.type,
                    "content": m.content,
                    "importance": m.importance,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in memories
            ]
        },
    }
