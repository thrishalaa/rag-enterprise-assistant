from sentence_transformers import SentenceTransformer
from src.utils.config import EMBEDDER_MODEL
from src.app.services.cache import EMBED_CACHE
import numpy as np

class Embedder:
    def __init__(self, model_name: str = EMBEDDER_MODEL):
        print("Loading embedder:", model_name)
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list) -> np.ndarray:
        # returns numpy array (n, d)
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings

    def embed_query(self, text: str):
        cache_hit = EMBED_CACHE.get(("q", text))
        if cache_hit is not None:
            return cache_hit
        emb = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)[0]
        EMBED_CACHE.set(("q", text), emb)
        return emb
