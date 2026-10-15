"""Pydantic request and response models for the API."""

from pydantic import BaseModel, field_validator


class AskRequest(BaseModel):
	"""A nonempty user question for the RAG endpoint."""

	question: str

	@field_validator("question")
	@classmethod
	def normalize_question(cls, value: str) -> str:
		"""Trim surrounding whitespace and reject an empty question."""
		question = value.strip()
		if not question:
			raise ValueError("Question cannot be empty.")
		return question


class AskResponse(BaseModel):
	"""The original question and its generated answer."""

	question: str
	answer: str