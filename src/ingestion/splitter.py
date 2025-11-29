# src/ingestion/splitter.py
from typing import List, Dict
from src.utils.config import CHUNK_SIZE, CHUNK_OVERLAP

def simple_chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> List[str]:
    """
    Memory-safe and loop-safe chunker.
    - Ensures progress on every iteration.
    - Handles short texts, empty strings, and prevents overlap >= chunk_size.
    """
    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        # avoid infinite loops; fall back to non-overlapping
        overlap = max(0, chunk_size // 2)

    chunks: List[str] = []
    n = len(text)
    start = 0
    step = chunk_size - overlap  # positive step guaranteed above

    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start += step

    return chunks


def document_to_chunks(doc: Dict) -> List[Dict]:
    """
    Accepts doc with either:
      - {'pages': [...], 'source': ...}  (pdf)
      - {'content': '...', 'source': ...} (txt/md)
    Returns list of {'text': chunk_text, 'source': source, 'meta': {}}
    """
    chunks = []

    source = doc.get("source", "<unknown>")

    if "pages" in doc and isinstance(doc["pages"], list):
        for i, page in enumerate(doc["pages"]):
            if not page:
                continue
            page_chunks = simple_chunk_text(page)
            for ch in page_chunks:
                chunks.append({"text": ch, "source": source, "meta": {"page": i}})
    else:
        content = doc.get("content", "") or ""
        for ch in simple_chunk_text(content):
            chunks.append({"text": ch, "source": source, "meta": {}})

    return chunks
