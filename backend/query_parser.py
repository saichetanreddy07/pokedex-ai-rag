"""Parse Pokémon, document intent, and generation from retrieval queries."""

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re

from backend.config import PROJECT_ROOT, TARGET_GENERATION

_ROMAN_GENERATIONS = {
	"i": 1,
	"ii": 2,
	"iii": 3,
	"iv": 4,
	"v": 5,
	"vi": 6,
	"vii": 7,
	"viii": 8,
	"ix": 9,
}
_GENERATION_NUMERALS = tuple(_ROMAN_GENERATIONS)


@dataclass(frozen=True)
class PokemonEntity:
	"""A Pokémon identity and the metadata needed for retrieval filters."""

	name: str
	pokemon: str
	generation: str
	evolution_chain_id: str


@dataclass(frozen=True)
class ParsedQuery:
	"""Query intent and entity information used to build a ChromaDB filter."""

	pokemon: tuple[PokemonEntity, ...]
	document_type: str | None
	generation: str


def _normalize_name(value: str) -> str:
	"""Remove punctuation and spacing to compare dataset names with query text."""
	return re.sub(r"[^a-z0-9]", "", value.casefold())


@lru_cache(maxsize=1)
def _load_pokemon_entities() -> tuple[PokemonEntity, ...]:
	"""Load searchable Pokémon names and their species metadata from CSVs."""
	data_dir = PROJECT_ROOT / "data" / "processed"
	pokemon_path = data_dir / "pokemon.csv"
	species_path = data_dir / "species.csv"
	if not pokemon_path.is_file() or not species_path.is_file():
		return ()

	with species_path.open(encoding="utf-8-sig", newline="") as csv_file:
		species_by_id = {
			row["id"]: row for row in csv.DictReader(csv_file)
		}
	entities = []
	with pokemon_path.open(encoding="utf-8-sig", newline="") as csv_file:
		for row in csv.DictReader(csv_file):
			name = row.get("name", "").strip().lower()
			species = species_by_id.get(row.get("id", ""), {})
			if not name:
				continue
			entities.append(
				PokemonEntity(
					name=name,
					pokemon=name,
					generation=species.get("generation", "").strip().lower(),
					evolution_chain_id=species.get("evolution_chain_id", "").strip(),
				)
			)
	return tuple(entities)


def _query_name_tokens(query: str) -> list[str]:
	"""Tokenize a query while preserving apostrophe-separated name parts."""
	return re.findall(r"[a-z0-9]+", query.casefold())


def _detect_pokemon(query: str) -> tuple[PokemonEntity, ...]:
	"""Find catalog names in a query, including punctuation variants."""
	tokens = _query_name_tokens(query)
	entities = sorted(
		_load_pokemon_entities(),
		key=lambda entity: len(_normalize_name(entity.name)),
		reverse=True,
	)
	found = []
	for entity in entities:
		name_key = _normalize_name(entity.name)
		if any(
			"".join(tokens[start:end]) == name_key
			for start in range(len(tokens))
			for end in range(start + 1, len(tokens) + 1)
		):
			found.append(entity)
	return tuple(found)


def _detect_document_type(query: str) -> str | None:
	"""Classify a clear question intent into one indexed document category."""
	cleaned = " ".join(re.findall(r"[a-z]+", query.casefold()))
	if re.search(r"\b(evolv\w*|evolution(?: chain)?)\b", cleaned):
		return "evolution_chain"
	if re.search(r"\b(abilit\w*)\b", cleaned):
		return "abilities"
	if re.search(r"\b(move|moves|learn|learns|learned|learnset)\b", cleaned):
		return "moves"
	if re.search(r"\b(height|tall|weigh|weight|heavy|physical)\b", cleaned):
		return "physical"
	if re.search(
		r"\b(stats?|hp|attack|defen[cs]e|speed|special attack|special defense)\b",
		cleaned,
	):
		return "stats"
	if re.search(r"\b(types?|typing)\b", cleaned):
		return "types"
	if re.search(r"\b(what is|who is|tell me about|describe)\b", cleaned):
		return "overview"
	return None


def _generation_name(value: str) -> str:
	"""Convert a generation number or Roman numeral to metadata form."""
	generation_number = (
		int(value) if value.isdigit() else _ROMAN_GENERATIONS[value.lower()]
	)
	if not 1 <= generation_number <= len(_GENERATION_NUMERALS):
		return ""
	return f"generation-{_GENERATION_NUMERALS[generation_number - 1]}"


def _detect_generation(query: str) -> str:
	"""Return an explicit generation or the configured project generation."""
	match = re.search(
		r"\b(?:generation|gen)\s*(ix|viii|vii|vi|v|iv|iii|ii|i|[1-9])\b",
		query,
		re.IGNORECASE,
	)
	if match:
		return _generation_name(match.group(1))
	return _generation_name(str(TARGET_GENERATION))


def parse_query(query: str) -> ParsedQuery:
	"""Extract Pokémon entities, document intent, and active generation."""
	return ParsedQuery(
		pokemon=_detect_pokemon(query),
		document_type=_detect_document_type(query),
		generation=_detect_generation(query),
	)
