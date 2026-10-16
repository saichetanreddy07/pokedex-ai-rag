"""FastAPI endpoints for the Pokedex AI RAG pipeline."""

import traceback

from fastapi import FastAPI, HTTPException

from backend.rag import answer_question
from backend.schemas import AskRequest, AskResponse

app = FastAPI(title="Pokedex AI API")


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a welcome message."""
    return {"message": "Welcome to Pokedex AI"}


@app.get("/health")
def read_health() -> dict[str, str]:
    """Report that the API service is running."""
    return {"status": "healthy"}


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    """Pass a question to the existing RAG pipeline."""
    try:
        answer = answer_question(request.question)

    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    except Exception as error:
        # Print the complete traceback to the terminal
        traceback.print_exc()

        # Return the actual error while debugging
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return AskResponse(
        question=request.question,
        answer=answer,
    )