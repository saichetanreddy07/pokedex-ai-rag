"""Build deterministic six-Pokémon teams from structured base data."""

import re
from typing import Any

from backend.config import TARGET_GENERATION
from backend.recommender import (
	TYPE_DISPLAY_NAMES,
	display_types,
	explain_selected,
	load_pokemon_catalog,
	public_profile,
	team_role,
)

# Standard type matchups, represented as (weaknesses, resistances, immunities).
TYPE_MATCHUPS: dict[str, tuple[set[str], set[str], set[str]]] = {
	"normal": (set(), {"rock", "steel"}, {"ghost"}),
	"fire": ({"grass", "ice", "bug", "steel"}, {"fire", "water", "rock", "dragon"}, set()),
	"water": ({"fire", "ground", "rock"}, {"water", "grass", "dragon"}, set()),
	"electric": ({"water", "flying"}, {"electric", "grass", "dragon"}, {"ground"}),
	"grass": ({"water", "ground", "rock"}, {"fire", "grass", "poison", "flying", "bug", "dragon", "steel"}, set()),
	"ice": ({"grass", "ground", "flying", "dragon"}, {"fire", "water", "ice", "steel"}, set()),
	"fighting": ({"normal", "ice", "rock", "dark", "steel"}, {"poison", "flying", "psychic", "bug", "fairy"}, {"ghost"}),
	"poison": ({"grass", "fairy"}, {"poison", "ground", "rock", "ghost"}, {"steel"}),
	"ground": ({"fire", "electric", "poison", "rock", "steel"}, {"grass", "bug"}, {"flying"}),
	"flying": ({"grass", "fighting", "bug"}, {"electric", "rock", "steel"}, set()),
	"psychic": ({"fighting", "poison"}, {"psychic", "steel"}, {"dark"}),
	"bug": ({"grass", "psychic", "dark"}, {"fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"}, set()),
	"rock": ({"fire", "ice", "flying", "bug"}, {"fighting", "ground", "steel"}, set()),
	"ghost": ({"psychic", "ghost"}, {"dark"}, {"normal"}),
	"dragon": ({"dragon"}, {"steel"}, {"fairy"}),
	"dark": ({"psychic", "ghost"}, {"fighting", "dark", "fairy"}, set()),
	"steel": ({"ice", "rock", "fairy"}, {"fire", "water", "electric", "steel"}, set()),
	"fairy": ({"fighting", "dragon", "dark"}, {"fire", "poison", "steel"}, set()),
}

ROMAN_GENERATIONS = {
	"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
	"vi": 6, "vii": 7, "viii": 8, "ix": 9,
}


def _active_attack_types(team: list[dict[str, Any]]) -> set[str]:
	"""Limit matchup checks to types represented in the team's generation data."""
	generations = {pokemon["generation"] for pokemon in team}
	return {
		type_name
		for pokemon in load_pokemon_catalog()
		if pokemon["generation"] in generations
		for type_name in pokemon["types"]
	}


def _effectiveness(attack_type: str, defender_types: list[str]) -> float:
	"""Return type effectiveness for one attack against a Pokémon's typing."""
	weaknesses, resistances, immunities = TYPE_MATCHUPS.get(
		attack_type, (set(), set(), set())
	)
	effectiveness = 1.0
	for defender_type in defender_types:
		if defender_type in immunities:
			return 0.0
		if defender_type in weaknesses:
			effectiveness *= 2.0
		elif defender_type in resistances:
			effectiveness *= 0.5
	return effectiveness


def weaknesses_for_team(team: list[dict[str, Any]]) -> dict[str, int]:
	"""Count how many team members are weak to each attacking type."""
	weakness_counts: dict[str, int] = {}
	for attack_type in _active_attack_types(team):
		count = sum(
			_effectiveness(attack_type, pokemon["types"]) > 1
			for pokemon in team
		)
		if count:
			weakness_counts[TYPE_DISPLAY_NAMES.get(attack_type, attack_type.title())] = count
	return weakness_counts


def resistances_for_team(team: list[dict[str, Any]]) -> dict[str, int]:
	"""Count how many team members resist or are immune to each type."""
	resistance_counts: dict[str, int] = {}
	for attack_type in _active_attack_types(team):
		count = sum(
			_effectiveness(attack_type, pokemon["types"]) < 1
			for pokemon in team
		)
		if count:
			resistance_counts[TYPE_DISPLAY_NAMES.get(attack_type, attack_type.title())] = count
	return resistance_counts


def _generation_filter(query: str) -> str:
	"""Read a requested generation; default to the configured dataset generation."""
	match = re.search(r"(?:generation|gen)\s*(ix|viii|vii|vi|v|iv|iii|ii|i|[1-9])\b", query.lower())
	if not match:
		generation_number = TARGET_GENERATION
	else:
		value = match.group(1)
		generation_number = int(value) if value.isdigit() else ROMAN_GENERATIONS[value]
	return f"generation-{_to_roman(generation_number)}"


def _to_roman(number: int) -> str:
	"""Convert a generation number from one through nine into a Roman numeral."""
	roman_values = (
		(9, "ix"), (8, "viii"), (7, "vii"), (6, "vi"), (5, "v"),
		(4, "iv"), (3, "iii"), (2, "ii"), (1, "i"),
	)
	result = ""
	for value, numeral in roman_values:
		if number >= value:
			result += numeral
			number -= value
	return result


def _theme(query: str) -> str:
	"""Classify the requested team-building objective."""
	cleaned = query.lower()
	if "rain" in cleaned:
		return "rain"
	if "beginner" in cleaned or "starter" in cleaned:
		return "beginner"
	if "fast" in cleaned or "offensive" in cleaned:
		return "fast_offense"
	if "defensive" in cleaned or "wall" in cleaned:
		return "defensive"
	if "electric" in cleaned and "coverage" in cleaned:
		return "electric_coverage"
	return "balanced"


def _team_score(
	pokemon: dict[str, Any],
	team: list[dict[str, Any]],
	theme: str,
	legendary_allowed: bool,
) -> float:
	"""Score a candidate for the theme and the coverage already on the team."""
	if not legendary_allowed and (pokemon["is_legendary"] or pokemon["is_mythical"]):
		return float("-inf")
	stats = pokemon["stats"]
	total_stats = pokemon["total_stats"]
	if theme == "rain":
		water_count = sum("water" in member["types"] for member in team)
		score = 140 if "water" in pokemon["types"] and water_count < 3 else 0
		if "electric" in pokemon["types"] or "grass" in pokemon["types"]:
			score += 75
		score += stats["special_attack"] * 0.7 + stats["speed"] * 0.3
	elif theme == "beginner":
		score = 120 - abs(total_stats - 350) * 0.3
		score += 20 if len(pokemon["types"]) <= 2 else 0
	elif theme == "fast_offense":
		score = stats["speed"] * 1.5 + max(stats["attack"], stats["special_attack"])
	elif theme == "defensive":
		score = stats["hp"] + stats["defense"] + stats["special_defense"]
	elif theme == "electric_coverage":
		ground_count = sum("ground" in member["types"] for member in team)
		if "ground" in pokemon["types"]:
			score = 180 if ground_count == 0 else -40
		else:
			score = 35
		score += max(stats["attack"], stats["special_attack"]) * 0.4
	else:
		score = total_stats
	team_types = {type_name for member in team for type_name in member["types"]}
	score += 35 * len(set(pokemon["types"]) - team_types)
	team_roles = {team_role(member) for member in team}
	if team_role(pokemon) not in team_roles:
		score += 25
	if team:
		current_weaknesses = weaknesses_for_team(team)
		for attack_type in current_weaknesses:
			if _effectiveness(attack_type.lower(), pokemon["types"]) < 1:
				score += min(18, current_weaknesses[attack_type] * 4)
	return score


def _find_around_pokemon(query: str) -> dict[str, Any] | None:
	"""Find a catalog Pokémon named in an 'around X' team request."""
	if "around" not in query.lower():
		return None
	return next(
		(
			pokemon
			for pokemon in load_pokemon_catalog()
			if pokemon["key"] in re.sub(r"[^a-z0-9]", "", query.lower())
		),
		None,
	)


def _team_reason(pokemon: dict[str, Any], theme: str) -> str:
	"""Create a factual selection basis for a team member."""
	stats = pokemon["stats"]
	type_text = "/".join(display_types(pokemon)) or "unknown"
	if theme == "rain":
		focus = "Water-type synergy" if "water" in pokemon["types"] else "complementary special offense"
	elif theme == "beginner":
		focus = "a non-legendary profile with accessible stat distribution"
	elif theme == "fast_offense":
		focus = f"base Speed {stats['speed']} and an attacking stat of {max(stats['attack'], stats['special_attack'])}"
	elif theme == "defensive":
		focus = f"combined HP and defenses of {stats['hp'] + stats['defense'] + stats['special_defense']}"
	elif theme == "electric_coverage":
		focus = "Ground typing, which is immune to Electric attacks" if "ground" in pokemon["types"] else "additional offensive type coverage"
	else:
		focus = f"its {team_role(pokemon).lower()} role and base stat total of {pokemon['total_stats']}"
	return f"Selected for {focus}; its type is {type_text}."


def build_team(query: str) -> dict[str, Any]:
	"""Build a six-member team and summarize type and role coverage."""
	cleaned_query = query.strip()
	if not cleaned_query:
		raise ValueError("Team request cannot be empty.")
	generation = _generation_filter(cleaned_query)
	catalog = [
		pokemon for pokemon in load_pokemon_catalog()
		if pokemon["generation"] == generation
	]
	if not catalog:
		raise ValueError(
			f"No processed Pokémon are available for {generation.replace('-', ' ').title()}. "
			"Build that generation's dataset before requesting this team."
		)
	cleaned_lower = cleaned_query.lower()
	if any(
		phrase in cleaned_lower
		for phrase in ("without legendary", "no legendary", "non-legendary", "non legendary")
	):
		legendary_allowed = False
	else:
		legendary_allowed = True
	theme = _theme(cleaned_query)
	around = _find_around_pokemon(cleaned_query)
	if "around" in cleaned_query.lower() and around is None:
		raise ValueError("The Pokémon named after 'around' was not found in the dataset.")
	if around and around["generation"] != generation:
		raise ValueError(f"{around['name'].title()} is not in the requested generation.")
	if around and not legendary_allowed and (around["is_legendary"] or around["is_mythical"]):
		raise ValueError("The requested anchor Pokémon conflicts with excluding legendary Pokémon.")
	team = [around] if around else []
	while len(team) < 6:
		candidates = [pokemon for pokemon in catalog if pokemon not in team]
		candidates.sort(
			key=lambda pokemon: _team_score(
				pokemon, team, theme, legendary_allowed
			),
			reverse=True,
		)
		if not candidates or _team_score(candidates[0], team, theme, legendary_allowed) == float("-inf"):
			raise ValueError("Not enough eligible Pokémon are available to build a team of six.")
		team.append(candidates[0])

	fallback_reasons = [_team_reason(pokemon, theme) for pokemon in team]
	reasons, explanation, explanation_source = explain_selected(
		cleaned_query, team, fallback_reasons
	)
	weaknesses = weaknesses_for_team(team)
	resistances = resistances_for_team(team)
	roles = [team_role(pokemon) for pokemon in team]
	team_types = sorted({type_name for pokemon in team for type_name in pokemon["types"]})
	major_weaknesses = [
		type_name for type_name, count in weaknesses.items() if count >= 3
	]
	return {
		"request": cleaned_query,
		"generation": generation.replace("generation-", "Generation ").title(),
		"team": [
			{**public_profile(pokemon), "slot": index, "reason": reason}
			for index, (pokemon, reason) in enumerate(zip(team, reasons), start=1)
		],
		"analysis": {
			"offensive_coverage": [TYPE_DISPLAY_NAMES[type_name] for type_name in team_types],
			"defensive_coverage": sorted(resistances),
			"type_balance": f"{len(team_types)} distinct types across six Pokémon",
			"roles": sorted(set(roles)),
			"strengths": [
				f"{len(team_types)} distinct STAB types provide varied offensive options.",
				f"The team has {len(set(roles))} stat-based roles: {', '.join(sorted(set(roles)))}.",
			],
			"weaknesses": [
				f"{type_name} attacks threaten {weaknesses[type_name]} team members."
				for type_name in major_weaknesses
			],
		},
		"explanation": explanation,
		"explanation_source": explanation_source,
	}
