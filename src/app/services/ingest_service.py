from src.ingestion.loaders import load_document 
from src.ingestion.splitter import document_to_chunks 
from src.app.services.embedder import Embedder 
from src.app.services.vector_store import FaissStore 
from src.utils.config import EMBEDDER_MODEL 
import numpy as np

def ingest_paths(paths: list):
    # 1) load raw docs
    docs = [load_document(p) for p in paths]

    # 2) split into chunks
    all_chunks = []
    metadatas = []
    texts = []        # NEW

    print("STEP 2: Splitting into chunks...", flush=True)
    for doc in docs:
        chunks = document_to_chunks(doc)
        print(f"  Loaded {len(chunks)} chunks from {doc['source']}", flush=True)

        for i, c in enumerate(chunks):
            meta = {"source": c["source"], "chunk_index": i}
            metadatas.append(meta)
            texts.append(c["text"])   # IMPORTANT
            all_chunks.append(c["text"])

    # 3) embed chunks
    print("STEP 3: Embedding chunks...", flush=True)
    embedder = Embedder()
    embeddings = embedder.embed_documents(all_chunks)
    print("  Embeddings generated.", flush=True)

    dim = embeddings.shape[1]

    # 4) add to faiss
    print("STEP 4: Saving to FAISS...", flush=True)
    store = FaissStore(dim)
    store.add(embeddings, metadatas, texts)
    print("  Added to FAISS.", flush=True)

    return {"ingested": len(all_chunks)}
