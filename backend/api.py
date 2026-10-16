"""FastAPI endpoints for the Pokedex AI RAG pipeline."""

import traceback

from fastapi import FastAPI, HTTPException

from backend.rag import answer_question
from backend.recommender import recommend_pokemon
from backend.schemas import (
	AnalyzeTeamRequest,
	AskRequest,
	AskResponse,
	RecommendRequest,
	RecommendResponse,
	TeamAnalysisResponse,
	TeamRequest,
	TeamResponse,
)
from backend.team_analyzer import analyze_team
from backend.team_builder import build_team

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


def _recommendation_error(error: Exception) -> HTTPException:
	"""Log a recommendation failure and return its diagnostic API response."""
	if isinstance(error, ValueError):
		return HTTPException(status_code=422, detail=str(error))
	traceback.print_exc()
	return HTTPException(status_code=503, detail=str(error))


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
	"""Recommend Pokémon using structured types, stats, and species data."""
	try:
		return RecommendResponse(**recommend_pokemon(request.query, request.limit))
	except Exception as error:
		raise _recommendation_error(error) from error


@app.post("/team", response_model=TeamResponse)
def create_team(request: TeamRequest) -> TeamResponse:
	"""Build a six-member team and report its computed type coverage."""
	try:
		return TeamResponse(**build_team(request.query))
	except Exception as error:
		raise _recommendation_error(error) from error


@app.post("/analyze-team", response_model=TeamAnalysisResponse)
def team_analysis(request: AnalyzeTeamRequest) -> TeamAnalysisResponse:
	"""Analyze team roles, type matchups, balance, and replacement choices."""
	try:
		return TeamAnalysisResponse(**analyze_team(request.team))
	except Exception as error:
		raise _recommendation_error(error) from error
