from backend.app.recommender.team_recommender import (
    recommend_by_type,
    build_balanced_team,
    recommend_counters
)

# Test type recommendations
print("\nElectric Type Pokémon:\n")

electric_pokemon = recommend_by_type(
    "electric"
)

for pokemon in electric_pokemon:

    print(pokemon)

# Test balanced team generation
print("\nBalanced Team:\n")

balanced_team = build_balanced_team()

for pokemon in balanced_team:

    print(pokemon)

# Test counter recommendations
print("\nCounters Against Fire Pokémon:\n")

fire_counters = recommend_counters(
    "fire"
)

for pokemon in fire_counters:

    print(pokemon)