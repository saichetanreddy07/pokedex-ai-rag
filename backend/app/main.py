from fastapi import FastAPI
from pydantic import BaseModel

from backend.app.rag.rag_pipeline import ask_pokedex

# Create FastAPI application
app = FastAPI(
    title="PokéDex AI",
    description="Pokémon Lore & RAG Assistant",
    version="1.0.0"
)

# Request schema
class ChatRequest(BaseModel):

    question: str

# Root route
@app.get("/")
def home():

    return {
        "message": "PokéDex AI Backend Running!"
    }

# Chat endpoint
@app.post("/chat")
def chat(request: ChatRequest):

    # Generate AI response
    response = ask_pokedex(
        request.question
    )

    return {
        "question": request.question,
        "response": response
    }