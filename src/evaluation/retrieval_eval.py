import json
import os
from pathlib import Path
from src.app.services.embedder import Embedder
from src.app.services.vector_store import FaissStore
from src.app.services.reranker import CrossEncoderReranker


# ---------------------------
# NORMALIZATION FIX (IMPORTANT)
# ---------------------------
def normalize_source(x: str) -> str:
    """Convert full absolute paths into clean filenames for comparison."""
    if not x:
        return ""
    return os.path.basename(x).strip().lower()


# ---- METRIC FUNCTIONS ----

def recall_at_k(retrieved, gt, k):
    return 1.0 if any(src in gt for src in retrieved[:k]) else 0.0

def precision_at_k(retrieved, gt, k):
    retrieved_k = retrieved[:k]
    return sum(1 for x in retrieved_k if x in gt) / k

def mrr(retrieved, gt):
    for i, src in enumerate(retrieved):
        if src in gt:
            return 1 / (i + 1)
    return 0


# ---- LOAD eval queries ----

def load_eval_queries():
    path = Path(__file__).parent / "queries.json"
    with open(path, "r") as f:
        return json.load(f)


# ---- MAIN EVAL ----

def evaluate_model(top_k=5):
    queries = load_eval_queries()
    embedder = Embedder()
    reranker = CrossEncoderReranker()

    avg_recall, avg_precision, avg_mrr = [], [], []

    for qinfo in queries:
        q = qinfo["question"]
        # Normalize ground truth sources
        gt = [normalize_source(s) for s in qinfo["relevant_sources"]]

        print("\n=== QUERY:", q, "===")

        # embed
        q_emb = embedder.embed_query(q)
        dim = len(q_emb)
        store = FaissStore(dim)

        results = store.search(q_emb, k=50)
        hits = results[0]

        retrieved_sources = []
        candidates = []

        # Load text + normalized source
        for h in hits:
            meta = h["meta"]
            source = normalize_source(meta.get("source"))
            text = h.get("text")

            retrieved_sources.append(source)
            candidates.append({"text": text, "meta": meta})

        # --- FAISS baseline metrics ---
        r = recall_at_k(retrieved_sources, gt, top_k)
        p = precision_at_k(retrieved_sources, gt, top_k)
        m = mrr(retrieved_sources, gt)

        print("FAISS: Recall:", r, "Precision:", p, "MRR:", m)

        # --- Rerank ---
        reranked = reranker.rerank(q, candidates)
        reranked_sources = [
            normalize_source(c["meta"]["source"]) 
            for c in reranked
        ]

        r2 = recall_at_k(reranked_sources, gt, top_k)
        p2 = precision_at_k(reranked_sources, gt, top_k)
        m2 = mrr(reranked_sources, gt)

        print("RERANK:", "Recall:", r2, "Precision:", p2, "MRR:", m2)

        # store FAISS scores (not reranked)
        avg_recall.append(r)
        avg_precision.append(p)
        avg_mrr.append(m)

    print("\n===== FINAL AVERAGE METRICS =====")
    print("Recall@k:", sum(avg_recall) / len(avg_recall))
    print("Precision@k:", sum(avg_precision) / len(avg_precision))
    print("MRR:", sum(avg_mrr) / len(avg_mrr))


if __name__ == "__main__":
    evaluate_model()
