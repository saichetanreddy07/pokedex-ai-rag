"""Recommend Pokémon from structured dataset records, independently of RAG."""

import json
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import pandas as pd

from backend.config import PROJECT_ROOT, TARGET_GENERATION
from backend.llm import generate_answer

PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
STAT_NAMES = (
	"hp",
	"attack",
	"defense",
	"special_attack",
	"special_defense",
	"speed",
)
POKEMON_TYPES = (
	"normal", "fire", "water", "electric", "grass", "ice", "fighting",
	"poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
	"dragon", "dark", "steel", "fairy",
)
TYPE_DISPLAY_NAMES = {type_name: type_name.title() for type_name in POKEMON_TYPES}


def _split_values(value: Any) -> list[str]:
	"""Split a comma-separated CSV value into normalized nonempty strings."""
	if value is None or pd.isna(value):
		return []
	return [item.strip().lower() for item in str(value).split(",") if item.strip()]


def _to_bool(value: Any) -> bool:
	"""Convert a pandas boolean or CSV value into a Python boolean."""
	if value is None or pd.isna(value):
		return False
	return value is True or str(value).strip().lower() in {"true", "1"}


def _to_number(value: Any) -> int:
	"""Convert a dataset number to an integer, using zero for missing values."""
	if value is None or pd.isna(value):
		return 0
	return int(float(value))


@lru_cache(maxsize=1)
def load_pokemon_catalog() -> tuple[dict[str, Any], ...]:
	"""Load and cache Pokémon and species records from processed CSV files."""
	pokemon_path = PROCESSED_DATA_DIR / "pokemon.csv"
	species_path = PROCESSED_DATA_DIR / "species.csv"
	if not pokemon_path.is_file() or not species_path.is_file():
		raise FileNotFoundError(
			"Pokémon data is missing. Run backend.preprocessor before using "
			"the recommendation features."
		)

	pokemon_frame = pd.read_csv(pokemon_path, dtype={"id": "string"})
	species_frame = pd.read_csv(species_path, dtype={"id": "string"})
	merged = pokemon_frame.merge(
		species_frame,
		on="id",
		how="left",
		suffixes=("_pokemon", "_species"),
	)
	profiles = []
	for row in merged.to_dict(orient="records"):
		name = str(row.get("name_pokemon") or row.get("name_species") or "").strip()
		if not name:
			continue
		stats = {stat: _to_number(row.get(stat)) for stat in STAT_NAMES}
		profiles.append(
			{
				"id": str(row["id"]),
				"name": name,
				"key": normalize_name(name),
				"types": _split_values(row.get("types")),
				"abilities": _split_values(row.get("abilities")),
				"moves": _split_values(row.get("moves")),
				"stats": stats,
				"total_stats": sum(stats.values()),
				"generation": str(row.get("generation") or "").strip().lower(),
				"evolution_chain_id": _to_number(row.get("evolution_chain_id")),
				"is_legendary": _to_bool(row.get("is_legendary")),
				"is_mythical": _to_bool(row.get("is_mythical")),
				"height": _to_number(row.get("height")),
				"weight": _to_number(row.get("weight")),
			}
		)
	if not profiles:
		raise ValueError("No Pokémon records were found in the processed dataset.")
	return tuple(profiles)


def normalize_name(name: str) -> str:
	"""Normalize a Pokémon name for matching across user input and CSV data."""
	return re.sub(r"[^a-z0-9]", "", name.casefold())


def find_pokemon(name: str) -> dict[str, Any] | None:
	"""Find one Pokémon by its normalized species or display name."""
	key = normalize_name(name)
	return next((pokemon for pokemon in load_pokemon_catalog() if pokemon["key"] == key), None)


def display_types(pokemon: dict[str, Any]) -> list[str]:
	"""Return title-cased Pokémon type names for API presentation."""
	return [TYPE_DISPLAY_NAMES.get(type_name, type_name.title()) for type_name in pokemon["types"]]


def team_role(pokemon: dict[str, Any]) -> str:
	"""Assign a simple role from the Pokémon's base stats."""
	stats = pokemon["stats"]
	attack_value = stats["attack"]
	special_attack_value = stats["special_attack"]
	defensive_value = stats["defense"] + stats["special_defense"] + stats["hp"]
	if stats["speed"] >= 100 and max(attack_value, special_attack_value) >= 90:
		return "Fast attacker"
	if defensive_value >= 260:
		return "Defensive anchor"
	if special_attack_value > attack_value + 15:
		return "Special attacker"
	if attack_value > special_attack_value + 15:
		return "Physical attacker"
	return "Balanced attacker"


def public_profile(pokemon: dict[str, Any]) -> dict[str, Any]:
	"""Return the stable, JSON-safe profile fields used by recommendation APIs."""
	return {
		"name": pokemon["name"].title(),
		"types": display_types(pokemon),
		"abilities": [ability.replace("-", " ").title() for ability in pokemon["abilities"]],
		"stats": pokemon["stats"],
		"total_stats": pokemon["total_stats"],
		"generation": pokemon["generation"].replace("generation-", "Generation ").title(),
		"is_legendary": pokemon["is_legendary"],
		"is_mythical": pokemon["is_mythical"],
		"role": team_role(pokemon),
	}


def _requested_ability(query: str) -> str | None:
	"""Find a dataset ability explicitly named in a recommendation query."""
	cleaned_query = normalize_name(query)
	abilities = sorted(
		{ability for pokemon in load_pokemon_catalog() for ability in pokemon["abilities"]},
		key=len,
		reverse=True,
	)
	return next(
		(ability for ability in abilities if normalize_name(ability) in cleaned_query),
		None,
	)


def _requested_move(query: str) -> str | None:
	"""Find a processed learnable move explicitly named in the query."""
	cleaned_query = normalize_name(query)
	moves = sorted(
		{move for pokemon in load_pokemon_catalog() for move in pokemon["moves"]},
		key=len,
		reverse=True,
	)
	return next(
		(move for move in moves if normalize_name(move) in cleaned_query),
		None,
	)


def _query_constraints(query: str) -> dict[str, Any]:
	"""Extract simple type, stat, status, and similarity constraints."""
	words = set(re.findall(r"[a-z]+", query.lower()))
	type_name = next(
		(type_name for type_name in POKEMON_TYPES if type_name in words),
		None,
	)
	similar_match = re.search(r"similar to\s+(.+)", query, re.IGNORECASE)
	similar_name = None
	if similar_match:
		requested_name = normalize_name(similar_match.group(1))
		known_names = sorted(
			load_pokemon_catalog(), key=lambda pokemon: len(pokemon["key"]), reverse=True
		)
		similar_name = next(
			(
				pokemon["name"]
				for pokemon in known_names
				if requested_name.startswith(pokemon["key"])
			),
			similar_match.group(1).strip(" .,-"),
		)
	generation_match = re.search(
		r"(?:generation|gen)\s*(ix|viii|vii|vi|v|iv|iii|ii|i|[1-9])\b",
		query,
		re.IGNORECASE,
	)
	generation = None
	if generation_match:
		generation_value = generation_match.group(1).lower()
		generation_number = (
			int(generation_value)
			if generation_value.isdigit()
			else {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
				  "vi": 6, "vii": 7, "viii": 8, "ix": 9}[generation_value]
		)
		generation_roman = ("i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix")[generation_number - 1]
		generation = f"generation-{generation_roman}"
	stat = None
	if "special attack" in query.lower() or "special-attack" in query.lower():
		stat = "special_attack"
	elif "attack" in words:
		stat = "attack"
	elif "defensive" in words or "defense" in words:
		stat = "defense"
	elif "fast" in words or "speed" in words:
		stat = "speed"
	return {
		"type": type_name,
		"beginner": "beginner" in words or "starter" in words,
		"fast": "fast" in words or "speed" in words,
		"defensive": "defensive" in words or "defense" in words,
		"legendary": "legendary" in words,
		"mythical": "mythical" in words,
		"ability": _requested_ability(query),
		"move": _requested_move(query),
		"stat": stat,
		"similar": find_pokemon(similar_name) if similar_name else None,
		"generation": generation,
	}


def _similarity_score(
	candidate: dict[str, Any],
	target: dict[str, Any],
) -> float:
	"""Score shared typing, evolution family, abilities, moves, and stats."""
	target_types = set(target["types"])
	type_score = len(target_types.intersection(candidate["types"])) / max(len(target_types), 1)
	stat_distance = sum(
		abs(candidate["stats"][stat] - target["stats"][stat]) / 255
		for stat in STAT_NAMES
	) / len(STAT_NAMES)
	ability_overlap = len(set(candidate["abilities"]) & set(target["abilities"]))
	move_overlap = len(set(candidate["moves"]) & set(target["moves"]))
	score = 0.45 * type_score + 0.30 * (1 - stat_distance)
	score += 0.15 * bool(
		candidate["evolution_chain_id"]
		and candidate["evolution_chain_id"] == target["evolution_chain_id"]
	)
	score += 0.06 * min(ability_overlap, 1) + 0.04 * min(move_overlap / 5, 1)
	return score


def _matches_constraints(
	pokemon: dict[str, Any],
	constraints: dict[str, Any],
) -> bool:
	"""Return whether a Pokémon meets all explicit request constraints."""
	if constraints["type"] and constraints["type"] not in pokemon["types"]:
		return False
	if constraints["beginner"] and (pokemon["is_legendary"] or pokemon["is_mythical"]):
		return False
	if constraints["legendary"] and not pokemon["is_legendary"]:
		return False
	if constraints["mythical"] and not pokemon["is_mythical"]:
		return False
	if constraints["generation"] and pokemon["generation"] != constraints["generation"]:
		return False
	if constraints["ability"] and constraints["ability"] not in pokemon["abilities"]:
		return False
	if constraints["move"] and constraints["move"] not in pokemon["moves"]:
		return False
	return True


def _rank_score(
	pokemon: dict[str, Any],
	query: str,
	constraints: dict[str, Any],
) -> float:
	"""Score a matching Pokémon according to the requested stat or trait."""
	score = 0.0
	if constraints["stat"]:
		score += pokemon["stats"][constraints["stat"]] * 2
	else:
		score += pokemon["total_stats"] * 0.25
	if constraints["fast"]:
		score += pokemon["stats"]["speed"] * 1.5
	if constraints["defensive"]:
		score += (
			pokemon["stats"]["defense"]
			+ pokemon["stats"]["special_defense"]
			+ pokemon["stats"]["hp"]
		) * 0.8
	if constraints["ability"]:
		score += 100
	elif "ability" in query.lower():
		score += min(len(pokemon["abilities"]), 3) * 12
	if constraints["beginner"]:
		score += max(0, 100 - abs(pokemon["total_stats"] - 350) / 3)
	if constraints["legendary"] or constraints["mythical"]:
		score += pokemon["total_stats"] * 0.5
	if constraints["similar"]:
		score += 500 * _similarity_score(pokemon, constraints["similar"])
	return score


def _rule_reason(
	pokemon: dict[str, Any],
	query: str,
	constraints: dict[str, Any],
) -> str:
	"""Build a factual fallback reason from matched types and structured stats."""
	parts = []
	if constraints["type"]:
		parts.append(f"it is a {constraints['type'].title()} type")
	if constraints["ability"]:
		parts.append(f"it has the {constraints['ability'].replace('-', ' ').title()} ability")
	if constraints["move"]:
		parts.append(f"it can learn {constraints['move'].replace('-', ' ').title()}")
	if constraints["stat"]:
		parts.append(f"its base {constraints['stat'].replace('_', ' ')} is {pokemon['stats'][constraints['stat']]}")
	if constraints["fast"] and not constraints["stat"] == "speed":
		parts.append(f"its base Speed is {pokemon['stats']['speed']}")
	if constraints["defensive"]:
		parts.append(
			"its combined HP and defensive stats are "
			f"{pokemon['stats']['hp'] + pokemon['stats']['defense'] + pokemon['stats']['special_defense']}"
		)
	if constraints["similar"]:
		shared = sorted(set(pokemon["types"]) & set(constraints["similar"]["types"]))
		parts.append(
			f"it shares {', '.join(shared)} typing with {constraints['similar']['name'].title()}"
			if shared
			else f"its stat profile is similar to {constraints['similar']['name'].title()}"
		)
	if constraints["beginner"]:
		parts.append("it is non-legendary and has a straightforward stat profile")
	if constraints["legendary"]:
		parts.append("it is marked legendary in the species data")
	if constraints["mythical"]:
		parts.append("it is marked mythical in the species data")
	if "ability" in query.lower() and not constraints["ability"] and pokemon["abilities"]:
		ability_names = ", ".join(
			ability.replace("-", " ").title() for ability in pokemon["abilities"]
		)
		parts.append(f"its recorded abilities include {ability_names}")
	if not parts:
		parts.append(f"it has a base stat total of {pokemon['total_stats']}")
	return f"Recommended because {', and '.join(parts)}."


def explain_selected(
	query: str,
	selected: list[dict[str, Any]],
	fallback_reasons: list[str],
) -> tuple[list[str], str, str]:
	"""Ask the configured LLM to explain selected records, with rule fallback."""
	if not selected:
		return [], "No matching Pokémon were found in the structured dataset.", "rules"
	compact_records = [
		{
			"name": pokemon["name"].title(),
			"types": display_types(pokemon),
			"abilities": pokemon["abilities"],
			"stats": pokemon["stats"],
			"reason_basis": fallback,
		}
		for pokemon, fallback in zip(selected, fallback_reasons)
	]
	prompt = (
		"Explain why each selected Pokémon fits the user's request. Use only the "
		"provided records, do not add Pokémon, and do not invent facts. Return only "
		"valid JSON with keys 'summary' (string) and 'reasons' (object mapping each "
		"exact Pokémon name to one concise reason).\n"
		f"User request: {query}\nRecords: {json.dumps(compact_records)}"
	)
	try:
		response = generate_answer(prompt)
		json_start = response.find("{")
		json_end = response.rfind("}")
		if json_start < 0 or json_end <= json_start:
			raise ValueError("The model response did not contain a JSON object.")
		payload = json.loads(response[json_start:json_end + 1])
		reasons_payload = payload.get("reasons")
		if not isinstance(reasons_payload, dict):
			raise ValueError("The model response did not contain recommendation reasons.")
		reasons = []
		for pokemon, fallback in zip(selected, fallback_reasons):
			model_reason = reasons_payload.get(pokemon["name"].title())
			reasons.append(
				model_reason.strip()
				if isinstance(model_reason, str) and model_reason.strip()
				else fallback
			)
		summary = payload.get("summary")
		if not isinstance(summary, str) or not summary.strip():
			summary = "Recommendations are ranked from the matching structured Pokémon records."
		return reasons, summary.strip(), "llm"
	except Exception:
		return (
			fallback_reasons,
			"LLM explanations are unavailable; reasons use the matched structured data.",
			"rules",
		)


def recommend_pokemon(query: str, limit: int = 5) -> dict[str, Any]:
	"""Return structured Pokémon recommendations and natural-language reasons."""
	cleaned_query = query.strip()
	if not cleaned_query:
		raise ValueError("Recommendation query cannot be empty.")
	if not 1 <= limit <= 10:
		raise ValueError("Recommendation limit must be between 1 and 10.")
	constraints = _query_constraints(cleaned_query)
	catalog = load_pokemon_catalog()
	if constraints["similar"] is None and "similar to" in cleaned_query.lower():
		raise ValueError("The Pokémon named after 'similar to' was not found in the dataset.")
	matches = [
		pokemon
		for pokemon in catalog
		if _matches_constraints(pokemon, constraints)
		and (not constraints["similar"] or pokemon["key"] != constraints["similar"]["key"])
	]
	if not matches:
		raise ValueError("No Pokémon in the processed dataset match those constraints.")
	selected = sorted(
		matches,
		key=lambda pokemon: _rank_score(pokemon, cleaned_query, constraints),
		reverse=True,
	)[:limit]
	fallback_reasons = [
		_rule_reason(pokemon, cleaned_query, constraints) for pokemon in selected
	]
	reasons, summary, explanation_source = explain_selected(
		cleaned_query, selected, fallback_reasons
	)
	return {
		"query": cleaned_query,
		"recommendations": [
			{
				**public_profile(pokemon),
				"reason": reason,
			}
			for pokemon, reason in zip(selected, reasons)
		],
		"explanation": summary,
		"explanation_source": explanation_source,
	}


def available_generations() -> list[str]:
	"""Return generations represented in the processed Pokémon dataset."""
	return sorted(
		{
			pokemon["generation"]
			for pokemon in load_pokemon_catalog()
			if pokemon["generation"]
		}
	)
