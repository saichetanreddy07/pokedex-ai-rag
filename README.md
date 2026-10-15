# Pokedex AI

A Pokémon knowledge assistant project built as a beginner-friendly foundation for semantic search, retrieval-augmented generation, and recommendations.

## Features

### FastAPI foundation
### Environment-based configuration

## Tech Stack

- Python 3.12
- FastAPI and Uvicorn
- Gradio
- ChromaDB
- Sentence Transformers
- Ollama with Llama 3
- Pandas, NumPy, and Requests
- python-dotenv

## Folder Structure

```text
pokedex-ai-rag/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── data_loader.py
│   ├── embeddings.py
│   ├── retriever.py
│   ├── llm.py
│   ├── rag.py
│   ├── recommender.py
│   └── utils.py
├── frontend/
│   └── app.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── chroma_db/
├── .env.example
├── README.md
└── requirements.txt
```

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Usage

Start the API from the project root:

```powershell
uvicorn backend.app:app --reload
```

The API is available at `http://127.0.0.1:8000`.