# Gen-AI Knowledge Chatbot Workspace

This repository contains several quick-start experiments for working with large language models (LLMs) and building a retrieval-augmented chatbot over internal documents using the Hugging Face Inference API.

## Repository Overview

| Directory | Purpose |
| --- | --- |
| `bot/` | Retrieval-Augmented Generation (RAG) chatbot that indexes local documents into FAISS using Hugging Face endpoints for both embeddings and chat completion. Run `uvicorn bot.app:app --reload` for the web app or `python bot.py` for a terminal chatbot experience. |
| `ChatModels/` | Minimal examples of calling OpenAI GPT-4 and Google Gemini chat models through LangChain. Useful for API smoke tests. |
| `LLMs/` | Simple LLM completion demo using OpenAI's text completion interface. |
| `requirements.txt` | Python dependencies used across the experiments. |

The `bot/` package is the most complete implementation and will be the foundation for turning the terminal chatbot into a hosted experience.

## Current RAG Bot Flow (`bot/rag_service.py`)

1. **Environment setup** – Loads `HUGGINGFACEHUB_API_TOKEN`, model IDs, and establishes the data/index folders.
2. **Document ingestion** – Reads PDFs, DOCX, TXT, and Markdown files from `bot/data/` using `langchain-unstructured` loaders.
3. **Chunking** – Splits documents into ~1k token chunks with overlap for better retrieval.
4. **Embedding + Vector Store** – Generates embeddings via `HuggingFaceEndpointEmbeddings` and persists a FAISS index in `bot/index/`.
5. **Conversational QA** – Wraps a Hugging Face hosted chat model (default `HuggingFaceH4/zephyr-7b-beta`) with LangChain's `RetrievalQA` chain.

The reusable logic now lives in `bot/rag_service.py` and is shared by both the CLI (`bot/bot.py`) and the FastAPI web experience (`bot/app.py`).

## Web Chatbot

The FastAPI server exposes three endpoints:

- `GET /` – Serves a lightweight web client that can run standalone or be embedded via an `<iframe>`.
- `POST /chat` – Accepts `{ "question": "..." }` and returns an answer plus citations.
- `GET /healthz` – Reports the startup status of the service.

To launch the web experience locally:

```bash
export HUGGINGFACEHUB_API_TOKEN=your_token
cd bot
uvicorn bot.app:app --reload
```

Navigate to `http://127.0.0.1:8000` to chat over the indexed internal documents. The API and frontend are CORS-enabled so the widget can also be embedded in other sites by proxying requests to the `/chat` endpoint.

## Deploying the Web Chatbot

### Option 1 – Docker (local or any container host)

```bash
# Build the image
docker build -t internal-doc-chatbot .

# Run it locally with your docs mounted in
docker run \
  -p 8000:8000 \
  -e HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN \
  -v "$(pwd)/bot/data:/app/bot/data" \
  -v "$(pwd)/bot/index:/app/bot/index" \
  internal-doc-chatbot
```

The container will automatically load (or rebuild) the FAISS index from `/app/bot/data`. Mounting the `bot/index/` folder preserves the vector store across restarts.

### Option 2 – Render.com (one-click style deploy)

1. Push this repository (or your fork) to GitHub.
2. Create a new [Render Web Service](https://render.com/docs/web-services) and point it at the repo.
3. Choose **Docker** as the environment. Render will use the provided `Dockerfile`.
4. When prompted for configuration, either import the supplied `render.yaml` or manually set:
   - **Start Command** – leave empty (handled by the Dockerfile).
   - **Environment Variables** – add `HUGGINGFACEHUB_API_TOKEN` with your Hugging Face Inference API key.
   - **Persistent Disk** – mount `/app/bot/index` so the FAISS index survives deploys (the `render.yaml` defines a 1GB disk by default).
5. Click **Create Web Service**. Render will build the image and launch `uvicorn` automatically. The public URL serves both the API (`/chat`, `/healthz`) and web widget (`/`).

For other PaaS providers (Railway, Fly.io, Azure Container Apps, etc.) you can reuse the same container image. Just be sure to supply the `HUGGINGFACEHUB_API_TOKEN` environment variable and mount storage for `/app/bot/index` if you want to avoid rebuilding the index on every start.

## Gaps to Address for a Production Chatbot

- **Web UI polish** – The bundled widget is intentionally lightweight. Add authentication, custom branding, and analytics before shipping broadly.
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

- [x] Refactor `bot/bot.py` into service modules.
- [x] Scaffold a FastAPI server with chat and health endpoints.
- [x] Prototype a simple web chat widget consuming the API.
- [x] Document deployment and configuration in the README.

This plan will convert the current CLI proof-of-concept into an embeddable or standalone web-based chatbot powered entirely by Hugging Face-hosted models.
