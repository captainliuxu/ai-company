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
MEMORY_SEARCH_TOP_K = 5
MEMORY_SEMANTIC_THRESHOLD = 0.18
MEMORY_RECENCY_HALFLIFE_DAYS = 14
MEMORY_WEIGHT_SEMANTIC = 0.55
MEMORY_WEIGHT_IMPORTANCE = 0.20
MEMORY_WEIGHT_RECENCY = 0.15
MEMORY_WEIGHT_TYPE = 0.10
MEMORY_TYPE_WEIGHT_USER_INFO = 1.00
MEMORY_TYPE_WEIGHT_PREFERENCE = 0.95
MEMORY_TYPE_WEIGHT_EVENT = 0.90
MEMORY_TYPE_WEIGHT_EMOTION = 0.80
MEMORY_TYPE_WEIGHT_SUMMARY = 0.60
MEMORY_MAX_SUMMARY_RESULTS = 1
MEMORY_MAX_EMOTION_RESULTS = 2

# Summary
SUMMARY_TRIGGER_ROUNDS = 20

# Chat
MAX_CONTEXT_MESSAGES = 20

# Voice
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() not in {"0", "false", "no", "off"}
VOICE_API_KEY = os.getenv("VOICE_API_KEY", AI_API_KEY)
VOICE_BASE_URL = os.getenv("VOICE_BASE_URL", "https://api.siliconflow.com")
VOICE_STT_MODEL = os.getenv("VOICE_STT_MODEL", "gpt-4o-mini-transcribe")
VOICE_TTS_MODEL = os.getenv("VOICE_TTS_MODEL", "gpt-4o-mini-tts")
VOICE_TTS_VOICE = os.getenv("VOICE_TTS_VOICE", "nova")
VOICE_MAX_UPLOAD_MB = int(os.getenv("VOICE_MAX_UPLOAD_MB", "10"))
