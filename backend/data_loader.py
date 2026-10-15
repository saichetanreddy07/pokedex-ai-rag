"""Download generation-scoped raw resources from the PokéAPI."""

import json
import time
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

from backend.config import (
	POKEAPI_BASE_URL,
	POKEAPI_MAX_RETRIES,
	POKEAPI_TIMEOUT,
	TARGET_GENERATION,
)

RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def fetch_resource(url: str) -> dict[str, Any]:
	"""Fetch one JSON resource, retrying request failures."""
	last_error: Exception | None = None

	for attempt in range(POKEAPI_MAX_RETRIES):
		try:
			response = requests.get(url, timeout=POKEAPI_TIMEOUT)
			response.raise_for_status()
			payload = response.json()
			if not isinstance(payload, dict):
				raise ValueError("The API response must be a JSON object.")
			return payload
		except (requests.RequestException, ValueError) as error:
			last_error = error
			if attempt + 1 < POKEAPI_MAX_RETRIES:
				time.sleep(min(2**attempt, 5))

	raise RuntimeError(
		f"Failed to fetch {url} after {POKEAPI_MAX_RETRIES} attempts."
	) from last_error


def save_json(data: dict[str, Any], file_path: Path) -> None:
	"""Save a JSON object, creating its parent directory if needed."""
	file_path.parent.mkdir(parents=True, exist_ok=True)
	file_path.write_text(
		json.dumps(data, indent=2, ensure_ascii=False),
		encoding="utf-8",
	)


def _extract_id(url: str) -> int:
	"""Extract the numeric resource ID from a PokéAPI URL."""
	resource_id = url.rstrip("/").rsplit("/", 1)[-1]
	if not resource_id.isdecimal():
		raise ValueError(f"Invalid resource URL: {url}")
	return int(resource_id)


def _fetch_generation_species(generation_id: int) -> dict[int, str]:
	"""Return species IDs and names listed for one generation."""
	generation = fetch_resource(
		f"{POKEAPI_BASE_URL}/generation/{generation_id}"
	)
	species = generation.get("pokemon_species")
	if not isinstance(species, list):
		raise ValueError(
			f"Invalid Pokémon species list for generation {generation_id}."
		)

	species_names: dict[int, str] = {}
	for item in species:
		if not isinstance(item, dict):
			raise ValueError("Invalid species entry in generation response.")
		url = item.get("url")
		name = item.get("name")
		if not isinstance(url, str) or not isinstance(name, str):
			raise ValueError("Generation response contains an invalid species.")
		species_names[_extract_id(url)] = name

	return species_names


def _resource_file_path(
	folder_name: str,
	resource_id: int,
	name: str,
	include_name: bool,
) -> Path:
	"""Build a raw resource's filename using the existing naming convention."""
	filename = f"{resource_id}_{name}.json" if include_name else f"{resource_id}.json"
	return RAW_DATA_DIR / folder_name / filename


def _read_json(file_path: Path) -> dict[str, Any] | None:
	"""Read a saved JSON object, reporting unreadable or invalid files."""
	try:
		payload = json.loads(file_path.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError) as error:
		tqdm.write(f"Could not read {file_path}: {error}")
		return None

	if not isinstance(payload, dict):
		tqdm.write(f"Could not read {file_path}: expected a JSON object.")
		return None
	return payload


def _download_resources(
	resource_names: dict[int, str],
	resource_endpoint: str,
	folder_name: str,
	include_name: bool = True,
) -> tuple[int, int, int]:
	"""Download selected resource IDs and return downloaded, skipped, failed counts."""
	output_dir = RAW_DATA_DIR / folder_name
	output_dir.mkdir(parents=True, exist_ok=True)
	downloaded = 0
	skipped = 0
	failed = 0

	with tqdm(resource_names.items(), desc=f"Downloading {folder_name}") as progress:
		for resource_id, name in progress:
			file_path = _resource_file_path(
				folder_name, resource_id, name, include_name
			)
			if file_path.exists() and _read_json(file_path) is not None:
				skipped += 1
				continue

			detail_url = f"{POKEAPI_BASE_URL}/{resource_endpoint}/{resource_id}"
			try:
				save_json(fetch_resource(detail_url), file_path)
				downloaded += 1
			except (OSError, RuntimeError) as error:
				failed += 1
				tqdm.write(f"Failed to download {detail_url}: {error}")

	return downloaded, skipped, failed


def download_species(species_names: dict[int, str]) -> tuple[int, int, int]:
	"""Download selected Pokémon species into data/raw/species."""
	return _download_resources(
		species_names, "pokemon-species", "species"
	)


def download_pokemon(species_names: dict[int, str]) -> tuple[int, int, int]:
	"""Download the selected species' Pokémon into data/raw/pokemon."""
	return _download_resources(species_names, "pokemon", "pokemon")


def _collect_move_names(species_names: dict[int, str]) -> dict[int, str]:
	"""Collect unique move IDs and names from saved Pokémon resources."""
	move_names: dict[int, str] = {}
	for pokemon_id, pokemon_name in species_names.items():
		file_path = _resource_file_path(
			"pokemon", pokemon_id, pokemon_name, include_name=True
		)
		pokemon = _read_json(file_path)
		if pokemon is None:
			continue

		moves = pokemon.get("moves")
		if not isinstance(moves, list):
			tqdm.write(f"No valid moves list found in {file_path}.")
			continue
		for item in moves:
			move = item.get("move") if isinstance(item, dict) else None
			url = move.get("url") if isinstance(move, dict) else None
			name = move.get("name") if isinstance(move, dict) else None
			if isinstance(url, str) and isinstance(name, str):
				move_names[_extract_id(url)] = name

	return move_names


def download_moves(move_names: dict[int, str]) -> tuple[int, int, int]:
	"""Download only moves referenced by the selected Pokémon."""
	return _download_resources(move_names, "move", "moves")


def _collect_evolution_chain_ids(species_names: dict[int, str]) -> set[int]:
	"""Collect unique evolution chain IDs from saved species resources."""
	chain_ids: set[int] = set()
	for species_id, species_name in species_names.items():
		file_path = _resource_file_path(
			"species", species_id, species_name, include_name=True
		)
		species = _read_json(file_path)
		if species is None:
			continue

		evolution_chain = species.get("evolution_chain")
		url = (
			evolution_chain.get("url")
			if isinstance(evolution_chain, dict)
			else None
		)
		if isinstance(url, str):
			chain_ids.add(_extract_id(url))

	return chain_ids


def download_evolution_chains(chain_ids: set[int]) -> tuple[int, int, int]:
	"""Download only evolution chains referenced by the selected species."""
	chain_names = {chain_id: "" for chain_id in sorted(chain_ids)}
	return _download_resources(
		chain_names, "evolution-chain", "evolution_chains", include_name=False
	)


def download_generation_data(generation_id: int) -> None:
	"""Download species, Pokémon, referenced moves, and evolution chains."""
	species_names = _fetch_generation_species(generation_id)
	if not species_names:
		raise ValueError(f"No Pokémon species found for generation {generation_id}.")

	print(f"Generation {generation_id}: {len(species_names)} species selected")
	for resource_name, downloader in (
		("species", download_species),
		("pokemon", download_pokemon),
	):
		_downloaded, _skipped, _failed = downloader(species_names)
		print(
			f"{resource_name}: {_downloaded} downloaded, "
			f"{_skipped} skipped, {_failed} failed"
		)

	move_names = _collect_move_names(species_names)
	print(f"{len(move_names)} unique moves referenced")
	_downloaded, _skipped, _failed = download_moves(move_names)
	print(
		f"moves: {_downloaded} downloaded, "
		f"{_skipped} skipped, {_failed} failed"
	)

	chain_ids = _collect_evolution_chain_ids(species_names)
	print(f"{len(chain_ids)} unique evolution chains referenced")
	_downloaded, _skipped, _failed = download_evolution_chains(chain_ids)
	print(
		f"evolution chains: {_downloaded} downloaded, "
		f"{_skipped} skipped, {_failed} failed"
	)


def main() -> None:
	"""Download the resources for the configured target generation."""
	try:
		download_generation_data(TARGET_GENERATION)
	except (RuntimeError, ValueError) as error:
		print(f"Could not download generation {TARGET_GENERATION}: {error}")


if __name__ == "__main__":
	main()