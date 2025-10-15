# Gen-AI Knowledge Chatbot Workspace

This repository contains several quick-start experiments for working with large language models (LLMs) and building a retrieval-augmented chatbot over internal documents using the Hugging Face Inference API.

## Repository Overview

| Directory | Purpose |
| --- | --- |
| `bot/` | Retrieval-Augmented Generation (RAG) chatbot that indexes local documents into FAISS using Hugging Face endpoints for both embeddings and chat completion. Run `python bot.py` for a terminal chatbot experience. |
| `ChatModels/` | Minimal examples of calling OpenAI GPT-4 and Google Gemini chat models through LangChain. Useful for API smoke tests. |
| `LLMs/` | Simple LLM completion demo using OpenAI's text completion interface. |
| `requirements.txt` | Python dependencies used across the experiments. |

The `bot/` package is the most complete implementation and will be the foundation for turning the terminal chatbot into a hosted experience.

## Current RAG Bot Flow (`bot/bot.py`)

1. **Environment setup** – Loads `HUGGINGFACEHUB_API_TOKEN`, model IDs, and establishes the data/index folders.
2. **Document ingestion** – Reads PDFs, DOCX, TXT, and Markdown files from `bot/data/` using `langchain-unstructured` loaders.
3. **Chunking** – Splits documents into ~1k token chunks with overlap for better retrieval.
4. **Embedding + Vector Store** – Generates embeddings via `HuggingFaceEndpointEmbeddings` and persists a FAISS index in `bot/index/`.
5. **Conversational QA** – Wraps a Hugging Face hosted chat model (default `HuggingFaceH4/zephyr-7b-beta`) with LangChain's `RetrievalQA` chain and provides a CLI chat loop with source citations.

## Gaps to Address for a Production Chatbot

- **No web UI** – The existing bot is CLI-only. We need a frontend that can be embedded into any website or launched as a standalone app.
- **Document management** – Documents must currently be copied manually into `bot/data/`. Consider adding upload APIs, scheduled re-indexing, and multi-tenant storage.
- **Authentication & access control** – Protect internal documents and optionally scope retrieval per user.
- **Deployment** – Package the service as a web API with persistent storage and containerized deployment.

## Suggested Implementation Plan

1. **Modularize the backend**
   - Extract the document loading, chunking, and indexing logic from `bot.py` into reusable modules (e.g., `ingest.py`, `retriever.py`).
   - Wrap the LangChain RetrievalQA pipeline in a class that exposes simple `query(question, session_id)` semantics.

2. **Build a REST API**
   - Use FastAPI or Flask inside `bot/` to expose endpoints for document upload, indexing status, and chat responses.
   - Reuse the existing FAISS index; persist it between runs on disk or via S3-compatible storage.

3. **Create a lightweight web client**
   - Option A: A vanilla HTML/JS widget that calls the REST API and can be dropped into any website via `<script>` tag.
   - Option B: A React/Vue SPA served by the backend for a full web app launch.
   - Include conversational UI elements, document source citations, and feedback capture.

4. **Authentication & authorization**
   - Add API key or OAuth-based auth at the REST layer.
   - Tie user identity to document collections if multi-tenant support is needed.

5. **Operational concerns**
   - Use background jobs (Celery/RQ) or async tasks for heavy document ingestion.
   - Log requests/responses and monitor Hugging Face API usage.
   - Containerize with Docker and define deployment scripts for the target hosting environment.

## Next Steps

- [ ] Refactor `bot/bot.py` into service modules.
- [ ] Scaffold a FastAPI server with chat and health endpoints.
- [ ] Prototype a simple web chat widget consuming the API.
- [ ] Document deployment and configuration in the README.

This plan will convert the current CLI proof-of-concept into an embeddable or standalone web-based chatbot powered entirely by Hugging Face-hosted models.
