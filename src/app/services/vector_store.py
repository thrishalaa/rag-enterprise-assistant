from typing import List, Dict
import faiss
import numpy as np
from pathlib import Path
import json
from sqlitedict import SqliteDict
from src.utils.config import FAISS_DIR, METADATA_PATH

FAISS_DIR.mkdir(parents=True, exist_ok=True)

class FaissStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.index_path = FAISS_DIR / "index.faiss"
        self.meta_db_path = METADATA_PATH

        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with SqliteDict(self.meta_db_path, autocommit=True) as db:
                self._id_counter = db.get("_id_counter", 0)
        else:
            self.index = faiss.IndexFlatIP(dim)
            self._id_counter = 0

    def add(self, embeddings: np.ndarray, metadatas: List[Dict], texts: List[str]):
        n = embeddings.shape[0]
        ids = np.arange(self._id_counter, self._id_counter + n).astype(np.int64)

        # Add vectors
        self.index.add(embeddings)

        # Save metadata + text
        with SqliteDict(self.meta_db_path, autocommit=True) as db:
            for i, mid in enumerate(ids):
                record = metadatas[i].copy()
                record["text"] = texts[i]     # store chunk text
                db[str(int(mid))] = json.dumps(record)
            db["_id_counter"] = int(ids[-1] + 1)

        self._id_counter += n
        self.save()

    def save(self):
        faiss.write_index(self.index, str(self.index_path))

    def search(self, query_emb: np.ndarray, k: int = 5):
        if query_emb.ndim == 1:
            q = query_emb.reshape(1, -1)
        else:
            q = query_emb

        D, I = self.index.search(q, k)
        results = []

        with SqliteDict(self.meta_db_path, autocommit=True) as db:
            for row_idx in range(I.shape[0]):
                hits = []
                for col_idx in range(I.shape[1]):
                    idx = int(I[row_idx, col_idx])
                    if idx == -1:
                        continue

                    meta_json = db.get(str(idx), None)
                    meta = json.loads(meta_json) if meta_json else {}

                    hits.append({
                        "id": idx,
                        "score": float(D[row_idx, col_idx]),
                        "text": meta.get("text", ""),         # chunk content
                        "source": meta.get("source", ""),     # pdf name
                        "meta": meta
                    })

                results.append(hits)

        return results
