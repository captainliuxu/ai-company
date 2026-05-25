"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as persona_router
from backend.database import async_session, engine, init_db
from backend.services.persona_service import PersonaService


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    await init_db()
    async with async_session() as session:
        service = PersonaService(session)
        created = await service.seed_default_personas()
        if created > 0:
            print(f"Seeded {created} default personas")
    yield
    await engine.dispose()


app = FastAPI(title="AI Companion Pro Demo", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(persona_router)


@app.get("/")
async def root():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
