from fastapi import FastAPI, UploadFile, File
from pathlib import Path
from typing import List

from src.app.services.ingest_service import ingest_paths
from src.app.services.embedder import Embedder
from src.app.services.vector_store import FaissStore
from src.utils.config import DATA_DIR
from src.app.api.query import router as chat_router
from src.utils.logger import get_logger
from fastapi import Depends
from src.app.auth import get_current_user
from src.app.auth_routes import router as auth_router


import shutil
import os

logger = get_logger(__name__)
logger.info("Starting FastAPI app")

app = FastAPI()

app.include_router(auth_router)
app.include_router(chat_router)

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...),user=Depends(get_current_user)):
    paths = []
    for f in files:
        dest = UPLOAD_DIR / f.filename
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)
        paths.append(str(dest))

    result = ingest_paths(paths)
    return {"status": "ok", "result": result}

@app.get("/search")
def search(q: str, k: int = 5):
    embedder = Embedder()
    q_emb = embedder.embed_query(q)

    dim = len(q_emb)
    store = FaissStore(dim)
    results = store.search(q_emb, k)

    return {"query": q, "results": results}
