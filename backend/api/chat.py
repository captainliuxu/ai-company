import asyncio
import json
import logging
import uuid

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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["personas"])


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


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

    emotion_service = None
    emotion_state = None
    try:
        emotion_service = EmotionService(db)
        current_emotion = await emotion_service.get_current_state(body.session_id)
        if current_emotion:
            emotion_state = {
                "favorability": current_emotion.favorability,
                "trust": current_emotion.trust,
                "mood": current_emotion.mood,
                "dependency": current_emotion.dependency,
            }
    except Exception as exc:
        logger.error("Failed to initialise EmotionService: %s", exc)

    memory_service = None
    memory_context = None
    try:
        memory_service = MemoryService(db)
        relevant_memories = await memory_service.search_memories(body.session_id, body.message, top_k=5)
        if relevant_memories:
            lines = []
            for i, mem in enumerate(relevant_memories, 1):
                lines.append(f"{i}. {mem.content}")
            memory_context = "\n".join(lines)
    except Exception as exc:
        logger.error("Failed to initialise MemoryService or search memories: %s", exc)

    # Post-processing task: runs after SSE stream closes, never blocks the response.
    async def _post_process(_full_reply: str):
        try:
            if emotion_service is not None:
                await emotion_service.analyze_emotion(body.session_id, body.message, _full_reply)
        except Exception as exc:
            logger.error("Failed to analyse emotion: %s", exc)

        try:
            if memory_service is not None:
                extracted = await memory_service.extract_from_conversation(body.message, _full_reply)
                for mem in extracted:
                    await memory_service.add_memory(
                        body.session_id,
                        mem["type"],
                        mem["content"],
                        mem.get("importance", 3),
                    )
        except Exception as exc:
            logger.error("Failed to extract or store memories: %s", exc)

        try:
            summary_service = SummaryService(db)
            if await summary_service.should_summarize(session["messages"]):
                summary = await summary_service.generate_summary(session["messages"])
                if summary:
                    session["messages"] = summary_service.apply_summary(session["messages"], summary)
                    if memory_service is not None:
                        await memory_service.add_memory(body.session_id, "summary", summary, 5)
        except Exception as exc:
            logger.error("Failed to run summary: %s", exc)

    async def stream_generator():
        full_reply = ""
        messages = build_messages(persona_dict, session["messages"], body.message, emotion_state, memory_context)
        try:
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
                    if response.status_code >= 400:
                        try:
                            error_body = await response.aread()
                            error_text = error_body.decode("utf-8", errors="replace")[:500]
                        except Exception:
                            error_text = "(unable to read error body)"
                        logger.error(
                            "AI API returned HTTP %d: %s",
                            response.status_code,
                            error_text,
                        )
                        yield _sse_event({"error": f"AI API error ({response.status_code})", "done": True})
                        return

                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        data_str = line[6:].strip()
                        if not data_str:
                            continue
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            logger.warning("Skipping malformed AI SSE payload: %s", data_str[:200])
                            continue

                        choices = data.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta") or {}
                        content = delta.get("content")
                        if isinstance(content, str) and content:
                            full_reply += content
                            yield _sse_event({"text": content})
        except httpx.HTTPError as exc:
            logger.exception("AI stream request failed: %s", exc)
            yield _sse_event({"error": "AI stream interrupted", "done": True})
            return
        except Exception as exc:
            logger.exception("Unexpected chat streaming error: %s", exc)
            yield _sse_event({"error": "聊天流中断，请重试", "done": True})
            return

        session["messages"].append({"role": "user", "content": body.message})
        if full_reply:
            session["messages"].append({"role": "assistant", "content": full_reply})
            asyncio.create_task(_post_process(full_reply))

        yield _sse_event({"done": True})

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
