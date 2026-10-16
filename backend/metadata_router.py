"""Build ChromaDB metadata filters from parsed query intent."""

from backend.query_parser import ParsedQuery


def _combine_filters(filters: list[dict[str, object]]) -> dict[str, object] | None:
	"""Join metadata conditions using ChromaDB's supported where operators."""
	if not filters:
		return None
	if len(filters) == 1:
		return filters[0]
	return {"$and": filters}


def build_metadata_filter(parsed_query: ParsedQuery) -> dict[str, object] | None:
	"""Build a pre-search filter using metadata fields present in the index."""
	filters: list[dict[str, object]] = []
	if parsed_query.document_type:
		filters.append({"document_type": parsed_query.document_type})

	if parsed_query.document_type == "evolution_chain":
		chain_ids = sorted(
			{
				pokemon.evolution_chain_id
				for pokemon in parsed_query.pokemon
				if pokemon.evolution_chain_id
			}
		)
		if len(chain_ids) == 1:
			filters.append({"chain_id": chain_ids[0]})
		elif chain_ids:
			filters.append(
				{"$or": [{"chain_id": chain_id} for chain_id in chain_ids]}
			)
		# Evolution-chain records have no Pokémon or generation metadata.
		return _combine_filters(filters)

	pokemon_names = sorted({pokemon.pokemon for pokemon in parsed_query.pokemon})
	if len(pokemon_names) == 1:
		filters.append({"pokemon": pokemon_names[0]})
	elif pokemon_names:
		filters.append(
			{"$or": [{"pokemon": name} for name in pokemon_names]}
		)
	if parsed_query.generation:
		filters.append({"generation": parsed_query.generation})
	return _combine_filters(filters)
