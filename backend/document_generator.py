"""Generate semantic-search documents from processed Pokémon CSV files."""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
	content: str,
	metadata: dict[str, object],
) -> dict[str, object]:
	"""Build a document with a consistent shape and nonempty metadata."""
	clean_metadata = {
		key: value
		for key, value in metadata.items()
		if value is not None and value != "" and value != []
	}
	return {
		"id": document_id,
		"resource": resource,
		"title": title,
		"content": " ".join(content.split()),
		"metadata": clean_metadata,
	}


def _pokemon_document(row: pd.Series) -> dict[str, object] | None:
	"""Build one Pokémon document from a merged CSV row."""
	pokemon_id = _clean_value(row.get("id"))
	if not pokemon_id:
		return None

	name = _clean_value(row.get("name_pokemon"))
	if not name:
		name = _clean_value(row.get("name_species")) or f"Pokemon {pokemon_id}"
	title = name.replace("-", " ").title()
	types = _split_values(row.get("types"))
	abilities = _split_values(row.get("abilities"))
	moves = _split_values(row.get("moves"))
	description = _clean_value(row.get("description"))
	generation = _clean_value(row.get("generation"))

	if types:
		content_parts = [
			f"{title} is a {', '.join(types)} type Pokémon."
		]
	else:
		content_parts = [f"{title} is a Pokémon."]
	if description:
		content_parts.append(description)
	if generation:
		content_parts.append(f"It belongs to {generation}.")
	if abilities:
		content_parts.append(f"Its abilities include {', '.join(abilities)}.")

	stats = []
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
			stats.append(f"{label} {value}")
	if stats:
		content_parts.append(f"Its base stats are {', '.join(stats)}.")

	for column, label, suffix in (
		("height", "Height", " decimeters"),
		("weight", "Weight", " hectograms"),
		("base_experience", "Base experience", " points"),
	):
		_append_detail(content_parts, label, row.get(column), suffix)
	if moves:
		content_parts.append(f"It can learn moves such as {', '.join(moves)}.")

	legendary = _clean_value(row.get("is_legendary")).lower()
	mythical = _clean_value(row.get("is_mythical")).lower()
	if legendary in {"true", "false"}:
		content_parts.append(
			"It is legendary." if legendary == "true" else "It is not legendary."
		)
	if mythical in {"true", "false"}:
		content_parts.append(
			"It is mythical." if mythical == "true" else "It is not mythical."
		)

	metadata: dict[str, object] = {"pokemon_id": pokemon_id}
	if generation:
		metadata["generation"] = generation
	if types:
		metadata["types"] = types
	if abilities:
		metadata["abilities"] = abilities
	if legendary in {"true", "false"}:
		metadata["is_legendary"] = legendary == "true"
	if mythical in {"true", "false"}:
		metadata["is_mythical"] = mythical == "true"

	return _build_document(
		f"pokemon-{pokemon_id}",
		"pokemon",
		title,
		" ".join(content_parts),
		metadata,
	)


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
	documents = []
	for _, row in merged.iterrows():
		document = _pokemon_document(row)
		if document is not None:
			documents.append(document)
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