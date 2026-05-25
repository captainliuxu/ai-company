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

    async def stream_generator():
        full_reply = ""
        messages = build_messages(persona_dict, session["messages"], body.message)

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

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
