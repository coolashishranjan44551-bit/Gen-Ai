"""FastAPI application that serves the internal document chatbot."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .rag_service import RAGService

logger = logging.getLogger(__name__)

app = FastAPI(title="Internal Document Chatbot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service: Optional[RAGService] = None
startup_error: Optional[Exception] = None


class Source(BaseModel):
    source: Optional[str] = None
    page: Optional[str] = None
    snippet: Optional[str] = None


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


@app.on_event("startup")
def _startup() -> None:
    global rag_service, startup_error
    try:
        rag_service = RAGService()
        startup_error = None
        logger.info("RAG service initialised successfully.")
    except Exception as exc:  # noqa: BLE001 - we want to log and expose startup failures
        rag_service = None
        startup_error = exc
        logger.exception("Failed to start RAG service: %s", exc)


@app.get("/", response_class=HTMLResponse)
async def read_index() -> str:
    index_path = Path(__file__).resolve().parent / "web" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Web client is missing.")
    return index_path.read_text(encoding="utf-8")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> Dict[str, Any]:
    if startup_error:
        raise HTTPException(
            status_code=500,
            detail=f"Chat service failed to start: {startup_error}",
        )
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Chat service not ready yet.")

    try:
        answer, sources = rag_service.answer(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"answer": answer, "sources": sources}


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    if startup_error:
        return {"status": "error", "detail": str(startup_error)}
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover - manual launch helper
    import uvicorn

    uvicorn.run("bot.app:app", host="0.0.0.0", port=8000, reload=True)
