import asyncio
import json
import logging
import uuid
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from backend.database import async_session, get_db
from backend.models.persona import Persona
from backend.schemas.chat import SessionCreate, SessionResponse, ChatRequest, ChatMessage
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


async def _create_session(
    db: AsyncSession,
    session_id: str,
    persona_id: str,
    created_at: str,
) -> None:
    await db.execute(
        text(
            """
            INSERT INTO chat_sessions (session_id, persona_id, messages_json, created_at)
            VALUES (:session_id, :persona_id, :messages_json, :created_at)
            """
        ),
        {
            "session_id": session_id,
            "persona_id": persona_id,
            "messages_json": "[]",
            "created_at": created_at,
        },
    )
    await db.commit()


async def _get_session(db: AsyncSession, session_id: str) -> dict | None:
    result = await db.execute(
        text(
            """
            SELECT session_id, persona_id, messages_json, created_at
            FROM chat_sessions
            WHERE session_id = :session_id
            """
        ),
        {"session_id": session_id},
    )
    row = result.mappings().first()
    if row is None:
        return None
    try:
        messages = json.loads(row["messages_json"])
    except json.JSONDecodeError:
        messages = []
    return {
        "session_id": row["session_id"],
        "persona_id": row["persona_id"],
        "messages": messages if isinstance(messages, list) else [],
        "created_at": row["created_at"],
    }


async def _require_session(db: AsyncSession, session_id: str) -> dict:
    session = await _get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def _save_session_messages(
    db: AsyncSession,
    session_id: str,
    messages: list[dict],
) -> None:
    await db.execute(
        text(
            """
            UPDATE chat_sessions
            SET messages_json = :messages_json
            WHERE session_id = :session_id
            """
        ),
        {
            "session_id": session_id,
            "messages_json": json.dumps(messages, ensure_ascii=False),
        },
    )
    await db.commit()


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
    created_at = datetime.now().isoformat()
    await _create_session(db, session_id, body.persona_id, created_at)

    resp = SessionResponse(
        session_id=session_id,
        persona_id=body.persona_id,
        created_at=created_at,
    )
    return {"success": True, "message": "", "data": resp.model_dump()}


@router.post("/chat/send")
async def send_message(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await _require_session(db, body.session_id)
    except HTTPException:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )

    if session["persona_id"] != body.persona_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Session persona mismatch", "data": None},
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
        async with async_session() as background_db:
            background_session = await _get_session(background_db, body.session_id)
            if background_session is None:
                logger.error("Post-process skipped because session %s no longer exists", body.session_id)
                return

            background_emotion_service = EmotionService(background_db)
            background_memory_service = MemoryService(background_db)

            try:
                await background_emotion_service.analyze_emotion(body.session_id, body.message, _full_reply)
            except Exception as exc:
                logger.error("Failed to analyse emotion: %s", exc)

            try:
                extracted = await background_memory_service.extract_from_conversation(body.message, _full_reply)
                for mem in extracted:
                    await background_memory_service.add_memory(
                        body.session_id,
                        mem["type"],
                        mem["content"],
                        mem.get("importance", 3),
                    )
            except Exception as exc:
                logger.error("Failed to extract or store memories: %s", exc)

            try:
                summary_service = SummaryService(background_db)
                if await summary_service.should_summarize(background_session["messages"]):
                    summary = await summary_service.generate_summary(background_session["messages"])
                    if summary:
                        updated_messages = summary_service.apply_summary(background_session["messages"], summary)
                        session["messages"] = updated_messages
                        await _save_session_messages(background_db, body.session_id, updated_messages)
                        await background_memory_service.add_memory(body.session_id, "summary", summary, 5)
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
            await _save_session_messages(db, body.session_id, session["messages"])
            asyncio.create_task(_post_process(full_reply))
        else:
            await _save_session_messages(db, body.session_id, session["messages"])

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
    try:
        await _require_session(db, session_id)
    except HTTPException:
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
    try:
        await _require_session(db, session_id)
    except HTTPException:
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
    try:
        await _require_session(db, session_id)
    except HTTPException:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )
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
