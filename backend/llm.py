"""Generate answers with the configured Ollama chat model."""

from functools import lru_cache

from langchain_ollama import ChatOllama

from backend.config import OLLAMA_MODEL


@lru_cache(maxsize=1)
def load_chat_model() -> ChatOllama:
	"""Create and cache the ChatOllama model instance."""
	return ChatOllama(model=OLLAMA_MODEL, temperature=0)


def generate_answer(prompt: str) -> str:
	"""Send a prompt to Ollama and return its plain-text answer."""
	if not prompt.strip():
		raise ValueError("Prompt cannot be empty.")

	response = load_chat_model().invoke(prompt)
	if not isinstance(response.content, str):
		raise TypeError("Ollama returned a non-text response.")
	return response.content.strip()