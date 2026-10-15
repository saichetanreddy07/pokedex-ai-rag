"""Environment-based settings for the application."""

import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/chroma_db")
TOP_K = int(os.getenv("TOP_K", "5"))
POKEAPI_BASE_URL = os.getenv(
	"POKEAPI_BASE_URL", "https://pokeapi.co/api/v2"
).rstrip("/")
POKEAPI_TIMEOUT = float(os.getenv("POKEAPI_TIMEOUT", "10"))
POKEAPI_MAX_RETRIES = int(os.getenv("POKEAPI_MAX_RETRIES", "3"))
TARGET_GENERATION = int(os.getenv("TARGET_GENERATION", "1"))