"""Persist knowledge-document embeddings in ChromaDB."""

from pathlib import Path
from typing import Any

import chromadb

from backend.embedder import (
	generate_embeddings,
	load_documents,
	load_embedding_model,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "pokemon_knowledge"


def get_client() -> chromadb.ClientAPI:
	"""Open a persistent ChromaDB client in data/chroma_db."""
	DATABASE_DIR.mkdir(parents=True, exist_ok=True)
	return chromadb.PersistentClient(path=str(DATABASE_DIR))


def get_collection(client: chromadb.ClientAPI) -> chromadb.Collection:
	"""Open the project collection or create it when it does not exist."""
	collection_names = {collection.name for collection in client.list_collections()}
	if COLLECTION_NAME in collection_names:
		return client.get_collection(name=COLLECTION_NAME)
	return client.create_collection(name=COLLECTION_NAME)


def _prepare_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
	"""Convert list-valued metadata to scalar text accepted by ChromaDB."""
	prepared_metadata = {}
	for key, value in metadata.items():
		if value is None:
			continue
		if isinstance(value, list):
			value = ", ".join(str(item) for item in value)
		if isinstance(value, (str, int, float, bool)):
			prepared_metadata[key] = value
		else:
			raise ValueError(f"Unsupported metadata value for {key!r}.")
	return prepared_metadata


def index_documents(
	records: list[dict[str, Any]],
	collection: chromadb.Collection,
) -> int:
	"""Insert records not already present and return the inserted count."""
	unique_records = []
	seen_ids: set[str] = set()
	for record in records:
		document_id = record.get("id")
		if not isinstance(document_id, str) or not document_id:
			raise ValueError("Every embedding record must have a nonempty string ID.")
		if document_id in seen_ids:
			continue
		seen_ids.add(document_id)
		unique_records.append(record)

	if not unique_records:
		return 0

	existing_ids = set(
		collection.get(
			ids=[record["id"] for record in unique_records],
			include=[],
		)["ids"]
	)
	new_records = [
		record for record in unique_records if record["id"] not in existing_ids
	]
	if not new_records:
		return 0

	ids = []
	documents = []
	embeddings = []
	metadatas = []
	for record in new_records:
		content = record.get("content")
		embedding = record.get("embedding")
		metadata = record.get("metadata")
		if not isinstance(content, str):
			raise ValueError(f"Document {record['id']} has no string content.")
		if not isinstance(embedding, list) or not embedding:
			raise ValueError(f"Document {record['id']} has no embedding vector.")
		if not isinstance(metadata, dict):
			raise ValueError(f"Document {record['id']} has no metadata object.")

		ids.append(record["id"])
		documents.append(content)
		embeddings.append([float(value) for value in embedding])
		metadatas.append(_prepare_metadata(metadata))

	collection.add(
		ids=ids,
		documents=documents,
		embeddings=embeddings,
		metadatas=metadatas,
	)
	return len(new_records)


def print_collection_stats(
	collection: chromadb.Collection,
	document_counts: dict[str, int],
	inserted_count: int,
) -> None:
	"""Print resource counts and the collection's persisted count."""
	print(f"Collection: {COLLECTION_NAME}")
	print(f"Pokemon Documents: {document_counts['pokemon']}")
	print(f"Move Documents: {document_counts['move']}")
	print(f"Evolution Documents: {document_counts['evolution']}")
	print(f"Total Indexed: {inserted_count}")
	print(f"Collection Count: {collection.count()}")
	print("Indexing Complete.")


def main() -> None:
	"""Generate embeddings and persist them in the project collection."""
	documents_by_resource = load_documents()
	document_counts = {
		resource: len(documents)
		for resource, documents in documents_by_resource.items()
	}
	documents = [
		document
		for resource_documents in documents_by_resource.values()
		for document in resource_documents
	]
	model = load_embedding_model()
	records = generate_embeddings(documents, model)
	collection = get_collection(get_client())
	inserted_count = index_documents(records, collection)
	print_collection_stats(collection, document_counts, inserted_count)


if __name__ == "__main__":
	main()