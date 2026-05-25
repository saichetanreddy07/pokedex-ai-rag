# PokéDex AI — Pokémon Lore & Team Recommendation Assistant

PokéDex AI is a full-stack Retrieval-Augmented Generation (RAG) application that combines Pokémon lore retrieval, semantic search, and AI-powered conversational responses using local LLMs.

The project uses FastAPI, ChromaDB, Ollama (Llama 3), and Gradio to create an interactive Pokémon assistant capable of answering lore questions, retrieving Pokémon knowledge semantically, and serving as a foundation for advanced team recommendation systems.

---

# Features

- Retrieval-Augmented Generation (RAG)
- Local LLM inference using Ollama + Llama 3
- Pokémon lore chatbot
- Semantic search using embeddings
- FastAPI backend API
- Gradio chatbot frontend
- ChromaDB vector database
- Pokédex lore retrieval
- Pokémon abilities, stats, and moves retrieval
- Foundation for team recommendation engine
- Modular AI architecture

---

# System Architecture

```text
User
   ↓
Gradio Frontend
   ↓
FastAPI Backend
   ↓
RAG Pipeline
   ↓
Retriever
   ↓
ChromaDB Vector Database
   ↓
Llama 3 via Ollama
```

---

# Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Gradio |
| Backend | FastAPI |
| LLM | Ollama + Llama 3 |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| AI Framework | LangChain |
| Dataset | PokéAPI |

---

# Project Structure

```text
Pokemon/
│
├── backend/
│   └── app/
│       ├── db/
│       ├── ingestion/
│       ├── rag/
│       ├── recommender/
│       └── main.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── chroma_db/
│
├── frontend/
│   └── gradio_app.py
│
├── requirements.txt
└── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/your-username/pokedex-ai-rag.git

cd pokedex-ai-rag
```

---

## 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Install Ollama + Llama 3

Install Ollama:

https://ollama.com/

Pull Llama 3 model:

```bash
ollama pull llama3
```

Verify installation:

```bash
ollama run llama3
```

---

# Data Pipeline

## Fetch Pokémon Data

```bash
python -m backend.app.ingestion.fetch_pokemon
```

## Fetch Species & Lore Data

```bash
python -m backend.app.ingestion.fetch_species
```

## Process RAG Documents

```bash
python -m backend.app.ingestion.process_documents
```

## Build Vector Database

```bash
python -m backend.app.ingestion.build_vector_store
```

---

# Running the Application

## Start FastAPI Backend

```bash
uvicorn backend.app.main:app --reload
```

Backend available at:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

---

## Start Gradio Frontend

Open another terminal:

```bash
python frontend/gradio_app.py
```

Frontend available at:

```text
http://127.0.0.1:7860
```

---

# Example Queries

- Who is Pikachu?
- Tell me about Charizard
- Who created Mewtwo?
- Which Pokémon causes lightning storms?
- Tell me about legendary bird Pokémon
- Explain Eevee evolutions
- What are Gengar’s abilities?

---

# How RAG Works

1. User asks a Pokémon-related question
2. Query is converted into embeddings
3. ChromaDB performs semantic vector search
4. Relevant Pokémon documents are retrieved
5. Retrieved context is sent to Llama 3
6. LLM generates grounded AI response

---

# Current Capabilities

- Semantic Retrieval
- Grounded AI Responses
- Pokémon Lore Chatbot
- Vector Search
- Local LLM Inference
- Full-Stack AI Architecture

---

# Future Improvements

- Pokémon team recommendation engine
- Type weakness analysis
- Evolution chain graph RAG
- Hybrid retrieval (metadata + embeddings)
- Neo4j Graph RAG
- Chat memory
- Docker deployment
- Pokémon-themed UI enhancements

---

# Dataset Sources

- PokéAPI
- Pokémon species endpoints
- Pokédex flavor text data

---

# Author

Sai Chetan Reddy

---

# Acknowledgements

- PokéAPI
- Ollama
- LangChain
- ChromaDB
- Gradio
- HuggingFace