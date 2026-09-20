"""
Centralized configuration for the Reading Recommendation Agent.

Loads all settings from .env once at import time.
Every other module imports `settings` from here instead of calling os.getenv() directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Typed settings object — single source of truth for all config values."""

    def __init__(self):
        # --- Groq LLM (server-side only) ---
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL_NAME: str = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-120b")

        # --- Storage (dual-mode: local SQLite vs production Postgres) ---
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")  # production Postgres
        self.DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/app.db")  # local SQLite

        # --- Vector store ---
        self.CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "database/chroma")
        self.VECTOR_STORE_URL: str = os.getenv("VECTOR_STORE_URL", "")
        self.VECTOR_STORE_API_KEY: str = os.getenv("VECTOR_STORE_API_KEY", "")

        # --- Embeddings ---
        self.EMBEDDING_MODEL_NAME: str = os.getenv(
            "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        )

        # --- Agent behavior ---
        self.CONVERSATION_MEMORY_WINDOW: int = int(
            os.getenv("CONVERSATION_MEMORY_WINDOW", "8")
        )
        self.MAX_AGENT_ITERATIONS: int = int(
            os.getenv("MAX_AGENT_ITERATIONS", "6")
        )
        self.MAX_RECOMMENDATIONS: int = int(
            os.getenv("MAX_RECOMMENDATIONS", "5")
        )

        # --- Derived helpers ---
        self.PROJECT_ROOT: Path = PROJECT_ROOT

    # ── Convenience properties ───────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """True when a production DATABASE_URL is set (Vercel / hosted)."""
        return bool(self.DATABASE_URL)

    @property
    def has_groq_key(self) -> bool:
        """True when a Groq API key is configured."""
        return bool(self.GROQ_API_KEY)

    @property
    def has_vector_store(self) -> bool:
        """True when either local Chroma or a hosted vector store is available."""
        return bool(self.CHROMA_PERSIST_DIR) or bool(self.VECTOR_STORE_URL)

    @property
    def sqlite_path(self) -> Path:
        """Absolute path to the local SQLite database file."""
        p = Path(self.DATABASE_PATH)
        if not p.is_absolute():
            p = self.PROJECT_ROOT / p
        return p

    @property
    def chroma_path(self) -> Path:
        """Absolute path to the local Chroma persist directory."""
        p = Path(self.CHROMA_PERSIST_DIR)
        if not p.is_absolute():
            p = self.PROJECT_ROOT / p
        return p

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  GROQ_MODEL_NAME={self.GROQ_MODEL_NAME!r},\n"
            f"  has_groq_key={self.has_groq_key},\n"
            f"  is_production={self.is_production},\n"
            f"  DATABASE_PATH={self.DATABASE_PATH!r},\n"
            f"  CHROMA_PERSIST_DIR={self.CHROMA_PERSIST_DIR!r},\n"
            f"  EMBEDDING_MODEL_NAME={self.EMBEDDING_MODEL_NAME!r},\n"
            f"  CONVERSATION_MEMORY_WINDOW={self.CONVERSATION_MEMORY_WINDOW},\n"
            f"  MAX_AGENT_ITERATIONS={self.MAX_AGENT_ITERATIONS},\n"
            f"  MAX_RECOMMENDATIONS={self.MAX_RECOMMENDATIONS}\n"
            f")"
        )


# ── Module-level singleton ───────────────────────────────────────────────
settings = Settings()
