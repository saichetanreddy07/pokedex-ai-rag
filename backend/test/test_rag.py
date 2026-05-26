from backend.app.rag.rag_pipeline import ask_pokedex

query = "Who is Pikachu?"

response = ask_pokedex(query)

print("\nQUESTION:")
print(query)

print("\nANSWER:")
print(response)