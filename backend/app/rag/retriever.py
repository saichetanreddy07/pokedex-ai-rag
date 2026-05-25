import chromadb

from pathlib import Path

from backend.app.rag.embeddings import generate_embedding

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ChromaDB storage path
CHROMA_PATH = (
    BASE_DIR /
    "data" /
    "chroma_db"
)

# Connect to persistent ChromaDB database
client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

# Load Pokémon RAG collection
collection = client.get_collection(
    name="pokemon_rag"
)

# Retrieve relevant Pokémon documents
def retrieve_documents(
    query,
    n_results=5
):

    # Generate embedding for user query
    query_embedding = generate_embedding(query)

    # Perform semantic vector search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return results