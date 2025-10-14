# bot.py
import os
from dotenv import load_dotenv

from langchain_unstructured import UnstructuredLoader
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import (
    HuggingFaceEndpointEmbeddings,
    HuggingFaceEndpoint,
    ChatHuggingFace,
)
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import ChatPromptTemplate

# ---------------------------
# Env & config
# ---------------------------
load_dotenv()
HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
if not HF_TOKEN:
    raise RuntimeError("Set HUGGINGFACEHUB_API_TOKEN in your environment/.env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "HuggingFaceH4/zephyr-7b-beta")  # chat model

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
INDEX_DIR = os.path.join(BASE, "index")

# ---------------------------
# 1) Load documents
# ---------------------------
if not os.path.isdir(DATA_DIR):
    raise RuntimeError("Create a ./data folder and add PDFs/DOCX/TXT files.")

docs = []
for fname in os.listdir(DATA_DIR):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.isfile(path):
        continue
    lower = fname.lower()
    if lower.endswith(".pdf"):
        docs += PyPDFLoader(path).load()
    elif lower.endswith(".docx"):
        docs += Docx2txtLoader(path).load()
    else:
        docs += UnstructuredLoader(path).load()

if not docs:
    raise RuntimeError("No documents found in ./data. Add PDFs/DOCX/TXT and rerun.")

# ---------------------------
# 2) Split into chunks
# ---------------------------
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
chunks = splitter.split_documents(docs)

# ---------------------------
# 3) Embeddings + FAISS (reuse if exists)
# ---------------------------
emb = HuggingFaceEndpointEmbeddings(
    model=EMBEDDING_MODEL,
    huggingfacehub_api_token=HF_TOKEN,
)

os.makedirs(INDEX_DIR, exist_ok=True)
try:
    # If an index already exists, load it (faster dev cycles)
    existing = [n for n in os.listdir(INDEX_DIR) if n.endswith(".faiss") or n.endswith(".pkl")]
except FileNotFoundError:
    existing = []

if existing:
    vs = FAISS.load_local(INDEX_DIR, emb, allow_dangerous_deserialization=True)
else:
    vs = FAISS.from_documents(chunks, emb)
    vs.save_local(INDEX_DIR)

# ---------------------------
# 4) Chat LLM (conversational) + RetrievalQA
# ---------------------------
chat_llm = ChatHuggingFace(
    llm=HuggingFaceEndpoint(
        repo_id=LLM_MODEL,
        task="conversational",               # REQUIRED for Zephyr
        huggingfacehub_api_token=HF_TOKEN,
        temperature=0.0,
        max_new_tokens=512,
    )
)

SYSTEM = "Answer ONLY from the provided context. If not present, say 'Not in docs'. Keep answers concise."

# IMPORTANT: include {context} because RetrievalQA(stuff) injects documents here.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM + "\n\nContext:\n{context}"),
        ("human", "{question}"),
    ]
)

qa = RetrievalQA.from_chain_type(
    llm=chat_llm,
    retriever=vs.as_retriever(search_kwargs={"k": 4}),
    chain_type="stuff",
    chain_type_kwargs={
        "prompt": prompt,
        "document_variable_name": "context",  # default is "context" but we state it explicitly
    },
    return_source_documents=True,
)

# ---------------------------
# 5) CLI loop
# ---------------------------
print("✅ Chatbot ready. Type 'exit' to quit.")
while True:
    q = input("\nYou: ").strip()
    if q.lower() == "exit":
        break

    # Optional quick pre-check (avoids LLM call if nothing is similar)
    try:
        _ = vs.similarity_search(q, k=1)
    except Exception:
        _ = []
    if not _:
        print("Bot: Not in docs.")
        continue

    # RetrievalQA expects {"query": "..."} and maps it to {question} for the prompt.
    out = qa.invoke({"query": q})

    print("\nBot:", out.get("result", "").strip())
    for i, d in enumerate(out.get("source_documents", []), 1):
        src = d.metadata.get("source")
        page = d.metadata.get("page")
        page_str = f" (page {page})" if page is not None else ""
        print(f"  Src {i}: {src}{page_str}")
