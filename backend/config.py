"""Environment-based settings for the application."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_chroma_db_path = Path(os.getenv("CHROMA_DB_PATH", "data/chroma_db"))
CHROMA_DB_PATH = str(
	_chroma_db_path if _chroma_db_path.is_absolute() else PROJECT_ROOT / _chroma_db_path
)
TOP_K = int(os.getenv("TOP_K", "5"))
POKEAPI_BASE_URL = os.getenv(
	"POKEAPI_BASE_URL", "https://pokeapi.co/api/v2"
).rstrip("/")
POKEAPI_TIMEOUT = float(os.getenv("POKEAPI_TIMEOUT", "10"))
POKEAPI_MAX_RETRIES = int(os.getenv("POKEAPI_MAX_RETRIES", "3"))
TARGET_GENERATION = int(os.getenv("TARGET_GENERATION", "1"))
