import chromadb

# Connect to local ChromaDB storage
client = chromadb.PersistentClient(
    path="../../../data/chroma_db"
)

# Create collection if it doesn't exist
collection = client.get_or_create_collection(
    name="pokemon_rag"
)

print("ChromaDB collection is ready!")