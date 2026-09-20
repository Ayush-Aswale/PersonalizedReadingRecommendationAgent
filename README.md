# Personalized Reading Recommendation Agent

An **Agentic AI** system that provides personalized book recommendations through natural conversation. Built with **LangChain**, **Groq LLM**, **React**, and **Gradio** as a college project demonstrating genuine agentic AI concepts.

---

## Architecture

```
Browser → React UI → /api/* → Flask API → LangChain Agent → Groq LLM
                                    ↕                ↕
                              SQLite/Postgres    Tool Calls
                              Chroma Vector DB   (search, rank, profile)
```

### Key Components

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | Groq (`openai/gpt-oss-120b`) | Natural language understanding and response generation |
| **Agent Framework** | LangChain + tool-calling | Orchestrates tools, memory, and reasoning |
| **Recommendation Engine** | Deterministic scorer + ranker | Transparent, explainable scoring separate from LLM |
| **Vector Store** | Chroma + sentence-transformers | Semantic "vibe" search via RAG |
| **Database** | SQLite (local) / Postgres (prod) | User profiles, history, feedback, book catalog |
| **Frontend** | React + Vite | Premium dark-themed chat UI with glassmorphism |
| **API** | Flask | RESTful endpoints for chat, profile, history |
| **Shell** | Gradio | Wraps everything for local development |

### Agentic AI Concepts Demonstrated

1. **Tool-calling agent** — LLM decides which tools to invoke (search, profile, feedback)
2. **RAG** — Semantic similarity search over book embeddings
3. **Conversation memory** — Sliding-window context across turns
4. **Deterministic scorer** — Transparent ranking separate from LLM generation
5. **Feedback loop** — User likes/dislikes are persisted and influence future recommendations

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend build)
- A [Groq API key](https://console.groq.com/keys)

### 1. Clone & Install

```bash
git clone <repo-url>
cd PersonalizedReadingRecommendationAgent

# Python dependencies
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Build Dataset & Database

```bash
# Generate the ~800-book dataset from Open Library
python scripts/generate_books.py

# Ingest into SQLite + Chroma vector store
python scripts/build_database.py
```

### 4. Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. Run

```bash
python app.py
```

This starts:
- **Flask API** on `http://127.0.0.1:5000`
- **Gradio UI** on `http://127.0.0.1:7860`

For React dev mode with hot reload:
```bash
cd frontend
npm run dev    # Runs on http://localhost:5173, proxies /api to Flask
```

---

## Project Structure

```
PersonalizedReadingRecommendationAgent/
├── app.py                      # Entry point (Gradio + Flask)
├── requirements.txt
├── .env.example
├── .gitignore
│
├── config/
│   └── settings.py             # Centralized configuration
│
├── agent/
│   ├── orchestrator.py         # LangChain AgentExecutor assembly
│   └── prompts.py              # System prompts with grounding rules
│
├── tools/
│   ├── book_tools.py           # search_books, get_book_details, find_similar_books
│   ├── user_tools.py           # get_user_profile, update_preference, record_feedback
│   └── composite_tools.py      # get_recommendation_candidates (all-in-one)
│
├── recommender/
│   ├── scorer.py               # Deterministic multi-signal scoring
│   └── ranker.py               # Candidate ranking pipeline
│
├── rag/
│   └── vector_store.py         # Chroma + HuggingFace embeddings
│
├── database/
│   └── db.py                   # Dual-mode repository (SQLite / Postgres)
│
├── memory/
│   └── conversation_memory.py  # Sliding-window conversation memory
│
├── data/
│   ├── raw/books_raw.csv       # ~800-book curated dataset
│   ├── ingest.py               # CSV → DB + Vector Store ingestion
│   └── README.md               # Dataset documentation
│
├── api/
│   └── app.py                  # Flask REST API
│
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── App.jsx             # Main chat UI
│   │   └── index.css           # Glassmorphism dark theme
│   └── vite.config.js          # Dev proxy to Flask
│
├── tests/
│   ├── conftest.py
│   ├── test_scorer.py
│   ├── test_db.py
│   ├── test_tools.py
│   └── test_agent_flow.py
│
├── utils/
│   ├── validators.py
│   └── logging_utils.py
│
└── scripts/
    ├── generate_books.py       # Dataset generation from Open Library
    └── build_database.py       # DB + Vector Store build script
```

---

## Running Tests

```bash
# All tests (agent test skipped without GROQ_API_KEY)
.venv\Scripts\pytest -v

# With agent integration test
GROQ_API_KEY=your_key .venv\Scripts\pytest -v
```

---

## Configuration

All settings are managed through `.env` (never committed). See [.env.example](.env.example) for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *(required)* | Your Groq API key |
| `GROQ_MODEL_NAME` | `openai/gpt-oss-120b` | LLM model (configurable) |
| `DATABASE_PATH` | `database/app.db` | Local SQLite path |
| `CHROMA_PERSIST_DIR` | `database/chroma` | Local vector store path |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `MAX_RECOMMENDATIONS` | `5` | Max books per response |

---

## Deployment (Vercel)

The project supports Vercel deployment with the React frontend + Flask API as a Python serverless function:

1. Push to GitHub
2. Connect to Vercel
3. Set environment variables (`GROQ_API_KEY`, `DATABASE_URL`, etc.)
4. Deploy

See `vercel.json` for the routing configuration.

---

## Dataset

~800 books across 10 genres, sourced from the **Open Library API**. See [data/README.md](data/README.md) for field documentation including which fields are derived/synthetic.

---

## License

Academic project — MIT License.
