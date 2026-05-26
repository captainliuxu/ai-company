"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/app.db")

# AI Companion — Gemini via api.xykjy.com proxy (OpenAI SDK compatible)
# 敏感值通过 .env 文件配置，参见 .env.example
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.xykjy.com")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# RAG
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.3

# Memory
MAX_MEMORIES_PER_SESSION = 200

# Summary
SUMMARY_TRIGGER_ROUNDS = 20

# Chat
MAX_CONTEXT_MESSAGES = 20
