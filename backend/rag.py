"""Retrieve context and generate a grounded answer with Ollama."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import logging
from typing import Any
import warnings

from backend.config import TOP_K
from backend.llm import generate_answer
from backend.prompts import FALLBACK_ANSWER, build_prompt
from backend.retriever import retrieve_documents

DEBUG = False


def _format_context(documents: list[dict[str, Any]]) -> str:
	"""Join retrieved titles and content into compact prompt context."""
	return "\n\n".join(
		f"{document['title']}\n{document['content']}"
		for document in documents
	)


def _retrieve(question: str) -> list[dict[str, Any]]:
	"""Retrieve context without library progress output outside debug mode."""
	if DEBUG:
		return retrieve_documents(question, k=TOP_K)

	previous_log_level = logging.root.manager.disable
	try:
		logging.disable(logging.WARNING)
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
				return retrieve_documents(question, k=TOP_K)
	finally:
		logging.disable(previous_log_level)


def answer_question(question: str) -> str:
	"""Answer a question using only the top retrieved knowledge documents."""
	cleaned_question = question.strip()
	if not cleaned_question:
		raise ValueError("Question cannot be empty.")

	documents = _retrieve(cleaned_question)
	if DEBUG:
		for document in documents:
			print(
				f"Retrieved {document['title']} "
				f"(score={document['score']:.2f})"
			)
	if not documents:
		return FALLBACK_ANSWER

	prompt = build_prompt(cleaned_question, _format_context(documents))
	return generate_answer(prompt) or FALLBACK_ANSWER


def main() -> None:
	"""Prompt for a question and print its answer."""
	question = input("Question: ").strip()
	if not question:
		answer = FALLBACK_ANSWER
	else:
		try:
			answer = answer_question(question)
		except Exception as error:
			if DEBUG:
				print(f"RAG pipeline error: {error}")
			answer = "Unable to generate an answer. Check Ollama and the configured model."

	print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
	main()