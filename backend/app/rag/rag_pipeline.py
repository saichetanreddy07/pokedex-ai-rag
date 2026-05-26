from backend.app.rag.retriever import retrieve_documents
from backend.app.rag.generator import generate_response

from backend.app.recommender.team_recommender import (
    recommend_by_type,
    build_balanced_team,
    recommend_counters,
    compare_pokemon
)

# Main Pokémon AI pipeline
def ask_pokedex(query):

    query_lower = query.lower()

    pokemon_types = [
        "fire",
        "water",
        "grass",
        "electric",
        "rock",
        "psychic",
        "ghost",
        "dragon",
        "ice",
        "ground",
        "flying",
        "bug",
        "poison",
        "fighting"
    ]

    # Build a balanced Pokémon team
    if (
        "balanced team" in query_lower
        or "build me a team" in query_lower
    ):

        team = build_balanced_team()

        response = "Recommended Balanced Pokémon Team:\n\n"

        for pokemon in team:

            response += (
                f"- {pokemon['name'].title()} "
                f"({', '.join(pokemon['types'])})\n"
            )

        return response

    # Recommend Pokémon based on type
    if "recommend" in query_lower:

        for pokemon_type in pokemon_types:

            if pokemon_type in query_lower:

                recommendations = recommend_by_type(
                    pokemon_type
                )

                response = (
                    f"Recommended "
                    f"{pokemon_type.title()} Pokémon:\n\n"
                )

                for pokemon in recommendations:

                    response += (
                        f"- {pokemon['name'].title()} "
                        f"({', '.join(pokemon['types'])})\n"
                    )

                return response

    # Suggest counters against a Pokémon type
    if (
        "counter" in query_lower
        or "weak against" in query_lower
    ):

        for pokemon_type in pokemon_types:

            if pokemon_type in query_lower:

                counters = recommend_counters(
                    pokemon_type
                )

                response = (
                    f"Recommended Counters Against "
                    f"{pokemon_type.title()} Pokémon:\n\n"
                )

                for pokemon in counters:

                    response += (
                        f"- {pokemon['name'].title()} "
                        f"({', '.join(pokemon['types'])})\n"
                    )

                return response

    # Compare two Pokémon
    if (
        "stronger" in query_lower
        or "compare" in query_lower
        or "vs" in query_lower
    ):

        pokemon_names = []

        for pokemon_type in pokemon_types:

            recommendations = recommend_by_type(
                pokemon_type
            )

            for pokemon in recommendations:

                pokemon_name = pokemon["name"]

                if pokemon_name.lower() in query_lower:

                    pokemon_names.append(
                        pokemon_name
                    )

        # Remove duplicates
        pokemon_names = list(
            set(pokemon_names)
        )

        # Compare first two Pokémon found
        if len(pokemon_names) >= 2:

            return compare_pokemon(
                pokemon_names[0],
                pokemon_names[1]
            )

    # Default RAG-based chatbot
    results = retrieve_documents(query)

    documents = results["documents"][0]

    # Combine retrieved documents into context
    context = "\n\n".join(documents)

    # Generate final AI response
    answer = generate_response(
        query=query,
        context=context
    )

    return answer