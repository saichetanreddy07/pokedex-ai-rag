import requests
import json

from tqdm import tqdm

# PokéAPI endpoint
BASE_URL = "https://pokeapi.co/api/v2/pokemon"

# Store all Pokémon data
pokemon_data = []

# Fetch first 151 Pokémon
for pokemon_id in tqdm(range(1, 152)):

    response = requests.get(
        f"{BASE_URL}/{pokemon_id}"
    )

    if response.status_code == 200:

        data = response.json()

        # Extract important Pokémon information
        pokemon_info = {

            "id": data["id"],

            "name": data["name"],

            "types": [
                pokemon_type["type"]["name"]
                for pokemon_type in data["types"]
            ],

            "abilities": [
                ability["ability"]["name"]
                for ability in data["abilities"]
            ],

            "stats": {
                stat["stat"]["name"]: stat["base_stat"]
                for stat in data["stats"]
            },

            "moves": [
                move["move"]["name"]
                for move in data["moves"][:20]
            ]
        }

        pokemon_data.append(pokemon_info)

# Save raw Pokémon dataset
with open(
    "../../../data/raw/pokemon_raw.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        pokemon_data,
        f,
        indent=2,
        ensure_ascii=False
    )

print("Pokémon data saved successfully!")