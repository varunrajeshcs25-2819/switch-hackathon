"""
PatchPilot Backend Configuration

Environment variables:
- GEMINI_API_KEY: Google AI Studio key used by all three agents (free tier works)
- GEMINI_MODEL: Optional model override (default: gemini-2.0-flash)
- ANTHROPIC_API_KEY / OPENAI_API_KEY: legacy, no longer required
- DATABASE_URL: SQLite URL for persistence (default: sqlite://./patchpilot.db)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent.resolve()

# Load .env file from project root or backend dir
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Gemini model used by all three agents
# gemini-2.0-flash is available on the free tier
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

# Database
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR}/patchpilot.db")

# Server
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Agent configuration
AGENT_TIMEOUT_SECONDS = int(os.environ.get("AGENT_TIMEOUT_SECONDS", "60"))
MAX_CONTEXT_TOKENS = int(os.environ.get("MAX_CONTEXT_TOKENS", "8000"))

# Switch/ Claude SDK settings
CLAUDE_MODEL_VISION = os.environ.get("CLAUDE_MODEL_VISION", "claude-3-5-sonnet-20240620")
CLAUDE_MODEL_REASONING = os.environ.get("CLAUDE_MODEL_REASONING", "claude-3-5-sonnet-20240620")

# OpenAI model fallbacks
OPENAI_VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
OPENAI_REASONING_MODEL = os.environ.get("OPENAI_REASONING_MODEL", "gpt-4o-mini")

# CORS origins (frontend URL)
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else []

print(f"Config loaded: DATABASE_URL={DATABASE_URL}, HOST={HOST}, PORT={PORT}")