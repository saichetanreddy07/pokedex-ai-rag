import requests
import json

from tqdm import tqdm

# Store Pokémon species/lore data
species_data = []

# Fetch first 151 Pokémon species
for pokemon_id in tqdm(range(1, 152)):

    response = requests.get(
        f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
    )

    if response.status_code == 200:

        data = response.json()

        # Get English Pokédex entry
        flavor_text = ""

        for entry in data["flavor_text_entries"]:

            if entry["language"]["name"] == "en":

                flavor_text = entry["flavor_text"]
                break

        # Extract useful species information
        species_info = {

            "name": data["name"],

            "habitat": (
                data["habitat"]["name"]
                if data["habitat"]
                else None
            ),

            "legendary": data["is_legendary"],

            "mythical": data["is_mythical"],

            "flavor_text": flavor_text
        }

        species_data.append(species_info)

# Save species dataset
with open(
    "../../../data/raw/pokemon_species.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        species_data,
        f,
        indent=2,
        ensure_ascii=False
    )

print("Pokémon species and lore data saved successfully!")