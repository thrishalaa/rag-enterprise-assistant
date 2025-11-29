from fastapi import APIRouter, Depends, HTTPException
from src.app.services.embedder import Embedder
from src.app.services.vector_store import FaissStore
from src.app.services.llm_client import LLMClient
from src.app.services.reranker import CrossEncoderReranker
from src.app.auth import get_current_user
from src.app.services.cache import SEARCH_CACHE
from src.utils.logger import get_logger
import re
import html
import time

router = APIRouter()
logger = get_logger(__name__)

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "hola", "yo",
    "greetings", "good morning", "good afternoon"
]

def is_greeting(text: str) -> bool:
    t = text.lower().strip()
    return any(t == g or t.startswith(g + " ") for g in GREETING_KEYWORDS)

# ---- NEW: improved prompt template ----
LLM_PROMPT_TEMPLATE = """You are an enterprise knowledge assistant. Use ONLY the information in the Context to answer the Question.

INSTRUCTIONS:
- Read the Context and then answer the Question directly in your own words.
- Keep the answer concise, factual, and actionable (1-6 sentences).
- If the context doesn't contain enough information to answer, respond exactly: "I don't know."
- Do NOT repeat sentences verbatim from the Context (no copy-paste).
- Do NOT output HTML, XML, or any markup.
- Do NOT hallucinate or invent facts.
- If multiple context parts have relevant details, combine them into a short direct answer.

Context:
{context}

Question:
{question}

Answer:
"""

# ---- Utility helpers ----
def clean_text_for_model(text: str) -> str:
    if not text:
        return ""
    # remove HTML tags and control characters, unescape entities
    txt = re.sub(r"<[^>]+>", " ", text)
    txt = html.unescape(txt)
    txt = re.sub(r"[\r\n\t]+", " ", txt)
    txt = " ".join(txt.split())
    return txt.strip()

def choose_sources(chunks):
    """Return unique source list preserving order and avoiding long filesystem paths."""
    sources = []
    seen = set()
    for c in chunks:
        src = c.get("meta", {}).get("source") or c.get("meta", {}).get("filename") or ""
        if not src:
            continue
        # normalize filename only
        fname = src.split("/")[-1].split("\\")[-1]
        if fname not in seen:
            seen.add(fname)
            sources.append(fname)
    return sources

@router.get("/chat")
def chat(q: str, user=Depends(get_current_user)):
    """
    Improved chat endpoint with:
    - better prompt
    - score thresholding + deduplication
    - tightened context size (small, high-quality)
    - final answer validation
    """
    start_time = time.time()
    try:
        if not q or not q.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        q = q.strip()
        logger.info(f"[CHAT] user={user.get('username')} query={q}")

        # quick greeting shortcut
        if is_greeting(q):
            return {"query": q, "answer": "Hello! I'm your enterprise knowledge assistant. How can I help you today?", "sources": []}

        # 1) embed query
        embedder = Embedder()
        q_emb = embedder.embed_query(q)
        dim = len(q_emb)

        # 2) FAISS search (with cache)
        cache_key = f"search::{q}"
        cached = SEARCH_CACHE.get(cache_key)
        if cached:
            logger.info("Cache hit for search")
            faiss_hits = cached
        else:
            store = FaissStore(dim)
            # request a few more candidates to give reranker options
            results = store.search(q_emb, k=20)
            faiss_hits = results[0]
            SEARCH_CACHE.set(cache_key, faiss_hits)

        # 3) build candidate list with basic filtering
        candidates = []
        for h in faiss_hits:
            text = (h.get("text") or "").strip()
            if not text or len(text) < 40:
                continue
            candidates.append({
                "id": h.get("id"),
                "text": text,
                "meta": h.get("meta", {}),
                "faiss_score": float(h.get("score", 0.0))
            })

        if not candidates:
            logger.info("No valid candidates found")
            return {"query": q, "answer": "I don't know.", "sources": []}

        # 4) rerank using cross-encoder
        reranker = CrossEncoderReranker()
        reranked = reranker.rerank(q, candidates)  # expected: list of dicts with 'text' and 'score' keys

        # 5) dynamic score thresholding to remove weakly relevant chunks
        # compute top_score and keep chunks >= fraction of top_score
        top_score = max([c.get("score", 0.0) for c in reranked]) if reranked else 0.0
        threshold = max(0.10, 0.45 * top_score)  # keep this tunable
        filtered = [c for c in reranked if c.get("score", 0.0) >= threshold]

        if not filtered:
            # fallback to top 2 from reranked if filtering removed everything
            filtered = reranked[:2]

        # 6) deduplicate very similar chunks (exact-text dedupe)
        unique_texts = set()
        unique_chunks = []
        for c in filtered:
            t = clean_text_for_model(c.get("text", ""))
            # simple dedupe by exact text; could add fuzzy dedupe later
            if t and t not in unique_texts:
                unique_texts.add(t)
                unique_chunks.append({**c, "clean_text": t})

        # 7) take the top N (small) high quality chunks to form context
        # keep max 2-3 high quality chunks to avoid noise
        TOP_K = 3
        top_chunks = unique_chunks[:TOP_K]

        # if still empty, fallback to best FAISS hits
        if not top_chunks and candidates:
            top_chunks = [{"clean_text": clean_text_for_model(c["text"]), "meta": c.get("meta", {})} for c in candidates[:2]]

        # 8) build context (sanitize and truncate)
        context_parts = []
        for c in top_chunks:
            txt = c.get("clean_text") or clean_text_for_model(c.get("text", ""))
            # truncate each chunk to a safe length (e.g., 1500 chars) to keep prompt length reasonable
            if len(txt) > 1500:
                txt = txt[:1500]
            context_parts.append(txt)
        context = "\n\n".join(context_parts)
        if len(context) > 4500:
            context = context[:4500]  # safety truncation

        logger.debug("Context sent to LLM:\n%s", context)

        # 9) build final prompt and call LLM
        prompt = LLM_PROMPT_TEMPLATE.format(context=context, question=q)

        llm = LLMClient()
        raw_answer = llm.generate(prompt)  # returns cleaned plain text per LLMClient contract

        # 10) final sanitization & quality checks
        answer = (raw_answer or "").strip()
        # remove any stray tags or angle brackets as extra safety
        answer = re.sub(r"<[^>]+>", "", answer)
        answer = answer.replace("&lt;", "").replace("&gt;", "")
        answer = " ".join(answer.split())

        # Reject answers that are clearly placeholders or too short / vague
        if not answer or len(answer) < 15 or answer.lower().startswith("i don't know") or "the context" in answer.lower():
            logger.info("LLM output was low quality or insufficient, returning fallback")
            return {"query": q, "answer": "I don't know.", "sources": choose_sources(top_chunks)}

        # 11) return sources (filename only)
        sources = choose_sources(top_chunks)

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] Answered query in {elapsed:.2f}s - query='{q}'")

        return {
            "query": q,
            "answer": answer,
            "sources": sources
        }

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[ERROR] chat failed after {elapsed:.2f}s: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
