"""Generate semantic-search documents from processed Pokémon CSV files."""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_POKEMON_DIR = PROJECT_ROOT / "data" / "raw" / "pokemon"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"


def _read_csv(file_name: str, id_column: str) -> pd.DataFrame:
	"""Read a processed CSV while preserving resource IDs as strings."""
	file_path = PROCESSED_DATA_DIR / file_name
	if not file_path.is_file():
		raise FileNotFoundError(f"Processed CSV not found: {file_path}")
	return pd.read_csv(file_path, dtype={id_column: "string"})


def _clean_value(value: object) -> str:
	"""Convert a CSV value to clean text, treating missing values as empty."""
	if pd.isna(value):
		return ""
	if isinstance(value, float) and value.is_integer():
		return str(int(value))
	return " ".join(str(value).split())


def _split_values(value: object) -> list[str]:
	"""Split a comma-separated CSV value into nonempty items."""
	cleaned_value = _clean_value(value)
	return [item.strip() for item in cleaned_value.split(",") if item.strip()]


def _append_detail(
	details: list[str],
	label: str,
	value: object,
	suffix: str = "",
) -> None:
	"""Append a labeled sentence when its value is present."""
	cleaned_value = _clean_value(value)
	if cleaned_value:
		details.append(f"{label}: {cleaned_value}{suffix}.")


def _build_document(
	document_id: str,
	resource: str,
	title: str,
	document_type: str,
	content: str,
	metadata: dict[str, object],
) -> dict[str, object]:
	"""Build a document with a consistent shape and nonempty metadata."""
	metadata["document_type"] = document_type
	clean_metadata = {
		key: value
		for key, value in metadata.items()
		if value is not None and value != "" and value != []
	}
	return {
		"id": document_id,
		"resource": resource,
		"title": title,
		"document_type": document_type,
		"content": "\n".join(
			" ".join(line.split()) for line in content.splitlines()
		).strip(),
		"metadata": clean_metadata,
	}


def _read_abilities(
	pokemon_id: str,
	pokemon_name: str,
	fallback_abilities: object,
) -> tuple[list[str], list[str]]:
	"""Separate normal and hidden abilities using raw Pokémon data."""
	file_path = RAW_POKEMON_DIR / f"{pokemon_id}_{pokemon_name}.json"
	if file_path.is_file():
		try:
			with file_path.open(encoding="utf-8") as json_file:
				pokemon_data = json.load(json_file)
		except (OSError, json.JSONDecodeError) as error:
			print(f"Could not read abilities from {file_path}: {error}")
		else:
			entries = pokemon_data.get("abilities")
			if isinstance(entries, list):
				normal_abilities = []
				hidden_abilities = []
				for entry in entries:
					if not isinstance(entry, dict):
						continue
					ability = entry.get("ability")
					ability_name = (
						_clean_value(ability.get("name"))
						if isinstance(ability, dict)
						else ""
					)
					if not ability_name:
						continue
					if entry.get("is_hidden") is True:
						hidden_abilities.append(ability_name)
					else:
						normal_abilities.append(ability_name)
				return list(dict.fromkeys(normal_abilities)), list(
					dict.fromkeys(hidden_abilities)
				)
	return _split_values(fallback_abilities), []


def _pokemon_slug(name: str) -> str:
	"""Return a stable lowercase Pokémon name for descriptive document IDs."""
	return "-".join(name.lower().split())


def _make_pokemon_document(
	pokemon_id: str,
	pokemon_name: str,
	generation: str,
	document_type: str,
	content: str,
	metadata: dict[str, object] | None = None,
) -> dict[str, object]:
	"""Build one focused Pokémon document with shared metadata."""
	display_name = pokemon_name.replace("-", " ").title()
	document_metadata: dict[str, object] = {
		"pokemon": pokemon_name,
		"pokemon_id": pokemon_id,
	}
	if generation:
		document_metadata["generation"] = generation
	if metadata:
		document_metadata.update(metadata)
	return _build_document(
		f"pokemon_{_pokemon_slug(pokemon_name)}_{document_type}",
		"pokemon",
		f"Pokemon: {display_name} - {document_type.title()}",
		document_type,
		content,
		document_metadata,
	)


def _boolean_value(value: object) -> bool | None:
	"""Parse a boolean-like CSV value when it is present."""
	cleaned_value = _clean_value(value).lower()
	if cleaned_value == "true":
		return True
	if cleaned_value == "false":
		return False
	return None


def _pokemon_section_content(
	pokemon_name: str,
	section_title: str,
	items: list[str],
	use_bullets: bool = True,
) -> str:
	"""Format a Pokémon knowledge section with a consistent leading name."""
	lines = [f"Pokemon: {pokemon_name}", "", f"{section_title}:"]
	if items:
		if use_bullets:
			lines.extend(f"- {item}" for item in items)
		else:
			lines.extend(items)
	else:
		lines.append("Information unavailable.")
	return "\n".join(lines)


def _pokemon_documents(row: pd.Series) -> list[dict[str, object]]:
	"""Build six focused documents from one merged Pokémon CSV row."""
	pokemon_id = _clean_value(row.get("id"))
	if not pokemon_id:
		return []

	name = _clean_value(row.get("name_pokemon"))
	if not name:
		name = _clean_value(row.get("name_species")) or f"Pokemon {pokemon_id}"
	display_name = name.replace("-", " ").title()
	types = _split_values(row.get("types"))
	description = _clean_value(row.get("description"))
	generation = _clean_value(row.get("generation"))
	documents: list[dict[str, object]] = []

	overview_items = []
	if description:
		overview_items.append(f"Pokédex Description: {description}")
	if generation:
		overview_items.append(f"Generation: {generation}")
	legendary = _boolean_value(row.get("is_legendary"))
	mythical = _boolean_value(row.get("is_mythical"))
	if legendary is not None and mythical is not None:
		if legendary and mythical:
			status = "Legendary and mythical"
		elif legendary:
			status = "Legendary, not mythical"
		elif mythical:
			status = "Mythical, not legendary"
		else:
			status = "Neither legendary nor mythical"
		overview_items.append(f"Status: {status}")
	elif legendary is not None:
		overview_items.append(
			"Status: Legendary" if legendary else "Status: Not legendary"
		)
	elif mythical is not None:
		overview_items.append("Status: Mythical" if mythical else "Status: Not mythical")
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"overview",
			_pokemon_section_content(display_name, "Overview", overview_items),
			{
				key: value
				for key, value in (
					("is_legendary", legendary),
					("is_mythical", mythical),
				)
				if value is not None
			},
		)
	)

	type_items = [type_name.replace("-", " ").title() for type_name in types]
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"types",
			_pokemon_section_content(display_name, "Types", type_items),
			{"types": types} if types else None,
		)
	)

	normal_abilities, hidden_abilities = _read_abilities(
		pokemon_id, name, row.get("abilities")
	)
	ability_items = [
		ability.replace("-", " ").title() for ability in normal_abilities
	]
	ability_items.extend(
		f"{ability.replace('-', ' ').title()} (Hidden Ability)"
		for ability in hidden_abilities
	)
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"abilities",
			_pokemon_section_content(display_name, "Abilities", ability_items),
			{
				"normal_abilities": normal_abilities,
				"hidden_ability": hidden_abilities,
			},
		)
	)

	stats = []
	stat_metadata = {}
	for column, label in (
		("hp", "HP"),
		("attack", "Attack"),
		("defense", "Defense"),
		("special_attack", "Special Attack"),
		("special_defense", "Special Defense"),
		("speed", "Speed"),
	):
		value = _clean_value(row.get(column))
		if value:
			stats.append(f"{label}: {value}")
			stat_metadata[column] = value
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"stats",
			_pokemon_section_content(
				display_name, "Base Stats", stats, use_bullets=False
			),
			stat_metadata or None,
		)
	)

	physical_parts = []
	physical_metadata = {}
	for column, label, suffix in (
		("height", "Height", " decimeters"),
		("weight", "Weight", " hectograms"),
		("base_experience", "Base experience", " points"),
	):
		value = _clean_value(row.get(column))
		if value:
			physical_label = label.replace("base experience", "Base Experience")
			physical_parts.append(f"{physical_label}: {value}{suffix}")
			physical_metadata[column] = value
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"physical",
			_pokemon_section_content(
				display_name, "Physical", physical_parts, use_bullets=False
			),
			physical_metadata or None,
		)
	)

	moves = _split_values(row.get("moves"))
	move_items = [move.replace("-", " ").title() for move in moves]
	documents.append(
		_make_pokemon_document(
			pokemon_id,
			name,
			generation,
			"moves",
			_pokemon_section_content(display_name, "Learnable Moves", move_items),
			{"moves": moves} if moves else None,
		)
	)
	return documents


def _move_document(row: pd.Series) -> dict[str, object] | None:
	"""Build one move document from a CSV row."""
	move_id = _clean_value(row.get("id"))
	if not move_id:
		return None

	name = _clean_value(row.get("name")) or f"Move {move_id}"
	title = name.replace("-", " ").title()
	move_type = _clean_value(row.get("type"))
	content_parts = [
		f"{title} is a {move_type} type Pokémon move."
		if move_type
		else f"{title} is a Pokémon move."
	]
	for column, label, suffix in (
		("power", "Power", ""),
		("accuracy", "Accuracy", "%"),
		("pp", "PP", ""),
		("priority", "Priority", ""),
		("damage_class", "Damage class", ""),
		("generation", "Introduced in", ""),
		("effect", "Effect", ""),
	):
		_append_detail(content_parts, label, row.get(column), suffix)

	metadata: dict[str, object] = {"move_id": move_id}
	for column in ("type", "damage_class", "generation"):
		value = _clean_value(row.get(column))
		if value:
			metadata[column] = value

	return _build_document(
		f"move-{move_id}",
		"move",
		title,
		"move",
		" ".join(content_parts),
		metadata,
	)


def _evolution_document(row: pd.Series) -> dict[str, object] | None:
	"""Build one readable document for an evolution chain."""
	chain_id = _clean_value(row.get("chain_id"))
	if not chain_id:
		return None

	base_pokemon = _split_values(row.get("base_pokemon"))
	stage_2 = _split_values(row.get("stage_2"))
	stage_3 = _split_values(row.get("stage_3"))
	content_parts = []
	if base_pokemon:
		content_parts.append(
			f"Evolution chain {chain_id} begins with {', '.join(base_pokemon)}."
		)
	if stage_2:
		content_parts.append(
			f"The next stage includes {', '.join(stage_2)}."
		)
	if stage_3:
		content_parts.append(
			f"A further evolution can become {', '.join(stage_3)}."
		)
	if not content_parts:
		content_parts.append(f"Evolution chain {chain_id} has no listed stages.")

	return _build_document(
		f"evolution-chain-{chain_id}",
		"evolution_chain",
		f"Evolution Chain {chain_id}",
		"evolution_chain",
		" ".join(content_parts),
		{"chain_id": chain_id},
	)


def _save_documents(documents: list[dict[str, object]], file_name: str) -> None:
	"""Save a list of documents as UTF-8 JSON."""
	DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
	output_path = DOCUMENTS_DIR / file_name
	with output_path.open("w", encoding="utf-8") as output_file:
		json.dump(documents, output_file, ensure_ascii=False, indent=2)
	print(f"Created {output_path} with {len(documents)} documents.")


def generate_pokemon_documents() -> list[dict[str, object]]:
	"""Merge Pokémon and species CSVs and create Pokémon documents."""
	pokemon = _read_csv("pokemon.csv", "id")
	species = _read_csv("species.csv", "id")
	merged = pokemon.merge(
		species,
		on="id",
		how="left",
		suffixes=("_pokemon", "_species"),
	)
	documents: list[dict[str, object]] = []
	for _, row in merged.iterrows():
		documents.extend(_pokemon_documents(row))
	return documents


def generate_move_documents() -> list[dict[str, object]]:
	"""Create one document for every processed move."""
	moves = _read_csv("moves.csv", "id")
	documents = []
	for _, row in moves.iterrows():
		document = _move_document(row)
		if document is not None:
			documents.append(document)
	return documents


def generate_evolution_documents() -> list[dict[str, object]]:
	"""Create one document for every processed evolution chain."""
	chains = _read_csv("evolution_chains.csv", "chain_id")
	documents = []
	for _, row in chains.iterrows():
		document = _evolution_document(row)
		if document is not None:
			documents.append(document)
	return documents


def main() -> None:
	"""Generate all knowledge-document JSON files."""
	outputs = (
		(generate_pokemon_documents, "pokemon_documents.json"),
		(generate_move_documents, "move_documents.json"),
		(generate_evolution_documents, "evolution_documents.json"),
	)
	for generator, file_name in outputs:
		_save_documents(generator(), file_name)


if __name__ == "__main__":
	main()