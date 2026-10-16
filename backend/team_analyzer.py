"""Analyze team roles, type matchups, balance, and replacement options."""

import re
from typing import Any

from backend.llm import generate_answer
from backend.recommender import (
	TYPE_DISPLAY_NAMES,
	display_types,
	explain_selected,
	find_pokemon,
	load_pokemon_catalog,
	public_profile,
	team_role,
)
from backend.team_builder import (
	TYPE_MATCHUPS,
	_effectiveness,
	resistances_for_team,
	weaknesses_for_team,
)

EXPECTED_ROLES = {
	"Fast attacker",
	"Physical attacker",
	"Special attacker",
	"Defensive anchor",
}


def _parse_names(team_input: str | list[str]) -> list[str]:
	"""Parse a team pasted as lines or commas, or accept a list of names."""
	if isinstance(team_input, str):
		lines = []
		for line in team_input.splitlines():
			cleaned_line = re.sub(r"^\s*(?:analyze my team:?|team:)\s*", "", line, flags=re.IGNORECASE)
			lines.extend(item.strip(" -*\t") for item in cleaned_line.split(","))
		names = [name for name in lines if name]
	else:
		names = [name.strip() for name in team_input if isinstance(name, str) and name.strip()]
	if not names:
		raise ValueError("Provide at least one Pokémon name to analyze.")
	if len(names) > 6:
		raise ValueError("A team can contain at most six Pokémon.")
	return names


def _load_team(team_input: str | list[str]) -> list[dict[str, Any]]:
	"""Resolve submitted names to processed Pokémon data and reject duplicates."""
	names = _parse_names(team_input)
	team = []
	seen: set[str] = set()
	unknown = []
	for name in names:
		pokemon = find_pokemon(name)
		if pokemon is None:
			unknown.append(name)
			continue
		if pokemon["key"] in seen:
			raise ValueError(f"{pokemon['name'].title()} appears more than once in the team.")
		seen.add(pokemon["key"])
		team.append(pokemon)
	if unknown:
		raise ValueError(
			"Pokémon not found in the processed dataset: " + ", ".join(unknown)
		)
	return team


def _offensive_types(team: list[dict[str, Any]]) -> list[str]:
	"""Return the distinct types represented by the team's Pokémon."""
	return sorted(
		{
			type_name
			for pokemon in team
			for type_name in pokemon["types"]
		}
	)


def _offensive_balance(team: list[dict[str, Any]]) -> dict[str, Any]:
	"""Compare average physical and special attacking stats on the team."""
	physical_average = sum(pokemon["stats"]["attack"] for pokemon in team) / len(team)
	special_average = sum(
		pokemon["stats"]["special_attack"] for pokemon in team
	) / len(team)
	difference = abs(physical_average - special_average)
	if difference < 15:
		label = "Balanced physical and special offense"
	elif physical_average > special_average:
		label = "Physical offense leaning"
	else:
		label = "Special offense leaning"
	return {
		"label": label,
		"average_attack": round(physical_average, 1),
		"average_special_attack": round(special_average, 1),
	}


def _defensive_balance(team: list[dict[str, Any]]) -> dict[str, Any]:
	"""Summarize repeated weaknesses, resistances, and type breadth."""
	weaknesses = weaknesses_for_team(team)
	resistances = resistances_for_team(team)
	duplicate_weaknesses = {
		type_name: count for type_name, count in weaknesses.items() if count >= 2
	}
	return {
		"label": (
			"Several shared weaknesses" if duplicate_weaknesses
			else "No repeated type weaknesses"
		),
		"weakness_types": len(weaknesses),
		"resisted_or_immune_types": len(resistances),
		"duplicate_weaknesses": duplicate_weaknesses,
	}


def _missing_roles(team: list[dict[str, Any]]) -> list[str]:
	"""List common stat-based roles not represented in the submitted team."""
	team_roles = {team_role(pokemon) for pokemon in team}
	return sorted(EXPECTED_ROLES - team_roles)


def _replacement_candidates(
	team: list[dict[str, Any]],
	weaknesses: dict[str, int],
	missing_roles: list[str],
) -> list[dict[str, Any]]:
	"""Suggest up to three unused Pokémon that address a team gap."""
	team_keys = {pokemon["key"] for pokemon in team}
	weak_types = {
		type_name.lower()
		for type_name, count in weaknesses.items()
		if count >= 2
	}
	catalog = [
		pokemon for pokemon in load_pokemon_catalog()
		if pokemon["key"] not in team_keys
		and not pokemon["is_legendary"]
		and not pokemon["is_mythical"]
	]
	selected = []
	for missing_role in missing_roles:
		candidates = sorted(
			catalog,
			key=lambda pokemon: (
				team_role(pokemon) == missing_role,
				sum(
					_effectiveness(attack_type, pokemon["types"]) < 1
					for attack_type in weak_types
				),
				pokemon["total_stats"],
			),
			reverse=True,
		)
		if candidates and candidates[0] not in selected and team_role(candidates[0]) == missing_role:
			selected.append(candidates[0])
	for attack_type in sorted(
		weak_types,
		key=lambda value: weaknesses[TYPE_DISPLAY_NAMES[value]],
		reverse=True,
	):
		if len(selected) >= 3:
			break
		counter = next(
			(
				pokemon for pokemon in catalog
				if pokemon not in selected
				and _effectiveness(attack_type, pokemon["types"]) < 1
			),
			None,
		)
		if counter:
			selected.append(counter)
	selected = selected[:3]
	if not selected:
		return []
	fallback_reasons = []
	for pokemon in selected:
		covered = [
			TYPE_DISPLAY_NAMES[type_name]
			for type_name in weak_types
			if _effectiveness(type_name, pokemon["types"]) < 1
		]
		role = team_role(pokemon)
		why = []
		if role in missing_roles:
			why.append(f"adds the missing {role.lower()} role")
		if covered:
			why.append(f"resists or is immune to {', '.join(covered)} attacks")
		if not why:
			why.append(f"adds a {role.lower()} with {pokemon['total_stats']} base stat points")
		fallback_reasons.append("Suggested because it " + " and ".join(why) + ".")
	reasons, _summary, _source = explain_selected(
		"Suggest replacements for this team", selected, fallback_reasons
	)
	return [
		{
			**public_profile(pokemon),
			"reason": reason,
		}
		for pokemon, reason in zip(selected, reasons)
	]


def _overall_rating(
	team: list[dict[str, Any]],
	weaknesses: dict[str, int],
	roles: list[str],
	coverage: list[str],
) -> dict[str, Any]:
	"""Calculate an explainable heuristic team rating from roles and coverage."""
	score = 45
	score += min(20, len(coverage) * 2)
	score += min(15, len(set(roles)) * 4)
	score += min(10, len(resistances_for_team(team)))
	score -= sum(max(0, count - 1) * 4 for count in weaknesses.values())
	score = max(0, min(100, score))
	if score >= 85:
		label = "Excellent"
	elif score >= 70:
		label = "Strong"
	elif score >= 55:
		label = "Developing"
	else:
		label = "Needs work"
	return {"score": score, "label": label, "basis": "Heuristic based on role variety, type coverage, resistances, and repeated weaknesses."}


def analyze_team(team_input: str | list[str]) -> dict[str, Any]:
	"""Analyze team composition using Pokémon stats and standard type matchups."""
	team = _load_team(team_input)
	weaknesses = weaknesses_for_team(team)
	resistances = resistances_for_team(team)
	roles = [team_role(pokemon) for pokemon in team]
	missing_roles = _missing_roles(team)
	coverage = _offensive_types(team)
	duplicate_weaknesses = {
		type_name: count for type_name, count in weaknesses.items() if count >= 2
	}
	physical_special_balance = _offensive_balance(team)
	defense_balance = _defensive_balance(team)
	team_summary = {
		"names": [pokemon["name"].title() for pokemon in team],
		"types": {pokemon["name"].title(): display_types(pokemon) for pokemon in team},
		"roles": roles,
		"missing_roles": missing_roles,
		"weaknesses": weaknesses,
		"resistances": resistances,
		"offensive_balance": physical_special_balance,
		"defensive_balance": defense_balance,
		"offensive_type_coverage": [TYPE_DISPLAY_NAMES[type_name] for type_name in coverage],
	}
	try:
		explanation = generate_answer(
			"Explain this Pokémon team's strengths and tradeoffs in 3 concise sentences. "
			"Use only the supplied structured facts; do not invent moves or matchups.\n"
			f"Team analysis: {team_summary}"
		)
		explanation_source = "llm"
	except Exception:
		explanation = (
			f"The team covers {len(coverage)} attacking types and has "
			f"{len(set(roles))} distinct stat-based roles. "
			f"Its largest repeated weakness is "
			f"{max(duplicate_weaknesses, key=duplicate_weaknesses.get) if duplicate_weaknesses else 'none identified'}."
		)
		explanation_source = "rules"
	return {
		"team": [public_profile(pokemon) for pokemon in team],
		"missing_roles": missing_roles,
		"type_weaknesses": weaknesses,
		"type_resistances": resistances,
		"duplicate_weaknesses": duplicate_weaknesses,
		"offensive_balance": physical_special_balance,
		"defensive_balance": defense_balance,
		"suggested_replacements": _replacement_candidates(
			team, weaknesses, missing_roles
		),
		"overall_rating": _overall_rating(team, weaknesses, roles, coverage),
		"explanation": explanation.strip(),
		"explanation_source": explanation_source,
	}
