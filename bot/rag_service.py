"""Shared Retrieval-Augmented Generation service utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import (
    ChatHuggingFace,
    HuggingFaceEndpoint,
    HuggingFaceEndpointEmbeddings,
)
from langchain_unstructured import UnstructuredLoader

# Load environment variables once per process.
load_dotenv()


class RAGService:
    """Encapsulates document indexing and question-answering logic."""

    def __init__(
        self,
        *,
        data_dir: Optional[os.PathLike[str]] = None,
        index_dir: Optional[os.PathLike[str]] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parent
        self.data_dir = Path(data_dir or base_dir / "data")
        self.index_dir = Path(index_dir or base_dir / "index")

        self._hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not self._hf_token:
            raise RuntimeError(
                "Set HUGGINGFACEHUB_API_TOKEN in your environment or .env file before starting the chatbot."
            )

        self.embedding_model = embedding_model or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.llm_model = llm_model or os.getenv(
            "LLM_MODEL", "HuggingFaceH4/zephyr-7b-beta"
        )

        self._embeddings = HuggingFaceEndpointEmbeddings(
            model=self.embedding_model,
            huggingfacehub_api_token=self._hf_token,
        )

        self._vectorstore = self._load_or_build_vectorstore()
        self._qa = self._build_retrieval_chain(self._vectorstore)

    # ------------------------------------------------------------------
    # Index construction helpers
    # ------------------------------------------------------------------
    def _load_documents(self) -> List:
        if not self.data_dir.is_dir():
            raise RuntimeError(
                f"{self.data_dir} does not exist. Add PDFs/DOCX/TXT/MD files before starting the server."
            )

        documents = []
        for path in sorted(self.data_dir.iterdir()):
            if not path.is_file():
                continue
            lower_name = path.name.lower()
            if lower_name.endswith(".pdf"):
                documents.extend(PyPDFLoader(str(path)).load())
            elif lower_name.endswith(".docx"):
                documents.extend(Docx2txtLoader(str(path)).load())
            else:
                documents.extend(UnstructuredLoader(str(path)).load())

        if not documents:
            raise RuntimeError(
                f"No documents found in {self.data_dir}. Add content and restart the server."
            )

        return documents

    def _chunk_documents(self, documents: List) -> List:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        return splitter.split_documents(documents)

    def _load_or_build_vectorstore(self) -> FAISS:
        documents = self._load_documents()
        chunks = self._chunk_documents(documents)

        self.index_dir.mkdir(parents=True, exist_ok=True)
        existing = [
            name
            for name in self.index_dir.iterdir()
            if name.suffix in {".faiss", ".pkl"}
        ]

        if existing:
            return FAISS.load_local(
                str(self.index_dir),
                self._embeddings,
                allow_dangerous_deserialization=True,
            )

        vectorstore = FAISS.from_documents(chunks, self._embeddings)
        vectorstore.save_local(str(self.index_dir))
        return vectorstore

    # ------------------------------------------------------------------
    # Question answering
    # ------------------------------------------------------------------
    def _build_retrieval_chain(self, vectorstore: FAISS) -> RetrievalQA:
        chat_llm = ChatHuggingFace(
            llm=HuggingFaceEndpoint(
                repo_id=self.llm_model,
                task="conversational",
                huggingfacehub_api_token=self._hf_token,
                temperature=0.0,
                max_new_tokens=512,
            )
        )

        system_prompt = (
            "Answer ONLY using the provided context. If the answer is missing, respond "
            "with 'Not in docs.' Keep replies concise."
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt + "\n\nContext:\n{context}"),
                ("human", "{question}"),
            ]
        )

        return RetrievalQA.from_chain_type(
            llm=chat_llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            chain_type="stuff",
            chain_type_kwargs={
                "prompt": prompt,
                "document_variable_name": "context",
            },
            return_source_documents=True,
        )

    def answer(self, question: str) -> Tuple[str, List[Dict[str, Optional[str]]]]:
        """Return the model's answer and a list of cited sources."""
        cleaned = question.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty.")

        try:
            preview = self._vectorstore.similarity_search(cleaned, k=1)
        except Exception:
            preview = []
        if not preview:
            return "Not in docs.", []

        result = self._qa.invoke({"query": cleaned})
        answer = result.get("result", "").strip() or "Not in docs."

        sources: List[Dict[str, Optional[str]]] = []
        for doc in result.get("source_documents", []):
            snippet = doc.page_content.replace("\n", " ")[:280]
            metadata: Dict[str, Optional[str]] = {
                "source": doc.metadata.get("source"),
            }
            page = doc.metadata.get("page")
            if page is not None:
                metadata["page"] = str(page)
            if snippet:
                metadata["snippet"] = snippet
            sources.append(metadata)

        return answer, sources


__all__ = ["RAGService"]
