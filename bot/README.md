# 📘 RAG Chatbot over Your Documents (Hugging Face Inference API)

A simple Retrieval-Augmented Generation (RAG) chatbot that:

1. loads your local docs,
2. splits them into chunks,
3. embeds them with Hugging Face Inference API,
4. stores them in FAISS,
5. answers questions using retrieved context.

> Works on Windows. Designed for corp networks (proxy/SSL) with small tweaks.

---

## 🗂 Project Structure

```
bot/
├─ app.py            # FastAPI web server that serves the chat widget and API
├─ bot.py            # CLI helper kept for quick experiments
├─ rag_service.py    # Shared indexing + RetrievalQA orchestration
├─ web/index.html    # Standalone web widget
├─ data/             # Put your PDFs/DOCX/TXT/MD here
├─ index/            # FAISS index is saved here (auto-created)
├─ .env              # Secrets & config (NOT committed)
└─ requirements.txt
```

## 🚀 Run the Web Chatbot

```bash
# Install dependencies
pip install -r ../requirements.txt -r requirements.txt

# Configure credentials and launch the server
export HUGGINGFACEHUB_API_TOKEN=your_token
uvicorn bot.app:app --reload
```

Open `http://127.0.0.1:8000` for the embedded web UI. To reuse the widget inside another
site, proxy API requests to the `/chat` endpoint (CORS is open by default).

## 💬 cURL Example

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our Azure pilot plan?"}'
```

## 🧪 CLI Fallback

```bash
python bot.py
```

The CLI uses the same RAG pipeline defined in `rag_service.py`.
