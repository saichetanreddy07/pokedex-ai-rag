"""Convert raw PokéAPI JSON files into clean CSV datasets."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

POKEMON_COLUMNS = [
	"id", "name", "height", "weight", "base_experience", "types",
	"abilities", "moves", "hp", "attack", "defense", "special_attack",
	"special_defense", "speed", "sprite_url",
]
SPECIES_COLUMNS = [
	"id", "name", "generation", "habitat", "color", "shape",
	"is_legendary", "is_mythical", "capture_rate", "base_happiness",
	"growth_rate", "description", "evolution_chain_id",
]
MOVE_COLUMNS = [
	"id", "name", "type", "power", "accuracy", "pp", "priority",
	"damage_class", "generation", "effect",
]
EVOLUTION_CHAIN_COLUMNS = ["chain_id", "base_pokemon", "stage_2", "stage_3"]


def clean_text(value: Any) -> str:
	"""Strip and normalize whitespace in a text value."""
	if value is None:
		return ""
	return " ".join(str(value).split())


def load_json(file_path: Path) -> dict[str, Any]:
	"""Load one JSON file and require its top-level value to be an object."""
	with file_path.open(encoding="utf-8") as json_file:
		data = json.load(json_file)
	if not isinstance(data, dict):
		raise ValueError("Expected a JSON object at the top level.")
	return data


def _get_name(value: Any) -> str:
	"""Return a nested PokéAPI resource name when available."""
	if isinstance(value, dict):
		return clean_text(value.get("name"))
	return ""


def _get_names(entries: Any, resource_key: str) -> str:
	"""Join names from a list of nested PokéAPI resources."""
	if not isinstance(entries, list):
		return ""

	names = []
	for entry in entries:
		if isinstance(entry, dict):
			name = _get_name(entry.get(resource_key))
			if name:
				names.append(name)
	return ",".join(names)


def extract_pokemon(data: dict[str, Any]) -> dict[str, Any]:
	"""Extract the requested fields from one Pokémon resource."""
	stats: dict[str, Any] = {
		"hp": None,
		"attack": None,
		"defense": None,
		"special_attack": None,
		"special_defense": None,
		"speed": None,
	}
	stat_names = {
		"hp": "hp",
		"attack": "attack",
		"defense": "defense",
		"special-attack": "special_attack",
		"special-defense": "special_defense",
		"speed": "speed",
	}
	stat_entries = data.get("stats")
	if isinstance(stat_entries, list):
		for entry in stat_entries:
			if not isinstance(entry, dict):
				continue
			stat = entry.get("stat")
			stat_name = stat.get("name") if isinstance(stat, dict) else None
			if stat_name in stat_names:
				stats[stat_names[stat_name]] = entry.get("base_stat")

	sprites = data.get("sprites")
	sprite_url = sprites.get("front_default") if isinstance(sprites, dict) else None
	type_names = []
	types = data.get("types", [])
	if isinstance(types, list):
		for entry in types:
			name = _get_name(entry.get("type")) if isinstance(entry, dict) else ""
			if name:
				type_names.append(name)

	return {
		"id": data.get("id"),
		"name": clean_text(data.get("name")),
		"height": data.get("height"),
		"weight": data.get("weight"),
		"base_experience": data.get("base_experience"),
		"types": ",".join(type_names),
		"abilities": _get_names(data.get("abilities"), "ability"),
		"moves": _get_names(data.get("moves"), "move"),
		**stats,
		"sprite_url": clean_text(sprite_url),
	}


def _get_english_text(entries: Any, text_key: str) -> str:
	"""Return the first available English text from a PokéAPI list."""
	if not isinstance(entries, list):
		return ""
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		if _get_name(entry.get("language")) == "en":
			text = clean_text(entry.get(text_key))
			if text:
				return text
	return ""


def _extract_id(url: Any) -> int | None:
	"""Extract a numeric resource ID from a PokéAPI URL."""
	if not isinstance(url, str):
		return None
	resource_id = url.rstrip("/").rsplit("/", 1)[-1]
	return int(resource_id) if resource_id.isdecimal() else None


def extract_species(data: dict[str, Any]) -> dict[str, Any]:
	"""Extract the requested fields from one Pokémon species resource."""
	evolution_chain = data.get("evolution_chain")
	evolution_chain_url = (
		evolution_chain.get("url")
		if isinstance(evolution_chain, dict)
		else None
	)
	return {
		"id": data.get("id"),
		"name": clean_text(data.get("name")),
		"generation": _get_name(data.get("generation")),
		"habitat": _get_name(data.get("habitat")),
		"color": _get_name(data.get("color")),
		"shape": _get_name(data.get("shape")),
		"is_legendary": data.get("is_legendary"),
		"is_mythical": data.get("is_mythical"),
		"capture_rate": data.get("capture_rate"),
		"base_happiness": data.get("base_happiness"),
		"growth_rate": _get_name(data.get("growth_rate")),
		"description": _get_english_text(
			data.get("flavor_text_entries"), "flavor_text"
		),
		"evolution_chain_id": _extract_id(evolution_chain_url),
	}


def extract_move(data: dict[str, Any]) -> dict[str, Any]:
	"""Extract the requested fields from one move resource."""
	return {
		"id": data.get("id"),
		"name": clean_text(data.get("name")),
		"type": _get_name(data.get("type")),
		"power": data.get("power"),
		"accuracy": data.get("accuracy"),
		"pp": data.get("pp"),
		"priority": data.get("priority"),
		"damage_class": _get_name(data.get("damage_class")),
		"generation": _get_name(data.get("generation")),
		"effect": _get_english_text(data.get("effect_entries"), "effect"),
	}


def _collect_evolution_stages(
	chain: Any,
	stage: int,
	stage_names: dict[int, list[str]],
) -> None:
	"""Collect species names at each of the first three evolution stages."""
	if not isinstance(chain, dict) or stage > 3:
		return

	name = _get_name(chain.get("species"))
	if name and name not in stage_names[stage]:
		stage_names[stage].append(name)

	evolutions = chain.get("evolves_to", [])
	if isinstance(evolutions, list):
		for evolution in evolutions:
			_collect_evolution_stages(evolution, stage + 1, stage_names)


def extract_evolution_chain(data: dict[str, Any]) -> dict[str, Any]:
	"""Flatten an evolution chain into its first three stages."""
	stage_names = {1: [], 2: [], 3: []}
	_collect_evolution_stages(data.get("chain"), 1, stage_names)
	return {
		"chain_id": data.get("id"),
		"base_pokemon": ",".join(stage_names[1]),
		"stage_2": ",".join(stage_names[2]),
		"stage_3": ",".join(stage_names[3]),
	}


def save_csv(
	records: list[dict[str, Any]],
	file_path: Path,
	columns: list[str],
) -> pd.DataFrame:
	"""Clean records and save them as a UTF-8 CSV file."""
	dataframe = pd.DataFrame(records, columns=columns)
	for column in dataframe.columns:
		if dataframe[column].dtype == "object":
			dataframe[column] = dataframe[column].map(
				lambda value: clean_text(value) if isinstance(value, str) else value
			)

	dataframe = dataframe.drop_duplicates().reset_index(drop=True)
	file_path.parent.mkdir(parents=True, exist_ok=True)
	dataframe.to_csv(file_path, index=False, encoding="utf-8", na_rep="")
	return dataframe


def _process_resource(
	resource_name: str,
	output_name: str,
	columns: list[str],
	extractor: Callable[[dict[str, Any]], dict[str, Any]],
) -> pd.DataFrame:
	"""Load, extract, and save all files for one resource type."""
	input_dir = RAW_DATA_DIR / resource_name
	records: list[dict[str, Any]] = []
	for file_path in sorted(input_dir.glob("*.json")):
		try:
			records.append(extractor(load_json(file_path)))
		except (OSError, json.JSONDecodeError, ValueError) as error:
			print(f"Skipping {file_path}: {error}")
	return save_csv(records, PROCESSED_DATA_DIR / output_name, columns)


def process_pokemon() -> pd.DataFrame:
	"""Create data/processed/pokemon.csv from raw Pokémon JSON files."""
	return _process_resource("pokemon", "pokemon.csv", POKEMON_COLUMNS, extract_pokemon)


def process_species() -> pd.DataFrame:
	"""Create data/processed/species.csv from raw species JSON files."""
	return _process_resource("species", "species.csv", SPECIES_COLUMNS, extract_species)


def process_moves() -> pd.DataFrame:
	"""Create data/processed/moves.csv from raw move JSON files."""
	return _process_resource("moves", "moves.csv", MOVE_COLUMNS, extract_move)


def process_evolution_chains() -> pd.DataFrame:
	"""Create data/processed/evolution_chains.csv from raw chain JSON files."""
	return _process_resource(
		"evolution_chains",
		"evolution_chains.csv",
		EVOLUTION_CHAIN_COLUMNS,
		extract_evolution_chain,
	)


def main() -> None:
	"""Generate all processed CSV datasets."""
	processors = (
		("pokemon", process_pokemon),
		("species", process_species),
		("moves", process_moves),
		("evolution chains", process_evolution_chains),
	)
	for resource_name, processor in processors:
		dataframe = processor()
		print(f"Created {resource_name} CSV with {len(dataframe)} rows.")


if __name__ == "__main__":
	main()