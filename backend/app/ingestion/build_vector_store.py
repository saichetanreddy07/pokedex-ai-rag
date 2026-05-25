import json
import chromadb

from pathlib import Path

from backend.app.rag.embeddings import generate_embedding

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# File locations
DOCUMENTS_PATH = (
    BASE_DIR /
    "data" /
    "processed" /
    "pokemon_documents.json"
)

CHROMA_PATH = (
    BASE_DIR /
    "data" /
    "chroma_db"
)

# Load processed Pokémon documents
with open(
    DOCUMENTS_PATH,
    "r",
    encoding="utf-8"
) as f:

    documents = json.load(f)

# Connect to persistent ChromaDB storage
client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

# Create collection if it doesn't already exist
collection = client.get_or_create_collection(
    name="pokemon_rag"
)

# Store embeddings and documents
for idx, doc in enumerate(documents):

    text = doc["text"]

    metadata = doc["metadata"]

    # Generate semantic embedding
    embedding = generate_embedding(text)

    # Add data to vector database
    collection.add(
        ids=[str(idx)],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata]
    )

print("Vector database built successfully!")