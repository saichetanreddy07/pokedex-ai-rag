"""Retrieve relevant knowledge documents from the ChromaDB collection."""

from typing import Any

import chromadb

from backend.config import TOP_K
from backend.embedder import load_embedding_model
from backend.vector_store import get_client, get_collection as open_collection


def get_collection() -> chromadb.Collection:
	"""Open the persistent Pokémon knowledge collection."""
	return open_collection(get_client())


def embed_query(query: str) -> list[float]:
	"""Encode one query with the cached knowledge-document model."""
	cleaned_query = query.strip()
	if not cleaned_query:
		raise ValueError("Query cannot be empty.")

	model = load_embedding_model()
	query_vector = model.encode(cleaned_query, convert_to_numpy=True)
	return [float(value) for value in query_vector]


def _get_title(document_id: str, content: str) -> str:
	"""Derive a display title from the stored content or document ID."""
	first_sentence = content.split(".", 1)[0].strip()
	if " is a " in first_sentence:
		return first_sentence.split(" is a ", 1)[0]
	if first_sentence.lower().startswith("evolution chain "):
		chain_id = first_sentence.split()[2]
		return f"Evolution Chain {chain_id}"
	return document_id.replace("-", " ").title()


def retrieve_documents(
	query: str,
	k: int = TOP_K,
) -> list[dict[str, Any]]:
	"""Return top-k documents with metadata and normalized similarity scores."""
	if k < 1:
		raise ValueError("k must be greater than zero.")

	collection = get_collection()
	collection_count = collection.count()
	if collection_count == 0:
		return []

	query_vector = embed_query(query)
	result_count = min(k, collection_count)
	matches = collection.query(
		query_embeddings=[query_vector],
		n_results=result_count,
		include=["documents", "metadatas", "distances"],
	)

	ids = matches["ids"][0]
	documents = matches["documents"][0]
	metadatas = matches["metadatas"][0]
	distances = matches["distances"][0]
	results = []
	for document_id, content, metadata, distance in zip(
		ids, documents, metadatas, distances
	):
		if content is None or distance is None:
			continue
		similarity = 1.0 / (1.0 + float(distance))
		results.append(
			{
				"id": document_id,
				"title": _get_title(document_id, content),
				"content": content,
				"metadata": metadata or {},
				"score": similarity,
			}
		)
	return results


def format_results(results: list[dict[str, Any]]) -> str:
	"""Format retrieved documents for display in the terminal."""
	if not results:
		return "No matching documents found."

	lines = [f"Top {len(results)} Results", ""]
	for index, result in enumerate(results, start=1):
		metadata_text = ", ".join(
			f"{key}: {value}" for key, value in result["metadata"].items()
		)
		lines.extend(
			[
				f"{index}.",
				f"Title: {result['title']}",
				f"Score: {result['score']:.2f}",
				f"Metadata: {metadata_text}" if metadata_text else "",
				result["content"],
				"",
				"-" * 50,
			]
		)
	return "\n".join(lines)


def main() -> None:
	"""Prompt for a query and print its top matching documents."""
	query = input("Query: ").strip()
	if not query:
		print("Please enter a non-empty query.")
		return

	results = retrieve_documents(query)
	print("\n" + "=" * 50)
	print(f"Query: {query}\n")
	print(format_results(results))
	print("=" * 50)


if __name__ == "__main__":
	main()