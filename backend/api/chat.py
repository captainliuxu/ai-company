import asyncio
import json
import logging
import uuid
from datetime import datetime
from io import BytesIO

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import AI_API_KEY, AI_BASE_URL, AI_MODEL
from backend.database import async_session, get_db
from backend.models.persona import Persona
from backend.schemas.chat import (
    ChatRequest,
    SessionCreate,
    SessionResponse,
    VoiceSynthesisRequest,
)
from backend.services.persona_service import PersonaService
from backend.services.prompt_builder import build_messages
from backend.services.emotion_service import EmotionService
from backend.services.memory_service import MemoryService
from backend.services.summary_service import SummaryService
from backend.services.voice_service import VoiceServiceError, voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["personas"])


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


_MEMORY_TYPE_LABELS = {
    "fact": "用户事实",
    "profile": "用户事实",
    "preference": "用户偏好",
    "event": "近期事件",
    "summary": "对话摘要",
}


def _normalise_memory_hit(item: object) -> dict | None:
    memory = item.get("memory") if isinstance(item, dict) else item
    if memory is None:
        return None

    content = getattr(memory, "content", None)
    if not isinstance(content, str):
        return None

    cleaned_content = content.strip()
    if not cleaned_content:
        return None

    memory_type = getattr(memory, "type", None) or "memory"
    created_at = getattr(memory, "created_at", None)
    score_payload = item if isinstance(item, dict) else {}
    return {
        "id": getattr(memory, "id", 0) or 0,
        "content": cleaned_content,
        "type": memory_type,
        "type_label": _MEMORY_TYPE_LABELS.get(memory_type, memory_type),
        "created_at": created_at.isoformat() if created_at else "",
        "hybrid_score": float(score_payload.get("hybrid_score", 0.0) or 0.0),
        "semantic_score": float(score_payload.get("semantic_score", 0.0) or 0.0),
        "importance_score": float(score_payload.get("importance_score", 0.0) or 0.0),
        "recency_score": float(score_payload.get("recency_score", 0.0) or 0.0),
    }


def _build_memory_context(retrieved_memories: list[object]) -> str | None:
    normalised_hits = []
    for item in retrieved_memories:
        hit = _normalise_memory_hit(item)
        if hit is not None:
            normalised_hits.append(hit)

    if not normalised_hits:
        return None

    normalised_hits.sort(
        key=lambda hit: (
            hit["hybrid_score"],
            hit["semantic_score"],
            hit["importance_score"],
            hit["recency_score"],
            hit["created_at"],
            hit["id"],
        ),
        reverse=True,
    )

    seen_contents: set[str] = set()
    lines = []
    for hit in normalised_hits:
        dedupe_key = hit["content"].casefold()
        if dedupe_key in seen_contents:
            continue
        seen_contents.add(dedupe_key)
        lines.append(f"{len(lines) + 1}. [{hit['type_label']}] {hit['content']}")

    return "\n".join(lines) if lines else None


def _serialize_memory_item(item: object, include_scores: bool = False) -> dict | None:
    memory = item.get("memory") if isinstance(item, dict) else item
    if memory is None:
        return None

    payload = {
        "id": getattr(memory, "id", None),
        "session_id": getattr(memory, "session_id", None),
        "type": getattr(memory, "type", None),
        "content": getattr(memory, "content", None),
        "importance": getattr(memory, "importance", None),
        "created_at": getattr(memory, "created_at", None).isoformat()
        if getattr(memory, "created_at", None)
        else None,
    }

    if include_scores and isinstance(item, dict):
        payload["semantic_score"] = float(item.get("semantic_score", 0.0) or 0.0)
        payload["final_score"] = float(item.get("hybrid_score", 0.0) or 0.0)

    return payload


def _voice_error_response(message: str, status_code: int = 503) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": None},
    )


async def _parse_tts_payload(request: Request) -> VoiceSynthesisRequest | JSONResponse:
    content_type = request.headers.get("content-type", "").lower()

    try:
        if "application/json" in content_type:
            raw_payload = await request.json()
        elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            form = await request.form()
            raw_payload = dict(form)
        else:
            return _voice_error_response("Unsupported content type for text-to-speech", status_code=415)
    except json.JSONDecodeError:
        return _voice_error_response("Invalid JSON body", status_code=400)
    except Exception as exc:
        logger.warning("Failed to parse voice TTS payload: %s", exc)
        return _voice_error_response("Invalid text-to-speech request body", status_code=400)

    try:
        return VoiceSynthesisRequest.model_validate(raw_payload)
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
        message = first_error.get("msg", "Invalid request body")
        if field:
            message = f"{field}: {message}"
        return _voice_error_response(message, status_code=422)


@router.get("/personas")
async def list_personas(db: AsyncSession = Depends(get_db)):
    service = PersonaService(db)
    personas = await service.get_all()
    return {
        "success": True,
        "message": "",
        "data": {"personas": [p.model_dump() for p in personas]},
    }


@router.get("/voice/health")
async def get_voice_health():
    available = await voice_service.is_available()
    status_code = 200 if available else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "success": available,
            "message": "" if available else (voice_service.availability_error or "Voice provider is unavailable"),
            "data": {
                "enabled": voice_service.voice_enabled,
                "available": available,
                "stt_model": voice_service.stt_model,
                "tts_model": voice_service.tts_model,
                "tts_voice": voice_service.default_voice,
                "max_upload_mb": voice_service.max_upload_mb,
            },
        },
    )


@router.post("/voice/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    try:
        text = await voice_service.speech_to_text(audio_bytes, audio.content_type or "application/octet-stream")
    except VoiceServiceError as exc:
        logger.warning("Voice STT failed: %s", exc)
        return _voice_error_response(str(exc))
    except Exception as exc:
        logger.exception("Unexpected voice STT error: %s", exc)
        return _voice_error_response("Speech-to-text failed unexpectedly")

    return {
        "success": True,
        "message": "",
        "data": {"text": text},
    }


@router.post("/voice/tts")
async def text_to_speech(request: Request):
    payload = await _parse_tts_payload(request)
    if isinstance(payload, JSONResponse):
        return payload

    try:
        audio_bytes = await voice_service.text_to_speech(payload.text, payload.voice or "default")
    except VoiceServiceError as exc:
        logger.warning("Voice TTS failed: %s", exc)
        return _voice_error_response(str(exc))
    except Exception as exc:
        logger.exception("Unexpected voice TTS error: %s", exc)
        return _voice_error_response("Text-to-speech failed unexpectedly")

    headers = {
        "Content-Disposition": 'inline; filename="speech.mp3"',
        "Cache-Control": "no-cache",
    }
    return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mpeg", headers=headers)


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


def _serialize_session_message(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None

    role = item.get("role")
    content = item.get("content")
    if role not in {"user", "assistant"} or not isinstance(content, str):
        return None

    cleaned_content = content.strip()
    if not cleaned_content:
        return None

    return {
        "role": role,
        "content": cleaned_content,
    }


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


@router.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await _get_session(db, session_id)
    if session is None:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )

    messages = []
    for item in session["messages"]:
        serialized = _serialize_session_message(item)
        if serialized is not None:
            messages.append(serialized)

    return {
        "success": True,
        "message": "",
        "data": {
            "session_id": session["session_id"],
            "persona_id": session["persona_id"],
            "created_at": session["created_at"],
            "messages": messages,
        },
    }


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
        relevant_memories = await memory_service.search_memories(
            body.session_id,
            body.message,
            top_k=5,
            return_debug_scores=True,
        )
        memory_context = _build_memory_context(relevant_memories)
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
async def get_memories(
    session_id: str,
    type: str | None = None,
    query: str | None = None,
    top_k: int = Query(5, ge=1),
    include_scores: bool = False,
    db: AsyncSession = Depends(get_db),
):
    try:
        await _require_session(db, session_id)
    except HTTPException:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Session not found", "data": None},
        )
    service = MemoryService(db)
    if not query:
        if type:
            memories = await service.get_by_type(session_id, type)
        else:
            memories = await service.get_by_session(session_id)
        memory_items = memories
        include_scores = False
    else:
        search_top_k = top_k
        if type:
            session_memories = await service.get_by_session(session_id)
            search_top_k = max(top_k, len(session_memories))

        scored_memories = await service.search_memories(
            session_id,
            query,
            top_k=search_top_k,
            return_debug_scores=True,
        )
        if type:
            scored_memories = [
                item
                for item in scored_memories
                if getattr(item.get("memory"), "type", None) == type
            ]
        memory_items = scored_memories[:top_k]

    serialized_memories = []
    for item in memory_items:
        serialized = _serialize_memory_item(item, include_scores=include_scores)
        if serialized is not None:
            serialized_memories.append(serialized)

    return {
        "success": True,
        "message": "",
        "data": {
            "memories": serialized_memories
        },
    }
