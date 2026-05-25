from backend.app.rag.retriever import retrieve_documents

text = "Pikachu is an electric Pokémon"

embedding = generate_embedding(text)

print(type(embedding))
print(len(embedding))
print(embedding[:10])