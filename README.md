# kiro-memory

AI-powered architectural decision tracking system with semantic search capabilities.

## Description

kiro-memory is a tool that extracts, stores, and enables semantic search over engineering decisions from code, specs, and commit history. It integrates with Kiro CLI to provide contextual decision retrieval.

## Features

- âœ… LLM-based decision extraction from multiple sources
- âœ… Semantic vector search using ChromaDB
- âœ… FastAPI backend with REST API
- âœ… React web dashboard
- âœ… CLI for developer workflows
- âœ… Kiro session hooks integration

## Technology Stack

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **AI/ML:** OpenAI GPT, Sentence Transformers
- **Database:** TinyDB (JSON), ChromaDB (vector)
- **Frontend:** React, JavaScript
- **CLI:** Click, Rich

## Installation

\\\ash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
\\\

## Configuration

Create a \.env\ file:

\\\
OPENAI_API_KEY=your_key_here
WORKSPACE_PATH=C:\Users\dhruv\kiro-memory
DECISIONS_PATH=.kiro/decisions
\\\

## Usage

\\\ash
# CLI
python -m src.cli.main scan       # Index workspace
python -m src.cli.main recall     # Search decisions
python -m src.cli.main list       # List all decisions

# Web Dashboard
python run_server.py
# Visit: http://localhost:8000
\\\

## Project Structure

\\\
kiro-memory/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ api/          # FastAPI backend
â”‚   â”œâ”€â”€ cli/          # Command-line interface
â”‚   â”œâ”€â”€ extractor/    # LLM extraction
â”‚   â”œâ”€â”€ hooks/        # Kiro hooks
â”‚   â”œâ”€â”€ ingestion/    # Data parsing
â”‚   â”œâ”€â”€ search/       # Vector search
â”‚   â””â”€â”€ store/        # Database
â”œâ”€â”€ web/              # React frontend
â”œâ”€â”€ tests/            # Unit tests
â””â”€â”€ requirements.txt  # Dependencies
\\\

## Development

- **Author:** Dhruvin Jayswal (23BT04026)
- **Status:** Production-ready
- **License:** Educational/Research use

## Links

- GitHub: [Add repository URL]
- Documentation: [Add docs URL]
