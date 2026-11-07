
"""PatchPilot Backend Configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BASE_DIR.parent.resolve()

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")

# Gemini configuration (used by backend/services/llm.py)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.environ.get(
    "GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta",
)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

# Other API keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Database
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR}/patchpilot.db",
)

# Server
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Agent configuration
AGENT_TIMEOUT_SECONDS = int(
    os.environ.get("AGENT_TIMEOUT_SECONDS", "60")
)
LLM_TIMEOUT_SECONDS = int(
    os.environ.get("LLM_TIMEOUT_SECONDS", "60")
)
MAX_CONTEXT_TOKENS = int(
    os.environ.get("MAX_CONTEXT_TOKENS", "8000")
)
MAX_SOURCE_CHARS = int(
    os.environ.get("MAX_SOURCE_CHARS", "12000")
)

# Other model settings
CLAUDE_MODEL_VISION = os.environ.get(
    "CLAUDE_MODEL_VISION",
    "claude-3-5-sonnet-20240620",
)
CLAUDE_MODEL_REASONING = os.environ.get(
    "CLAUDE_MODEL_REASONING",
    "claude-3-5-sonnet-20240620",
)

OPENAI_VISION_MODEL = os.environ.get(
    "OPENAI_VISION_MODEL",
    "gpt-4o-mini",
)
OPENAI_REASONING_MODEL = os.environ.get(
    "OPENAI_REASONING_MODEL",
    "gpt-4o-mini",
)

# CORS
ALLOWED_ORIGINS = (
    os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if os.environ.get("ALLOWED_ORIGINS")
    else []
)

print(
    f"Config loaded: DATABASE_URL={DATABASE_URL}, "
    f"HOST={HOST}, PORT={PORT}"
)
