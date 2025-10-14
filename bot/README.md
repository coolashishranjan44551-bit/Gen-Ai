# 📘 RAG Chatbot over Your Documents (Hugging Face Inference API)

A simple Retrieval-Augmented Generation (RAG) chatbot that:
1) loads your local docs,  
2) splits them into chunks,  
3) embeds them with Hugging Face Inference API,  
4) stores them in FAISS,  
5) answers questions using retrieved context.

> Works on Windows. Designed for corp networks (proxy/SSL) with small tweaks.

---

## 🗂 Project Structure

my-doc-bot/
├─ bot.py # run this to chat in terminal
├─ data/ # put your PDFs/DOCX/TXT/MD here
├─ index/ # FAISS index is saved here (auto-created)
├─ .env # secrets & config (NOT committed)
├─ .gitignore
└─ requirements.txt