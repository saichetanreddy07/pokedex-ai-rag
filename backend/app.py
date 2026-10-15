"""Minimal FastAPI application for the project foundation."""

from fastapi import FastAPI

app = FastAPI(
    title="Pokedex AI",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a welcome message."""
    return {"message": "Welcome to Pokedex AI"}


@app.get("/health")
def read_health() -> dict[str, str]:
    """Report that the application is healthy."""
    return {"status": "healthy"}