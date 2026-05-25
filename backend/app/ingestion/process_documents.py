import json

from pathlib import Path

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# File paths
RAW_POKEMON_PATH = (
    BASE_DIR /
    "data" /
    "raw" /
    "pokemon_raw.json"
)

RAW_SPECIES_PATH = (
    BASE_DIR /
    "data" /
    "raw" /
    "pokemon_species.json"
)

PROCESSED_PATH = (
    BASE_DIR /
    "data" /
    "processed" /
    "pokemon_documents.json"
)

# Load raw Pokémon datasets
with open(
    RAW_POKEMON_PATH,
    "r",
    encoding="utf-8"
) as f:

    pokemon_data = json.load(f)

with open(
    RAW_SPECIES_PATH,
    "r",
    encoding="utf-8"
) as f:

    species_data = json.load(f)

# Create quick lookup for species info
species_lookup = {
    pokemon["name"]: pokemon
    for pokemon in species_data
}

# Store processed RAG documents
documents = []

# Process each Pokémon
for pokemon in pokemon_data:

    name = pokemon["name"]

    # Get matching species data
    species_info = species_lookup.get(
        name,
        {}
    )

    # Extract lore-related information
    lore_text = species_info.get(
        "flavor_text",
        ""
    )

    habitat = species_info.get(
        "habitat",
        "unknown"
    )

    legendary = species_info.get(
        "legendary",
        False
    )

    mythical = species_info.get(
        "mythical",
        False
    )

    # Extract battle stats
    stats = pokemon["stats"]

    hp = stats.get("hp", 0)
    attack = stats.get("attack", 0)
    defense = stats.get("defense", 0)

    special_attack = stats.get(
        "special-attack",
        0
    )

    special_defense = stats.get(
        "special-defense",
        0
    )

    speed = stats.get("speed", 0)

    # Keep only common moves
    common_moves = pokemon["moves"][:10]

    # Create semantic RAG document
    document_text = f"""
Pokémon Name: {name}

Pokémon Types:
{", ".join(pokemon["types"])}

Abilities:
{", ".join(pokemon["abilities"])}

Base Stats:
HP: {hp}
Attack: {attack}
Defense: {defense}
Special Attack: {special_attack}
Special Defense: {special_defense}
Speed: {speed}

Common Moves:
{", ".join(common_moves)}

Habitat:
{habitat}

Legendary Status:
{legendary}

Mythical Status:
{mythical}

Pokédex Lore:
{lore_text}
"""

    # Save document and metadata
    documents.append({
        "text": document_text,

        "metadata": {
            "name": name,
            "types": pokemon["types"],
            "habitat": habitat,
            "legendary": legendary,
            "mythical": mythical
        }
    })

# Save processed RAG documents
with open(
    PROCESSED_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        documents,
        f,
        indent=2,
        ensure_ascii=False
    )

print("Processed RAG documents created successfully!")
print(f"Total documents created: {len(documents)}")