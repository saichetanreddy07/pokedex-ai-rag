# Pokedex AI

A Pokémon knowledge assistant project built as a beginner-friendly foundation for semantic search, retrieval-augmented generation, and recommendations.

## Features

### FastAPI foundation
### Environment-based configuration
### Resumable PokéAPI data collection

## Data Collection

The downloader starts with PokéAPI's Generation endpoint. Set `TARGET_GENERATION`
in `.env` to choose a generation; it defaults to Generation I. The generation
response determines which species are processed, so the Pokémon IDs are not
maintained as a hardcoded list.

For those species, the pipeline:

- Downloads **Pokémon species** data, including species information such as
	flavor text and habitat.
- Downloads the corresponding **Pokémon** data, including names, types, and
	base stats.
- Collects move references from those Pokémon and downloads only the referenced
	**moves**, including type, power, and accuracy.
- Collects evolution chain references from those species and downloads only
	the referenced **evolution chains**.

This generation-scoped approach avoids unrelated resources and unnecessary
alternate Pokémon forms.

Each response is stored as an individual JSON file:

```text
data/raw/
├── pokemon/
├── species/
├── moves/
└── evolution_chains/
```

## Data Preprocessing

Raw JSON downloaded from the PokéAPI is transformed into clean, structured CSV
datasets in `data/processed/`. These CSV files will be used for later document
generation and embedding steps. Run the preprocessing pipeline from the project
root with:

```powershell
python backend/preprocessor.py
```

## Knowledge Document Generation

The knowledge-document stage transforms the processed CSV datasets into
searchable documents:

```text
Raw JSON -> Processed CSV -> Knowledge Documents
```

Run it from the project root with `python -m backend.document_generator`.
The generated JSON files in `data/documents/` are ready for the later
embedding phase.

## Embedding Generation

Knowledge documents are converted into vector embeddings with
`all-MiniLM-L6-v2`. The generated embeddings are ready for storage in the
vector database. Run the embedding pipeline from the project root with:

```powershell
python -m backend.embedder
```

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
│   ├── preprocessor.py
│   ├── document_generator.py
│   ├── embedder.py
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

Run the data downloader from the project root:

```powershell
python -m backend.data_loader
```

Existing files are skipped so interrupted downloads can be resumed.

Start the API from the project root:

```powershell
uvicorn backend.app:app --reload
```

The API is available at `http://127.0.0.1:8000`.