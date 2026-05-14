from __future__ import annotations

from pathlib import Path


class RAGService:
    def ingest(self, documents: list[dict]) -> dict:
        indexed = []
        total_chunks = 0
        for doc in documents:
            chunks = self._chunk(self._read_text(doc))
            total_chunks += len(chunks)
            indexed.append(
                {
                    "asset_id": doc["id"],
                    "source": doc["name"],
                    "asset_type": doc["asset_type"],
                    "chunk_count": len(chunks),
                    "vector_store": "local-placeholder",
                }
            )
        return {
            "status": "indexed",
            "document_count": len(indexed),
            "chunk_count": total_chunks,
            "documents": indexed,
        }

    def retrieve(self, query: str, documents: list[dict]) -> list[dict]:
        chunks = []
        for doc in documents:
            text = self._read_text(doc)
            for index, chunk in enumerate(self._chunk(text)):
                if not query or any(term in chunk.lower() for term in query.lower().split()):
                    chunks.append({"source": doc["name"], "chunk": chunk, "rank": index + 1})
        return chunks[:8]

    def answer(self, query: str, chunks: list[dict], documents: list[dict]) -> dict:
        if not chunks and documents:
            chunks = self.retrieve(query, documents)
        context = " ".join(chunk["chunk"] for chunk in chunks[:3]).strip()
        answer = context[:1200] if context else "No grounded context was found yet. Upload documents or datasets to enrich the answer."
        return {"answer": answer, "citations": [{"source": c["source"], "rank": c["rank"]} for c in chunks[:5]], "confidence": 0.78}

    def nlp_summary(self, query: str, chunks: list[dict]) -> dict:
        text = " ".join(chunk["chunk"] for chunk in chunks)
        words = [word.strip(".,:;!?").lower() for word in text.split()]
        keywords = sorted({w for w in words if len(w) > 6})[:12]
        sentiment = "neutral"
        if any(w in words for w in ["growth", "increase", "positive", "profit"]):
            sentiment = "positive"
        if any(w in words for w in ["risk", "drop", "negative", "loss"]):
            sentiment = "negative"
        return {"summary": text[:700] or query[:700], "sentiment": sentiment, "keywords": keywords, "entities": []}

    def _read_text(self, doc: dict) -> str:
        path = Path(doc["path"])
        if not path.exists():
            return ""
        if doc.get("asset_type") == "pdf":
            try:
                from pypdf import PdfReader

                return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
            except Exception:
                return path.name
        if doc.get("asset_type") in {"text", "csv"}:
            return path.read_text(errors="ignore")[:20000]
        return path.name

    def _chunk(self, text: str, size: int = 900, overlap: int = 120) -> list[str]:
        if not text:
            return []
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
            return splitter.split_text(text)
        except Exception:
            pass
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + size])
            start += max(size - overlap, 1)
        return chunks
