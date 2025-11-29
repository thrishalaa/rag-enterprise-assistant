from pathlib import Path
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Base directory of project (root folder)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -----------------------------
# STORAGE FOLDERS
# -----------------------------
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

FAISS_DIR = DATA_DIR / "faiss_index"
FAISS_DIR.mkdir(parents=True, exist_ok=True)

METADATA_PATH = DATA_DIR / "metadata.db"  # SQLite DB for chunk metadata

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# EMBEDDING MODEL
# -----------------------------
# Example in .env → EMBEDDER_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDER_MODEL = os.getenv("EMBEDDER_MODEL")

# -----------------------------
# CHUNKING CONFIG
# -----------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 2000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 300))

# -----------------------------
# LLM MODEL (GGUF FILE PATH)
# -----------------------------
# Example in .env → LLAMA_MODEL_PATH=models/deepseek/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf
llama_env_path = os.getenv("LLAMA_MODEL_PATH")

if llama_env_path:
    LLAMA_MODEL_PATH = BASE_DIR / llama_env_path
else:
    # fallback if env variable missing
    LLAMA_MODEL_PATH = BASE_DIR / "models" / "llama" / "ggml-model-q4_0.bin"

# -----------------------------
# APP SECRET KEY (JWT Auth)
# -----------------------------
# Example in .env → SECRET_KEY=f673a9abcd...
SECRET_KEY = os.getenv("SECRET_KEY")
