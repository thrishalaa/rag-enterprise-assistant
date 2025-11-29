
# 📘 Enterprise Knowledge Base – Local RAG Assistant

A fully offline, open-source **Retrieval-Augmented Generation (RAG)** system built with **FastAPI**, **FAISS**, **Sentence-Transformers**, and a **local LLM** using llama.cpp (DeepSeek-R1 Distill Qwen 1.5B GGUF).
Supports document ingestion, semantic search, reranking, evaluation metrics, and a complete Streamlit UI.

---

## 🚀 Features

* 🔒 **Completely offline** – Runs fully on CPU with local GGUF model
* 📄 **Document ingestion** (PDF, TXT, Markdown)
* ✂️ **Text chunking** with configurable size & overlap
* 🔍 **Semantic search** using FAISS vector database
* 🧠 **RAG pipeline** with context-grounded answering using local LLM
* 🎯 **Reranking** using Cross-Encoder (ms-marco-MiniLM-L6-v2)
* 📊 **Evaluation tools**: Recall@k, Precision@k, MRR, Human eval logs
* 🖥️ **Streamlit UI** for uploading documents and chatting with the assistant
* 🔐 **Configurable via `.env`** (model path, embedding model, etc.)

---

## 🏗 Architecture Overview

```
User → Streamlit UI → FastAPI Backend → FAISS Vector Store
                                 ↓
                         Cross-Encoder Reranker
                                 ↓
                       Local LLM via llama.cpp
                                 ↓
                            Final Answer
```

---

## 📁 Project Structure

```
project/
│
├─ src/
│   ├─ app/
│   │   ├─ api/               # /chat, /ingest, /search endpoints
│   │   ├─ services/          # embedder, vector store, LLM client, reranker
│   │   └─ main.py            # FastAPI app entrypoint
│   ├─ ingestion/             # loaders, text splitter
│   ├─ evaluation/            # recall@k, MRR, human evaluation logs
│   └─ utils/                 # config, logger
│
├─ ui/
│   └─ streamlit_app.py       # Web UI for upload & chat
│
├─ models/                    # GGUF models (not included)
├─ data/                      # FAISS index, metadata, uploads
├─ .env                       # environment variables (not included)
├─ .gitignore
├─ requirements.txt
└─ README.md
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/rag-enterprise-assistant.git
cd rag-enterprise-assistant
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

### 3. Download a GGUF model

Example (DeepSeek-R1 Distill Qwen 1.5B Q4_K_M):

Place the file here:

```
models/deepseek/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf
```

### 4. Create a `.env` file

```
EMBEDDER_MODEL=sentence-transformers/all-MiniLM-L6-v2
LLAMA_MODEL_PATH=models/deepseek/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf
SECRET_KEY=your_secret_key_here
CHUNK_SIZE=2000
CHUNK_OVERLAP=300
```

---

## ▶️ Running the Application

### Start the FastAPI backend:

```
uvicorn src.app.main:app --reload --port 8000
```

### Start the Streamlit UI:

```
streamlit run ui/streamlit_app.py
```

The UI runs at:

👉 [http://localhost:8501](http://localhost:8501)

Backend runs at:

👉 [http://localhost:8000](http://localhost:8000)

---

## 📤 Ingest Documents

Use Streamlit UI or:

```
POST /ingest
```

---

## 🔍 Semantic Search

```
GET /search?q=your question
```

---

## 💬 Chat with the Assistant

```
GET /chat?q=your question
```

Uses:

* FAISS top-20 retrieval
* Cross-encoder reranking
* LLM inference via llama.cpp
* Final grounded answer

---

## 📈 Evaluation Tools

Run retrieval evaluation:

```
python src/evaluation/retrieval_eval.py
```

Includes:

* Recall@k
* Precision@k
* MRR
* FAISS vs Reranker comparison

Human evaluation logs stored in:

```
evaluation/human_eval_log.jsonl
```

---

## 🧩 Tech Stack

* **FastAPI** – backend API
* **FAISS** – vector database
* **Sentence-Transformers** – embeddings
* **Cross-Encoder** – reranking
* **llama.cpp / llama-cpp-python** – local LLM
* **Streamlit** – UI
* **Python** – core language

---

## ⚠️ Note

Model files (`.gguf`) and FAISS index files are **not included** due to size.

---

## ✨ Future Improvements

* PDF preview in UI
* Chat history
* Multi-user sessions
* Admin dashboard
* Improved ranking with multi-vector retrieval

---

