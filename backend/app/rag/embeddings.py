import os

from sentence_transformers import SentenceTransformer

# Disable TensorFlow warnings/issues
os.environ["USE_TF"] = "0"

# Load embedding model
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# Generate semantic embeddings
def generate_embedding(text):

    embedding = model.encode(text)

    return embedding.tolist()