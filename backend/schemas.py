"""Pydantic request and response models for the API."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class RecommendRequest(BaseModel):
	"""Natural-language request for structured Pokémon recommendations."""

	query: str
	limit: int = Field(default=5, ge=1, le=10)

	@field_validator("query")
	@classmethod
	def normalize_query(cls, value: str) -> str:
		"""Trim the recommendation query and reject blank input."""
		query = value.strip()
		if not query:
			raise ValueError("Recommendation query cannot be empty.")
		return query


class TeamRequest(BaseModel):
	"""Natural-language request for a six-Pokémon team."""

	query: str

	@field_validator("query")
	@classmethod
	def normalize_query(cls, value: str) -> str:
		"""Trim the team request and reject blank input."""
		query = value.strip()
		if not query:
			raise ValueError("Team request cannot be empty.")
		return query


class AnalyzeTeamRequest(BaseModel):
	"""Team names supplied as a pasted string or list of names."""

	team: str | list[str]

	@field_validator("team")
	@classmethod
	def validate_team(cls, value: str | list[str]) -> str | list[str]:
		"""Reject empty teams and values that cannot contain Pokémon names."""
		if isinstance(value, str):
			if not value.strip():
				raise ValueError("Provide at least one Pokémon name to analyze.")
			return value.strip()
		if not value or any(not isinstance(name, str) or not name.strip() for name in value):
			raise ValueError("Team must contain nonempty Pokémon names.")
		return [name.strip() for name in value]


class RecommendationItem(BaseModel):
	"""One recommended Pokémon with structured data and explanation."""

	name: str
	types: list[str]
	abilities: list[str]
	stats: dict[str, int]
	total_stats: int
	generation: str
	is_legendary: bool
	is_mythical: bool
	role: str
	reason: str = ""


class RecommendResponse(BaseModel):
	"""Recommended Pokémon and the explanation source."""

	query: str
	recommendations: list[RecommendationItem]
	explanation: str
	explanation_source: str


class TeamResponse(BaseModel):
	"""Six selected Pokémon with coverage and explanation."""

	request: str
	generation: str
	team: list[RecommendationItem]
	analysis: dict[str, Any]
	explanation: str
	explanation_source: str


class TeamAnalysisResponse(BaseModel):
	"""Structured composition analysis for a submitted team."""

	team: list[RecommendationItem]
	missing_roles: list[str]
	type_weaknesses: dict[str, int]
	type_resistances: dict[str, int]
	duplicate_weaknesses: dict[str, int]
	offensive_balance: dict[str, Any]
	defensive_balance: dict[str, Any]
	suggested_replacements: list[RecommendationItem]
	overall_rating: dict[str, Any]
	explanation: str
	explanation_source: str
