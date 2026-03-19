# RAG System with Llama 3 & Multi-Layer Caching

This project implements a Retrieval-Augmented Generation (RAG) system using **Llama 3**, **Django**, **PostgreSQL (pgvector)**, and **Redis**. It features a multi-layer caching strategy:
1.  **KV Cache (Redis):** Fast, exact-match caching.
2.  **Semantic Cache (PostgreSQL + pgvector):** Caching for similar queries.
3.  **RAG Pipeline:** Context-aware generation using Ollama.

---

## ARCHITECTURE

```
 User Query
    │
    ├─► Layer 1: KV Cache (Redis) → exact match → return instantly
    │
    ├─► Layer 2: Semantic Cache (pgvector) → similar question found (dist < 0.1) → return cached answer
    │
    └─► RAG Pipeline (Cache Miss):
         ├── Embed question (all-MiniLM-L6-v2) 
         ├── Retrieve top 3 docs (cosine similarity in pgvector)
         ├── Generate answer (llama3) 
         └── Store in both caches (Update Redis & QueryLog)

```

---

## Prerequisites

Ensure you have the following installed:
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/)
*   [Ollama](https://ollama.com/) (Running in the system tray)

---

## Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Assignment4_Enfec
```

### 2. Start Infrastructure (Docker)
This project uses Docker to run the database (with vector support) and the cache layer.
```bash
docker-compose up -d
```
*Port mapping: Postgres (5433), Redis (6379).*

### 3. Set up Python Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Prepare the LLM
Pull the Llama 3 model using Ollama:
```bash
ollama pull llama3
```

### 5. Initialize the Database
Run migrations to create the schema:
```bash
cd backend
python manage.py migrate
```

### 6. Ingest Sample Data
Populate the vector database with initial documents:
```bash
python ingest_docs.py
```

---

## Running the Application

You will need two terminals (both with your virtual environment activated).

### Terminal 1: Backend (Django)
```bash
cd backend
python manage.py runserver
```
*API Base: `http://localhost:8000/api`*

### Terminal 2: UI (Streamlit)
```bash
cd ui
streamlit run app.py
```
*The dashboard will open at `http://localhost:8501`.*

---

## Verification & Features

1.  **First Query:** Ask a question in the UI (e.g., *"What is the remote work policy?"*). This will trigger a full **RAG Pipeline** (Cache Miss).
2.  **Exact Match:** Ask the **exact same question** again. It will hit the **KV Cache** (Redis) for near-instant results.
3.  **Semantic Match:** Ask a **similar question** (e.g., *"Can I work from home?"*). It will hit the **Semantic Cache** using vector similarity.
4.  **Analytics:** View real-time metrics on the Streamlit dashboard, including Hit Rate, Average Latency, and Cache distribution (KV vs. Semantic).
