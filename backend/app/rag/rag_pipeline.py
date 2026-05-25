from backend.app.rag.retriever import retrieve_documents
from backend.app.rag.generator import generate_response

# Main RAG pipeline
def ask_pokedex(query):

    # Retrieve relevant Pokémon documents
    results = retrieve_documents(query)

    documents = results["documents"][0]

    # Combine retrieved documents into context
    context = "\n\n".join(documents)

    # Generate grounded AI response
    answer = generate_response(
        query=query,
        context=context
    )

    return answer