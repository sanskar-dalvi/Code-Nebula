# Project Architecture – Code-Nebula

## Overview
Code-Nebula is a smart pipeline that takes C# source code and converts it into a searchable graph structure using parsing, AI, and Neo4j.

---

## Pipeline Steps

1. **Parse**
   - C# code is parsed using ANTLR.
   - We extract key entities like classes, methods, etc.

2. **Enrich**
   - The extracted code data is sent to an AI model.
   - AI returns a summary, tags, and insights.

3. **Insert into Graph**
   - The enriched data is inserted into a Neo4j database.
   - Each entity becomes a node; relationships are visualized.

---

## Access Methods

- **CLI Tool (cli.py)** – For command-line processing
- **FastAPI Web API** – For integration with other tools

---

## Technologies Used

- Python
- ANTLR (C# grammar)
- OpenAI or LLM APIs
- Neo4j
- FastAPI
- Git & CI/CD

