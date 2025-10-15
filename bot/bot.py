"""Simple terminal interface for the RAG chatbot."""

from __future__ import annotations

from bot.rag_service import RAGService


def main() -> None:
    service = RAGService()
    print("✅ Chatbot ready. Type 'exit' to quit.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue
        answer, sources = service.answer(question)
        print("\nBot:", answer)
        for idx, source in enumerate(sources, 1):
            label = source.get("source") or f"Source {idx}"
            page = source.get("page")
            page_suffix = f" (page {page})" if page else ""
            snippet = source.get("snippet")
            print(f"  Src {idx}: {label}{page_suffix}")
            if snippet:
                print(f"    {snippet}")


if __name__ == "__main__":
    main()
