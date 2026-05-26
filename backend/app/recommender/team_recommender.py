import json

from pathlib import Path

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Pokémon dataset path
POKEMON_PATH = (
    BASE_DIR /
    "data" /
    "raw" /
    "pokemon_raw.json"
)

# Load Pokémon dataset
with open(
    POKEMON_PATH,
    "r",
    encoding="utf-8"
) as f:

    pokemon_data = json.load(f)

# Simple Pokémon type counter chart
TYPE_COUNTERS = {

    "fire": ["water", "rock"],

    "water": ["electric", "grass"],

    "grass": ["fire", "ice"],

    "electric": ["ground"],

    "rock": ["water", "grass"],

    "psychic": ["bug", "ghost"],

    "ghost": ["ghost", "dark"],

    "dragon": ["ice"],

    "ground": ["water", "grass"],

    "ice": ["fire", "rock"],

    "fighting": ["psychic"],

    "poison": ["ground"],

    "bug": ["fire", "rock"],

    "flying": ["electric", "rock"]
}

# Recommend Pokémon based on type
def recommend_by_type(pokemon_type):

    recommendations = []

    for pokemon in pokemon_data:

        if pokemon_type.lower() in pokemon["types"]:

            recommendations.append({

                "name": pokemon["name"],

                "types": pokemon["types"],

                "abilities": pokemon["abilities"],

                "stats": pokemon["stats"]
            })

    return recommendations[:5]

# Create a balanced team with diverse types
# Create a balanced team using stronger Pokémon
def build_balanced_team():

    team = []

    used_types = set()

    # Sort Pokémon by total stats
    sorted_pokemon = sorted(

        pokemon_data,

        key=lambda pokemon: sum(
            pokemon["stats"].values()
        ),

        reverse=True
    )

    for pokemon in sorted_pokemon:

        pokemon_types = pokemon["types"]

        # Avoid too many repeated types
        if not used_types.intersection(
            pokemon_types
        ):

            team.append({

                "name": pokemon["name"],

                "types": pokemon_types,

                "abilities": pokemon["abilities"],

                "stats": pokemon["stats"]
            })

            used_types.update(
                pokemon_types
            )

        # Standard team size
        if len(team) == 6:
            break

    return team

# Recommend counters against a specific type
def recommend_counters(enemy_type):

    counter_types = TYPE_COUNTERS.get(
        enemy_type.lower(),
        []
    )

    counters = []

    for pokemon in pokemon_data:

        if any(
            pokemon_type in counter_types
            for pokemon_type in pokemon["types"]
        ):

            counters.append({

                "name": pokemon["name"],

                "types": pokemon["types"],

                "abilities": pokemon["abilities"],

                "stats": pokemon["stats"]
            })

    return counters[:5]

# Compare two Pokémon using total stats
def compare_pokemon(pokemon_1, pokemon_2):

    first_pokemon = None
    second_pokemon = None

    for pokemon in pokemon_data:

        if pokemon["name"].lower() == pokemon_1.lower():

            first_pokemon = pokemon

        if pokemon["name"].lower() == pokemon_2.lower():

            second_pokemon = pokemon

    # Pokémon not found
    if not first_pokemon or not second_pokemon:

        return "Could not find both Pokémon."

    # Calculate total stats
    first_total = sum(
        first_pokemon["stats"].values()
    )

    second_total = sum(
        second_pokemon["stats"].values()
    )

    # Decide stronger Pokémon
    if first_total > second_total:

        winner = first_pokemon["name"]

    elif second_total > first_total:

        winner = second_pokemon["name"]

    else:

        winner = "Both Pokémon are equally strong"

    response = f"""
Comparison Result:

{first_pokemon['name'].title()} Total Stats: {first_total}

{second_pokemon['name'].title()} Total Stats: {second_total}

Stronger Pokémon:
{winner.title()}
"""

    return response