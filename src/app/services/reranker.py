from sentence_transformers import CrossEncoder

class CrossEncoderReranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        print("Loading CrossEncoder:", model_name)
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list):
        """
        candidates: list of dicts { "text": str, "meta": {...}, "id": int, "score": float }
        Returns reranked list sorted by relevance.
        """
        # Prepare query-doc pairs for scoring
        pairs = [(query, c["text"]) for c in candidates]

        # Predict scores
        scores = self.model.predict(pairs)

        # Assign rerank_score
        for i, c in enumerate(candidates):
            c["rerank_score"] = float(scores[i])

        # Sort descending by rerank_score
        return sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
