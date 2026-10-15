"""Generate in-memory vector embeddings for knowledge documents."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 32
DOCUMENT_FILES = {
	"pokemon": "pokemon_documents.json",
	"move": "move_documents.json",
	"evolution": "evolution_documents.json",
}


def load_documents() -> dict[str, list[dict[str, Any]]]:
	"""Load and validate each knowledge-document JSON file."""
	documents_by_resource: dict[str, list[dict[str, Any]]] = {}
	for resource, file_name in DOCUMENT_FILES.items():
		file_path = DOCUMENTS_DIR / file_name
		if not file_path.is_file():
			raise FileNotFoundError(f"Knowledge document file not found: {file_path}")

		with file_path.open(encoding="utf-8") as json_file:
			documents = json.load(json_file)
		if not isinstance(documents, list):
			raise ValueError(f"Expected a list of documents in {file_path}.")

		validated_documents = []
		for index, document in enumerate(documents):
			if not isinstance(document, dict):
				raise ValueError(f"Document {index} in {file_path} is not an object.")
			if not isinstance(document.get("id"), str):
				raise ValueError(f"Document {index} in {file_path} has no string id.")
			if not isinstance(document.get("content"), str):
				raise ValueError(
					f"Document {index} in {file_path} has no string content."
				)
			if not isinstance(document.get("metadata"), dict):
				raise ValueError(
					f"Document {index} in {file_path} has no metadata object."
				)
			validated_documents.append(
				{
					"id": document["id"],
					"content": document["content"],
					"metadata": document["metadata"],
				}
			)
		documents_by_resource[resource] = validated_documents

	return documents_by_resource


@lru_cache(maxsize=1)
def load_embedding_model() -> SentenceTransformer:
	"""Load the configured Sentence Transformers model once per process."""
	return SentenceTransformer(MODEL_NAME)


def generate_embeddings(
	documents: list[dict[str, Any]],
	model: SentenceTransformer,
	batch_size: int = BATCH_SIZE,
) -> list[dict[str, Any]]:
	"""Embed document content in batches and return source-associated records."""
	if batch_size < 1:
		raise ValueError("batch_size must be greater than zero.")
	if not documents:
		return []

	contents = [document["content"] for document in documents]
	vectors = model.encode(
		contents,
		batch_size=batch_size,
		show_progress_bar=True,
		convert_to_numpy=True,
	)
	if len(vectors) != len(documents):
		raise ValueError("The model returned a different number of embeddings.")

	embedding_records = []
	for document, vector in zip(documents, vectors):
		embedding_records.append(
			{
				"id": document["id"],
				"content": document["content"],
				"metadata": document["metadata"],
				"embedding": [float(value) for value in vector],
			}
		)
	return embedding_records


def main() -> None:
	"""Generate embeddings and print a summary without saving vectors."""
	documents_by_resource = load_documents()
	documents = [
		document
		for resource_documents in documents_by_resource.values()
		for document in resource_documents
	]
	model = load_embedding_model()
	embedding_records = generate_embeddings(documents, model)
	embedding_dimension = model.get_embedding_dimension()
	if embedding_dimension is None and embedding_records:
		embedding_dimension = len(embedding_records[0]["embedding"])

	print(f"Model: {MODEL_NAME}")
	print(f"Pokémon documents: {len(documents_by_resource['pokemon'])}")
	print(f"Move documents: {len(documents_by_resource['move'])}")
	print(f"Evolution documents: {len(documents_by_resource['evolution'])}")
	print(f"Total documents: {len(embedding_records)}")
	print(f"Embedding dimension: {embedding_dimension}")
	print("Embedding generation completed successfully.")


if __name__ == "__main__":
	main()