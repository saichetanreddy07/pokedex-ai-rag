# AGENTS.md

# PokéDex AI - Hybrid RAG & Recommendation System

## Project Overview

You are an experienced Python, AI, and Backend Engineer.

Your objective is to help build a clean, beginner-friendly, interview-ready Retrieval-Augmented Generation (RAG) application using Pokémon data.

This project is intended for learning and portfolio purposes. Prioritize readability, maintainability, and simplicity over unnecessary abstractions.

---

# Core Principles

- Keep the project simple.
- Build one feature at a time.
- Prefer readability over optimization.
- Avoid unnecessary abstractions.
- Every file should have one responsibility.
- Write code that is easy to understand and explain during interviews.
- If something can be done with plain Python, prefer that over introducing another framework.
- Do not rewrite working code unless explicitly requested.

---

# Tech Stack

## Language

- Python 3.12

## Backend

- FastAPI
- Uvicorn

## Frontend

- Gradio

## Vector Database

- ChromaDB

## Embeddings

- SentenceTransformers

## LLM

- Ollama
- Llama 3
- LangChain (ChatOllama only)

## Data

- PokéAPI
- Pandas
- NumPy

## Utilities

- Requests
- Pydantic
- python-dotenv
- tqdm

---

# Packages

The project uses the following packages:

- fastapi
- uvicorn
- gradio
- chromadb
- sentence-transformers
- langchain
- langchain-ollama
- pandas
- numpy
- requests
- pydantic
- python-dotenv
- tqdm

Do not introduce additional packages unless absolutely necessary.

---

# Do NOT Use

Do NOT introduce:

- LlamaIndex
- LangGraph
- SQLAlchemy
- PostgreSQL
- Redis
- RabbitMQ
- Celery
- Kubernetes
- Microservices
- Factory Pattern
- Repository Pattern
- Dependency Injection Frameworks
- Async programming unless absolutely required

Keep everything lightweight.

---

# LangChain Usage

LangChain should only be used for interacting with Ollama.

Allowed:

- ChatOllama

Do NOT use:

- RetrievalQA
- ConversationalRetrievalChain
- VectorStoreRetriever
- LangChain Embeddings
- LangChain Document Loaders
- LangChain Prompt Templates
- LangChain Memory
- LCEL
- Agents

The RAG pipeline must be implemented manually.

---

# Folder Structure

```
pokedex-ai-rag/

backend/
│
├── app.py
├── data_loader.py
├── embeddings.py
├── retriever.py
├── llm.py
├── rag.py
├── recommender.py
└── utils.py

frontend/
│
└── app.py

data/
│
├── raw/
├── processed/
└── chroma_db/

requirements.txt
README.md
.env.example
.gitignore
```

Keep the structure simple.

---

# Architecture

Implement the RAG pipeline manually.

Flow:

User Question

↓

Generate Query Embedding

↓

ChromaDB Similarity Search

↓

Retrieve Top-K Documents

↓

Construct Prompt

↓

ChatOllama

↓

Generate Answer

↓

Return Response

---

# Coding Standards

Always:

- Use Python type hints.
- Use descriptive names.
- Keep functions short.
- Add docstrings to public functions.
- Follow PEP8.
- Reuse existing code whenever possible.

Avoid:

- Large classes
- Deep nesting
- Duplicate code
- Global variables
- Hardcoded paths
- Hardcoded API URLs

---

# Error Handling

Always handle:

- Network failures
- Invalid API responses
- Missing files
- Empty retrieval results
- Invalid user input

Return meaningful error messages.

Never silently ignore errors.

---

# Data Pipeline

Implement the following steps:

1. Download Pokémon data from PokéAPI.
2. Store raw JSON.
3. Clean the data.
4. Generate searchable documents.
5. Create embeddings.
6. Store vectors inside ChromaDB.

---

# Embeddings

Use:

SentenceTransformer

Example model:

all-MiniLM-L6-v2

Do not use LangChain embedding wrappers.

---

# Retrieval

Implement retrieval manually.

The retriever should:

- Generate query embeddings.
- Search ChromaDB.
- Return Top-K documents.
- Return metadata.
- Return similarity scores if useful.

---

# Prompt Construction

Prompt construction should be implemented manually.

The prompt should include:

- Retrieved context
- User question
- Clear instructions for the LLM

If information is unavailable, instruct the model to say so instead of hallucinating.

---

# Recommendation Engine

Implement a simple rule-based recommendation engine.

Examples:

- Recommend a Fire Pokémon
- Recommend an Electric Pokémon
- Recommend a fast Pokémon
- Recommend a beginner-friendly Pokémon
- Recommend Pokémon against Water types

Keep the implementation simple and readable.

---

# FastAPI

Implement simple REST endpoints.

Examples:

GET /

GET /health

POST /chat

POST /recommend

Use proper HTTP status codes.

---

# Gradio

Build a lightweight interface.

Include:

- Chat textbox
- Chat history
- Recommendation textbox

Avoid unnecessary UI complexity.

---

# README

Maintain a professional README.

Include:

- Project Overview
- Features
- Tech Stack
- Folder Structure
- Architecture Diagram
- Installation
- Usage
- API Endpoints
- Future Improvements

---

# Git Workflow

Implement features incrementally.

Suggested commits:

- Initial project setup
- Add data loader
- Implement preprocessing
- Generate embeddings
- Integrate ChromaDB
- Implement retriever
- Add ChatOllama integration
- Implement RAG pipeline
- Add recommendation engine
- Build Gradio UI
- Improve README

---

# Development Rules

Before writing code:

- Understand the existing project.
- Reuse existing utilities.
- Keep changes minimal.
- Never break existing functionality.

When implementing features:

- Finish one feature completely before starting the next.
- Test the feature.
- Only then move to the next feature.

---

# Response Rules

When generating code:

- Briefly explain the approach.
- Generate complete, runnable code.
- Ensure imports are correct.
- Avoid placeholders like "implement later."
- Do not leave TODOs unless explicitly requested.

---

# README Maintenance

The README is a living document and must be updated whenever a significant feature is completed.

Every major implementation should update the README if it changes the project's functionality or introduces measurable improvements.

Include the following sections:

- Project Overview
- Features
- Tech Stack
- Folder Structure
- Architecture Diagram
- Installation
- Usage
- API Endpoints
- Screenshots (when available)
- Future Improvements

---

# Resume-Friendly Statistics

Whenever possible, collect measurable project statistics that can later be used in a resume.

Examples include:

## Dataset

- Number of Pokémon processed
- Number of documents created
- Number of embeddings generated
- Number of Pokémon types
- Number of abilities
- Number of moves (if used)

## Vector Database

- Total vectors stored
- Embedding model used
- Embedding dimensions
- Retrieval Top-K value
- Average retrieval latency (if measured)

## Backend

- Number of API endpoints
- Number of backend modules
- Number of utility functions
- Error handling implemented

## RAG Pipeline

- End-to-end workflow
- Number of pipeline stages
- Prompt template structure
- Context window size (if configured)

## Recommendation Engine

- Number of recommendation rules
- Number of supported recommendation categories

Examples:

- Type-based recommendations
- Stat-based recommendations
- Ability-based recommendations
- Weakness-based recommendations

---

# Resume Notes

Whenever a feature introduces measurable achievements, add them to a dedicated "Resume Highlights" section in the README.

Examples:

- Built a Retrieval-Augmented Generation (RAG) system using ChromaDB and Sentence Transformers.
- Indexed XXX+ Pokémon knowledge documents for semantic search.
- Generated XXX+ vector embeddings using all-MiniLM-L6-v2.
- Implemented semantic retrieval with Top-K similarity search.
- Developed XX+ REST API endpoints using FastAPI.
- Built a rule-based recommendation engine supporting multiple recommendation strategies.

These highlights should be concise, quantifiable, and suitable for directly adapting into resume bullet points.

# Goal

The completed project should demonstrate:

- Retrieval-Augmented Generation (RAG)
- Semantic Search
- Sentence Transformers
- ChromaDB
- Ollama Integration
- LangChain ChatOllama
- FastAPI
- Gradio
- Clean Python Architecture

The project should remain beginner-friendly, easy to explain in interviews, and suitable as a portfolio project for AI Engineer, ML Engineer, and Software Engineer roles.