# Personalized Reading Recommendation Agent — Software Architecture Blueprint

**Prepared for:** 2nd-year CS/Data Science Agentic AI course project
**Stack:** Python · LangChain · Groq API · Gradio + React (custom components) · SQLite + Chroma
**Author role:** Senior AI Software Architect (design-only; no implementation code)

---

## 1. Project Overview

### What the application does
A conversational AI agent that recommends books based on a user's stated genre/author preferences, reading level, mood, reading goals, and free-form natural-language requests ("something short and uplifting after a long week," "give me a sci-fi book like *The Martian* but easier to read"). The agent reasons about what the user is asking for, decides which internal tools to call, retrieves candidate books from a real dataset, filters out books the user has already read or disliked, ranks the remainder against the user's profile, and returns a small set of recommendations each with a grounded, book-specific explanation of *why* it was chosen.

### Target user
A casual-to-moderate reader who doesn't want to browse catalogs or star ratings manually and would rather describe what they're in the mood for and let a system that "knows them" narrow it down. In the demo, this is played by the student/faculty evaluator.

### Problem it solves
Generic recommendation widgets ("customers also bought") ignore mood, current goals, and reading level, and can't be reasoned with in natural language. This agent solves that by combining structured personalization data (profile, history, feedback) with LLM reasoning and tool-grounded retrieval, so recommendations are both personalized and explainable.

### Why this qualifies as Agentic AI (not just an LLM wrapper)
The system is agentic because the LLM does not answer from memory — it must **decide**, at each turn, which tools to call, in what order, and how to combine their outputs, before producing a final answer:
- It performs multi-step planning (intent → profile lookup → search → filter → rank → explain).
- It uses external tools it can choose or skip (search, history lookup, similarity lookup, preference updates).
- It maintains state across turns (memory of profile, history, feedback).
- It grounds its output in retrieved data instead of generating facts from parametric knowledge (no hallucinated books).
- It closes a feedback loop: user reactions change future tool outputs (via a preference/feedback store), not just future prompt text.

### How this differs from a normal book recommendation website
| Normal recommendation site | This agent |
|---|---|
| Fixed filters/dropdowns | Natural-language requests interpreted by an LLM |
| Static "similar items" algorithm | Agent dynamically decides which tools/signals matter per request |
| No reasoning trace visible | UI exposes the agent's tool-calling steps ("Agent Activity" panel) |
| Recommendations are opaque | Every recommendation includes a generated, grounded explanation |
| Feedback usually just a rating stored silently | Feedback explicitly re-enters the agent's next reasoning pass |

### Main user journey
1. User opens the app, creates or selects a profile.
2. User sets initial preferences (genres, favorite authors, reading level, preferred length) or skips and lets the agent infer them conversationally.
3. User chats naturally: asks for a recommendation, mentions a mood, references a book they liked.
4. Agent plans → calls tools → retrieves grounded candidates → ranks → responds with cards + explanations.
5. User opens a book, likes/dislikes it, or marks it read.
6. Feedback updates memory; the next recommendation reflects it.
7. User can review reading history, favorites, and past recommendations at any time.

---

## 2. Core Features

### A. MVP / Mandatory Features
| # | Feature | Notes |
|---|---|---|
| 1 | User profile creation & selection | Local, simple (no auth needed) |
| 2 | Genre preferences, favorite authors, reading level, preferred length | Structured onboarding form |
| 3 | Natural-language recommendation requests | Core agent entry point |
| 4 | Book search (title/author/genre) | `search_books` tool |
| 5 | Personalized recommendations | Core ranking pipeline |
| 6 | Recommendation explanations ("Why this book?") | Grounded, generated per book |
| 7 | Reading history (mark as read) | Used for previously-read filtering |
| 8 | Favorites | Simple bookmarking |
| 9 | Like/dislike feedback | Feeds personalization |
| 10 | Previously-read filtering | Agent excludes read books automatically |
| 11 | Agent activity/tool trace shown in UI | Demonstrates agentic behavior for the viva |
| 12 | Local fallback dataset (no internet dependency except Groq) | Required by project constraints |

### B. Advanced Features
| # | Feature | Notes |
|---|---|---|
| 13 | Mood-based recommendations | Mood is a first-class signal in scoring |
| 14 | Similar-book recommendations ("more like this") | Uses embeddings/vector similarity |
| 15 | Long-term preference memory that adapts from feedback | Not just static onboarding values |
| 16 | Recommendation history log | Distinct from reading history |
| 17 | Session persistence across app restarts | SQLite-backed |
| 18 | Reading goals (e.g., "read more nonfiction this month") | Soft scoring signal |

### C. Optional / Stretch Features
| # | Feature | Notes |
|---|---|---|
| 19 | Adaptive reading-level detection from feedback patterns | Nice viva talking point, low priority |
| 20 | Multi-user comparison / "reading twins" | Skip unless time allows |
| 21 | Export reading history to CSV | Trivial add-on |
| 22 | Voice input | Out of scope unless explicitly required |
| 23 | Book cover image fetching (Open Library covers API) | Optional visual polish, has internet dependency — must degrade gracefully offline |

**Recommendation:** Build all of A, build 13–17 of B if time allows, treat C as bonus only after everything else works and is tested.

---

## 3. Agentic AI Architecture

### High-level components
```
┌─────────────────────────────────────────────────────────────┐
│                         USER (UI)                            │
└───────────────────────────┬───────────────────────────────────┘
                             │ natural language / UI actions
┌───────────────────────────▼───────────────────────────────────┐
│                     AGENT ORCHESTRATOR                        │
│   LangChain Tool-Calling Agent (AgentExecutor)                │
│   - System prompt (persona + rules)                           │
│   - ChatGroq LLM (tool-calling capable model)                 │
│   - ConversationBufferMemory (short-term)                     │
│   - Bound tools (see Section 4)                                │
└───────────────────────────┬───────────────────────────────────┘
        │ tool calls         │ reads/writes            │ reads
┌───────▼────────┐  ┌────────▼─────────┐      ┌─────────▼────────┐
│ Book Retrieval  │  │  User Data Store  │      │  Recommendation  │
│ (SQLite + Chroma│  │  (SQLite: users,  │      │  Scorer/Ranker   │
│  vector search) │  │  prefs, history,  │      │  (pure Python,   │
│                 │  │  favorites,       │      │  not an LLM call)│
│                 │  │  feedback)        │      │                  │
└─────────────────┘  └───────────────────┘      └──────────────────┘
```

### What the agent decides autonomously
Improved decision flow (grounding ranking outside the LLM, which is safer and more explainable for a college project):

```
User message
   → LLM interprets intent + extracts constraints (genre, mood, length, "similar to X", explicit exclusions)
   → Agent decides: does this need profile context? (usually yes) → calls get_user_profile / get_reading_history
   → Agent decides: does this need a fresh search or a similarity lookup?
        - new topic/genre/mood request → search_books / get_recommendation_candidates
        - "more like X" request → find_similar_books
   → Agent receives candidate list (grounded book records, not invented)
   → Agent calls filtering/ranking logic (deterministic Python function exposed as a tool,
     OR done in backend directly before final LLM pass — see design decision below)
   → Agent excludes previously-read / previously-disliked books
   → Agent (LLM) writes a short natural-language explanation per surviving top-N candidate,
     using ONLY the fields provided in the candidate record (never inventing details)
   → Agent optionally calls update_user_preference / record_feedback if the user expressed
     a new like/dislike/preference conversationally
   → Final structured response returned to UI (list of book objects + explanations + agent trace)
```

**Key design decision:** Ranking/scoring is implemented as **deterministic Python** (a scoring function, Section 7), not left to the LLM. The LLM's job is intent parsing, tool orchestration, and explanation generation — not arithmetic ranking. This keeps recommendations grounded, reproducible, and easy to defend in a viva ("the LLM cannot fabricate a ranking; the score is computed in code and the LLM only explains it").

### Components summary
| Component | Choice |
|---|---|
| LLM | Groq-hosted Llama 3.x (tool-calling capable), via `langchain-groq` |
| Agent type | LangChain `create_tool_calling_agent` + `AgentExecutor` |
| System prompt | Persona + strict grounding rules (Section 17) |
| Tools | 8 tools, Section 4 |
| Memory | `ConversationBufferWindowMemory` (short-term) + SQLite (long-term) |
| Retrieval | SQLite for structured filtering + Chroma for semantic "similar book" search |
| Book database | Local CSV/SQLite dataset, Section 6 |
| Recommendation logic | Deterministic scorer (Python), Section 7 |
| Feedback mechanism | `record_feedback` tool → SQLite → feeds future scoring |

---

## 4. Agent Tools

All tools are implemented as LangChain `@tool`-decorated functions with typed inputs (Pydantic models) so Groq's tool-calling can invoke them reliably.

### 4.1 `search_books` (Mandatory)
- **Purpose:** Structured search over the book dataset by genre, author, keyword, and/or reading-level/length filters.
- **Inputs:** `query: str` (optional keyword), `genre: Optional[str]`, `author: Optional[str]`, `max_length_pages: Optional[int]`, `reading_level: Optional[str]`
- **Outputs:** List of up to 20 book records `{book_id, title, author, genre, pages, reading_level, avg_rating, short_description}`
- **When used:** New topic/genre request, or as the first broad candidate pool for any recommendation.
- **Example call:** `search_books(genre="science fiction", max_length_pages=300)`
- **Example result:** `[{"book_id": "B0142", "title": "Project Hail Mary", "author": "Andy Weir", "genre": "Science Fiction", "pages": 476, "reading_level": "medium", "avg_rating": 4.7, "short_description": "A lone astronaut must save Earth..."}]`

### 4.2 `get_book_details` (Mandatory)
- **Purpose:** Fetch the full record for one book (for the detail view / grounding an explanation).
- **Inputs:** `book_id: str`
- **Outputs:** Full book record including full description, tags, ISBN if present.
- **When used:** User clicks a book, or agent needs full detail before writing an explanation.
- **Example call:** `get_book_details(book_id="B0142")`

### 4.3 `get_user_profile` (Mandatory)
- **Purpose:** Retrieve stored preferences for the active user.
- **Inputs:** `user_id: str`
- **Outputs:** `{favorite_genres, favorite_authors, reading_level, preferred_length, reading_goal}`
- **When used:** At the start of almost every recommendation turn.

### 4.4 `get_reading_history` (Mandatory)
- **Purpose:** Retrieve books the user has already marked as read (and their ratings/feedback).
- **Inputs:** `user_id: str`
- **Outputs:** List of `{book_id, title, status, user_rating}`
- **When used:** Before finalizing recommendations, to exclude already-read books.

### 4.5 `update_user_preference` (Mandatory)
- **Purpose:** Persist a new or changed preference the user expressed conversationally (e.g., "I actually don't like long books").
- **Inputs:** `user_id: str`, `field: str`, `value: str`
- **Outputs:** Confirmation `{updated: true, field, value}`
- **When used:** Only when the user explicitly states a preference change in natural language.

### 4.6 `add_to_favorites` / `mark_as_read` (Mandatory)
- **Purpose:** Record that the user favorited or finished a book.
- **Inputs:** `user_id: str`, `book_id: str`, `action: "favorite"|"read"`
- **Outputs:** Confirmation.
- **When used:** Triggered by explicit UI button (not usually by free-text, but agent can call it if user says "mark that as read").

### 4.7 `record_feedback` (Mandatory)
- **Purpose:** Store like/dislike signal tied to a book and (optionally) a reason.
- **Inputs:** `user_id: str`, `book_id: str`, `sentiment: "like"|"dislike"`, `reason: Optional[str]`
- **Outputs:** Confirmation.
- **When used:** After user reacts to a recommendation; feeds the scorer's feedback term (Section 7).

### 4.8 `find_similar_books` (Advanced, recommended)
- **Purpose:** Semantic similarity search using embeddings (Chroma) — powers "more like X."
- **Inputs:** `book_id: str` OR `free_text_description: str`, `top_k: int = 10`
- **Outputs:** List of book records ranked by cosine similarity.
- **When used:** User references a specific book or describes a vibe rather than a genre.

### 4.9 `get_recommendation_candidates` (Optional convenience wrapper)
- **Purpose:** Single tool that internally calls `search_books` + `get_user_profile` + `get_reading_history` and returns a pre-filtered candidate pool. Reduces the number of round trips the LLM must plan.
- **Inputs:** `user_id: str`, `request_summary: str`
- **Outputs:** Filtered candidate list ready for scoring.
- **When used:** Optional simplification — good if students find multi-tool planning unreliable with smaller Groq models; can be added after the core 8 tools work.

**Mandatory set for MVP:** 4.1–4.7 (7 tools). **4.8 required for the "Advanced" mood/similarity tier.** **4.9 optional.**

---

## 5. Data Architecture

**Decision:** SQLite for all structured/relational data (users, preferences, history, favorites, feedback, recommendation log) + Chroma (local, file-based) for vector search over book descriptions. This avoids running a server, persists to a single file, and is trivial to demo and reset.

### Schemas

**books** (loaded from dataset, read-mostly)
```
book_id        TEXT PRIMARY KEY
title          TEXT
author         TEXT
genre          TEXT
sub_genre      TEXT
pages          INTEGER
reading_level  TEXT   -- easy | medium | hard
avg_rating     REAL
publish_year   INTEGER
description    TEXT
tags           TEXT   -- comma-separated
```
Sample: `("B0142","Project Hail Mary","Andy Weir","Science Fiction","Hard SF",476,"medium",4.7,2021,"A lone astronaut wakes up...","space,survival,humor")`

**users**
```
user_id      TEXT PRIMARY KEY
display_name TEXT
created_at   TIMESTAMP
```

**preferences**
```
user_id          TEXT PRIMARY KEY REFERENCES users
favorite_genres  TEXT   -- comma-separated
favorite_authors TEXT
reading_level    TEXT
preferred_length TEXT   -- short | medium | long
reading_goal     TEXT
current_mood     TEXT   -- last stated mood, transient
updated_at       TIMESTAMP
```

**reading_history**
```
id         INTEGER PRIMARY KEY AUTOINCREMENT
user_id    TEXT REFERENCES users
book_id    TEXT REFERENCES books
status     TEXT   -- reading | read
rated      REAL   -- optional 1-5
added_at   TIMESTAMP
```

**favorites**
```
id        INTEGER PRIMARY KEY AUTOINCREMENT
user_id   TEXT REFERENCES users
book_id   TEXT REFERENCES books
added_at  TIMESTAMP
```

**feedback**
```
id         INTEGER PRIMARY KEY AUTOINCREMENT
user_id    TEXT REFERENCES users
book_id    TEXT REFERENCES books
sentiment  TEXT   -- like | dislike
reason     TEXT
created_at TIMESTAMP
```

**recommendations** (log of what was shown, for history + evaluation)
```
id           INTEGER PRIMARY KEY AUTOINCREMENT
user_id      TEXT REFERENCES users
book_id      TEXT REFERENCES books
request_text TEXT
score        REAL
explanation  TEXT
shown_at     TIMESTAMP
```

Chroma collection `book_embeddings`: one vector per book, `id=book_id`, `document=title + description + tags`, `metadata={genre, reading_level, author}`.

---

## 6. Book Dataset

### Recommended source
Use the **Goodbooks-10k** dataset (public, CSV, ~10,000 books with title, author, average rating, tags/genres) as the base, trimmed down to a **curated subset of 500–1,500 books** for this project — full 10k is unnecessary and slows embedding generation for a student laptop.

Alternative if `goodbooks-10k` is hard to source: a manually curated CSV of 300–500 well-known books across 8–10 genres (compiled once, checked into the repo). This is the safer path given the "must work offline" constraint.

### Required columns
`book_id, title, author, genre, sub_genre (optional), pages, reading_level, avg_rating, publish_year, description, tags`

If the source dataset lacks `reading_level`, derive a simple heuristic bucket (e.g., by page count + a small manually reviewed override list) — do not call an LLM to classify all rows at build time (unnecessary cost); a rule-based bucketing is enough and defensible in a viva.

### Size
500–1,500 rows is the sweet spot: large enough to feel like a real catalog, small enough to embed in minutes on a laptop CPU and to eyeball for correctness.

### Where it lives
`data/raw/books_raw.csv` (as downloaded/curated) → cleaned into `database/app.db` (`books` table) via a one-time `scripts/build_database.py` step at setup time. Never re-parse CSV at runtime.

### How it's loaded
On first run, if `database/app.db` doesn't exist or the `books` table is empty, run the ingestion script automatically (or instruct the user to run it once — either is acceptable; automatic is nicer for a demo).

### How it's searched
- Structured search (`search_books`) → plain SQL `WHERE` filters on genre/author/pages/reading_level, `LIKE` for keyword.
- Semantic search (`find_similar_books`) → Chroma vector query.

### Embeddings
Generate once at ingestion time (not per request): embed `title + ". " + description + ". Tags: " + tags` per book using a local/free embedding model (`sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface`, runs on CPU, no API cost) and store vectors in a local Chroma persistent directory (`database/chroma/`). This means **vector search works fully offline** — only the conversational LLM calls need Groq/internet, satisfying the "must work if internet is unavailable except for Groq" constraint.

### Fallback
If Chroma/embeddings fail to initialize (e.g., missing package), the app must fall back to structured SQL search only and disable "find similar books like X" with a friendly message — never crash the whole app (see Section 18).

---

## 7. Personalization System

### Signals used
| Signal | Source | Type |
|---|---|---|
| Favorite genres | profile | static, user-set |
| Favorite authors | profile | static, user-set |
| Reading level | profile | static, user-set |
| Preferred length | profile | static, user-set |
| Current mood | latest conversational turn | transient |
| Reading goal | profile | static, user-set |
| Reading history | reading_history table | behavioral |
| Likes/dislikes | feedback table | behavioral, evolving |
| Current request text | live input | explicit, highest priority |

### How signals combine — deterministic scoring function
This is computed in plain Python after candidates are retrieved (by `search_books` and/or `find_similar_books`), **not** by the LLM:

```
score(book, user, request) =
      3.0  * genre_match(book, user.favorite_genres, request.genre_hint)
    + 2.5  * author_match(book, user.favorite_authors)
    + 2.0  * semantic_similarity(book, request)        # from Chroma, 0-1, only if applicable
    + 1.5  * rating_score(book.avg_rating)               # normalized 0-1 (avg_rating / 5)
    + 1.5  * reading_level_fit(book.reading_level, user.reading_level, request.difficulty_hint)
    + 1.0  * length_fit(book.pages, user.preferred_length, request.length_hint)
    + 1.0  * mood_fit(book.tags, request.mood)
    + feedback_adjustment(book, user)                    # see below
    - 100  * already_read_penalty(book, user)            # hard exclude, not soft
```

- `feedback_adjustment`: +1.0 if the user liked a book by the same author/genre before; −1.5 if they disliked a book with overlapping tags/genre; caps the effect so one bad match doesn't permanently blacklist an entire genre.
- `already_read_penalty` and explicit dislikes on the *exact same book* are hard filters (removed from the candidate list entirely), not just down-weighted — a college evaluator will specifically try "recommend me something" twice to see if it repeats itself.
- Weights are intentionally simple, tunable constants — good enough to explain in a viva as "explicit request and author match matter most; rating is a tie-breaker," not meant to be a research-grade formula.

### Explanation generation
After the top-N (typically 3–5) books are selected by the scorer, the LLM is given **only** those book records plus the *reasons the scorer flagged them* (e.g., `matched_genre: "Science Fiction", matched_signal: "similar to Project Hail Mary", rating: 4.7`) and asked to write one or two natural sentences per book. This prevents hallucinated justifications and keeps explanations grounded in real fields.

---

## 8. Memory Architecture

| Memory type | What it holds | Storage | Lifetime |
|---|---|---|---|
| Short-term conversational | Last N turns of the chat (for coreference like "that one," "the second book") | `ConversationBufferWindowMemory` (LangChain, in-process) | Current session only |
| Long-term preference memory | Genres, authors, reading level, length, goal | SQLite `preferences` table | Persistent across sessions |
| Reading history | Books read/reading + user ratings | SQLite `reading_history` | Persistent |
| Feedback memory | Like/dislike events + reasons | SQLite `feedback` | Persistent |
| Recommendation log | What was shown, when, with what score/explanation | SQLite `recommendations` | Persistent (also powers "Recommendation History" UI tab) |

**What should NOT be remembered:** raw chat transcripts beyond the session window (no need to persist full conversation text — keep only structured outcomes: preferences, history, feedback). This keeps the DB small and avoids any sensitive-data creep, which is also a nice point for Section 19 (privacy).

**Retrieval during recommendations:** at the start of each agent turn, the orchestrator (not the LLM) eagerly loads `get_user_profile` + `get_reading_history` results into the tool-calling context automatically (or the agent calls them as its first 1-2 tool calls) — either approach is fine; the wrapper tool `get_recommendation_candidates` (4.9) is the clean way to guarantee this happens every time without relying on the LLM remembering to do it.

---

## 9. RAG / Retrieval Architecture

**Yes, lightweight RAG is used** — specifically for the "similar book" / mood-vibe matching feature, not for general Q&A.

- **Embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (local, CPU, free, ~80MB) via `langchain-huggingface`.
- **Vector store:** Chroma, persisted to `database/chroma/` (local folder, no server).
- **Document structure:** one document per book = `f"{title} by {author}. Genre: {genre}. {description} Tags: {tags}"`.
- **Chunking:** none needed — each book's text is short enough (a paragraph) to embed as a single chunk. No text-splitting pipeline required; keep it simple.
- **Metadata stored per vector:** `book_id, title, author, genre, reading_level`.
- **Similarity search:** cosine similarity (Chroma default), `top_k=10`, then intersected/re-ranked by the deterministic scorer in Section 7 (semantic similarity is just one input to the final score, not the final answer).
- **Retrieval flow:**
  ```
  request text or "similar to <book>" → embed query
     → Chroma.similarity_search(query_embedding, k=10)
     → candidate book_ids + similarity scores
     → merged with SQL-filtered candidates (exclude read/disliked)
     → passed to scorer (Section 7)
     → top-N passed to LLM for explanation generation only
  ```
- **Why RAG is unnecessary elsewhere:** general chit-chat, onboarding, and preference updates don't need retrieval — they're simple structured reads/writes. Using RAG only where it earns its keep (semantic book similarity) keeps the project simple to explain and avoids the common student mistake of RAG-ifying everything.

---

## 10. Groq + LangChain Architecture

- **Connection:** `langchain-groq`'s `ChatGroq` class, instantiated with `groq_api_key=os.getenv("GROQ_API_KEY")`.
- **Recommended model category:** a Groq-hosted **Llama 3.x "instant/versatile" tier model with tool-calling support** (pick the current tool-calling-capable Groq model at build time — verify against Groq's live model list, since exact model names change; the architecture only requires "a Groq chat model that supports function/tool calling").
- **Env variable structure:**
  ```
  GROQ_API_KEY=
  GROQ_MODEL_NAME=            # e.g. current Groq tool-calling model id
  ```
- **Configuration:** centralize in `config/settings.py`, loaded once via `python-dotenv`, exposed as a small `Settings` dataclass/object — never call `os.getenv` scattered across modules.
- **Error handling:**
  - Missing/invalid key at startup → fail fast with a clear console message + a friendly banner in the UI ("Groq API key not configured — see .env.example"), not a stack trace.
  - Request-time auth error (401) → caught, surfaced to UI as a non-fatal error card; app remains usable for browsing/search/history features that don't need the LLM.
- **Rate-limit handling:** catch 429s, apply a short exponential backoff (e.g., 2 retries, 1s/2s), then surface a "please try again in a moment" message rather than crashing the agent loop.
- **Fallback behavior:** if Groq is completely unreachable, the app can still serve **non-agentic** structured search (genre/author filters via the UI directly hitting SQLite) so the demo isn't a total blackout — document this clearly as the offline-degraded mode.

---

## 11. Frontend/UI Architecture

### Layout
```
┌───────────────────────────────────────────────────────────────────┐
│  Header: App name · active user selector · settings gear           │
├───────────────┬───────────────────────────────────────┬────────────┤
│  Sidebar       │  Main Content                          │  Activity  │
│                │                                         │  Panel     │
│  - Profile     │  Tabs: [Chat/Recs] [History] [Favorites]│            │
│    summary     │                                         │  Live      │
│  - Preferences │  Chat/Recs tab:                         │  agent     │
│    (editable)  │   - conversation thread                 │  tool-call │
│  - Mood picker │   - recommendation cards (grid)         │  trace     │
│  - Nav links   │   - book detail modal/drawer            │  ("Called  │
│                │                                         │   search_  │
│                │  History tab: read list + ratings       │   books…") │
│                │  Favorites tab: favorited grid          │            │
└───────────────┴───────────────────────────────────────┴────────────┘
```

### Component hierarchy
```
App
├── Header
│   ├── UserSelector
│   └── SettingsMenu
├── Sidebar
│   ├── ProfileSummaryCard
│   ├── PreferencesEditor        (genres, authors, level, length, goal)
│   └── MoodPicker
├── MainContent
│   ├── TabBar (Chat | History | Favorites)
│   ├── ChatPanel
│   │   ├── MessageThread
│   │   ├── MessageInput
│   │   └── RecommendationGrid
│   │       └── RecommendationCard (title, author, rating, "why" explanation, like/dislike, add-to-favorites)
│   ├── HistoryPanel (table/list)
│   ├── FavoritesPanel (grid)
│   └── BookDetailDrawer (full description, tags, actions)
└── ActivityPanel
    └── AgentStepList (tool name, input summary, result summary, timestamp)
```

### Notes
- Keep the **Activity Panel** — it is the single highest-value UI element for demonstrating "this is agentic, not a chatbot" to a viva panel.
- Recommendation cards, book detail, activity trace, and the preferences editor should be the **custom React components** (visually rich, interactive). Chat input/thread can be a lighter custom component too if feasible, or Gradio's chat component if time is short.

---

## 12. React + Gradio Integration

This project has a **mandatory Gradio + React requirement**. React is not optional. Gradio and React have separate responsibilities so the architecture remains understandable and practical for a student project.

**Split of responsibility:**
| Area | Technology | Responsibility |
|---|---|---|
| Python application shell, lifecycle, server-side callbacks | **Gradio Blocks** | Runs the Python application and provides the browser bridge for the Gradio-hosted local application. |
| Main custom visual interface | **React** | Recommendation cards, recommendation grid, agent activity trace, profile/preferences editor, book detail drawer, history/favorites views. |
| React build | **Vite** | Builds the React source into static JavaScript/CSS assets that can be loaded by the Gradio application. |
| LLM/agent/data logic | **Python + LangChain** | Agent orchestration, tools, ranking, memory, database and retrieval. |
| Chat plumbing | **Gradio events / controlled React bridge** | Sends user messages to Python and receives structured JSON results. |

### Required React approach

Use a small React application under `frontend/` and build it with Vite. Do not create a second independent backend server merely to support React. The preferred development flow is:

```text
frontend/src/*
      ↓
   Vite build
      ↓
frontend/dist/*
      ↓
Gradio application loads the built React assets
      ↓
Python/LangChain agent
```

The React UI should communicate with Python through a clearly defined Gradio-compatible bridge. Prefer Gradio's supported event/state mechanisms. If a small companion HTTP endpoint is genuinely required for a React interaction, keep it internal to the same application/deployment design and document why it is needed; do not create an unnecessary separate service.

### React components that must be implemented

At minimum:

- `RecommendationGallery`
- `RecommendationCard`
- `AgentTracePanel`
- `ProfileCard`
- `PreferencesEditor`
- `BookDetailDrawer`
- `HistoryView`
- `FavoritesView`

Chat may use Gradio's native chat component where this materially reduces implementation risk, but the surrounding application experience must remain React-based and visually custom.

### Local launch

The target local experience is a browser-based application, not a terminal-only program. After the frontend is built, the student should be able to launch the application with a simple documented command such as:

```text
python app.py
```

The README must state the exact build and launch commands and the resulting local URL.

### Important deployment note

Gradio is excellent for the local Python application and college demonstration, but its long-lived interactive server behavior must not be assumed to map one-to-one onto a Vercel serverless deployment. Therefore the project must explicitly separate **local/college-demo architecture** from the **Vercel deployment adapter** described in the deployment section. Do not claim that a normal persistent Gradio process, local SQLite file, or local Chroma directory automatically becomes a durable Vercel service.

---

## 13. Backend Architecture

| Module | Responsibility |
|---|---|
| `app.py` | Entry point; builds Gradio Blocks UI, wires callbacks to the agent orchestrator, calls `demo.launch()`. |
| `agent/orchestrator.py` | Builds the LangChain `ChatGroq` LLM, assembles tools, system prompt, memory; exposes `run_turn(user_id, message) -> AgentResponse`. |
| `agent/prompts.py` | All prompt templates (system, explanation, preference-extraction, feedback-analysis) — Section 17. |
| `tools/book_tools.py` | `search_books`, `get_book_details`, `find_similar_books`. |
| `tools/user_tools.py` | `get_user_profile`, `get_reading_history`, `update_user_preference`, `add_to_favorites`, `record_feedback`. |
| `tools/composite_tools.py` | `get_recommendation_candidates` (optional wrapper tool). |
| `data/db.py` | SQLite connection management, schema creation, CRUD helpers for every table in Section 5. |
| `data/ingest.py` | One-time script: reads raw CSV, cleans/derives `reading_level`, populates `books` table, builds Chroma embeddings. |
| `rag/vector_store.py` | Chroma client setup, embedding function, `similarity_search` wrapper. |
| `recommender/scorer.py` | Deterministic scoring function from Section 7; pure functions, unit-testable, no LLM calls. |
| `recommender/ranker.py` | Orchestrates: candidates → filter read/disliked → score → sort → top-N. |
| `memory/conversation_memory.py` | Wraps `ConversationBufferWindowMemory` per active session. |
| `config/settings.py` | Loads `.env`, exposes typed settings object. |
| `utils/logging_utils.py` | Consistent logging (also powers the Activity Panel trace). |
| `utils/validators.py` | Input validation/sanitization (Section 19). |
| `ui/app_ui.py` | Gradio Blocks layout + custom HTML components (Sections 11–12). |
| `ui/components/*.py` | Small functions returning HTML strings for RecommendationGallery, AgentTrace, ProfileCard, BookDetailDrawer. |

---

## 14. Complete Folder Structure

```
reading-recommender-agent/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py
│   └── prompts.py
│
├── tools/
│   ├── __init__.py
│   ├── book_tools.py
│   ├── user_tools.py
│   └── composite_tools.py
│
├── data/
│   ├── raw/
│   │   └── books_raw.csv
│   ├── __init__.py
│   └── ingest.py
│
├── database/
│   ├── db.py
│   ├── app.db                # generated at setup, gitignored
│   └── chroma/                # generated at setup, gitignored
│
├── recommender/
│   ├── __init__.py
│   ├── scorer.py
│   └── ranker.py
│
├── memory/
│   ├── __init__.py
│   └── conversation_memory.py
│
├── rag/
│   ├── __init__.py
│   └── vector_store.py
│
├── ui/
│   ├── __init__.py
│   ├── app_ui.py
│   └── components/
│       ├── recommendation_gallery.py
│       ├── agent_trace.py
│       ├── profile_card.py
│       └── book_detail.py
│
├── utils/
│   ├── __init__.py
│   ├── logging_utils.py
│   └── validators.py
│
├── scripts/
│   └── build_database.py     # thin CLI wrapper around data/ingest.py
│
└── tests/
    ├── test_scorer.py
    ├── test_tools.py
    ├── test_db.py
    └── test_agent_flow.py
```

---

## 15. Data Flow

**A. User onboarding flow**
```
UI: New user form → Python: create user_id, insert into `users`
   → insert defaults into `preferences`
   → UI redirects to Chat tab with a welcome message from the agent
```

**B. Recommendation flow**
```
User message ──► Agent Orchestrator
   Orchestrator ──► get_user_profile, get_reading_history  (tools)
   Orchestrator ──► search_books and/or find_similar_books (tools)
   Candidates ──► ranker.py: exclude read/disliked, score, sort, top-N
   Top-N + reasons ──► LLM explanation prompt ──► per-book explanation text
   Final payload ──► UI: RecommendationGallery + logged into `recommendations` table
```

**C. Agent tool-calling flow**
```
LLM (Groq, tool-calling mode) receives system prompt + user msg + tool schemas
   → LLM emits a tool_call (name + JSON args)
   → LangChain AgentExecutor invokes the matching Python function
   → tool result (JSON) appended to the message history
   → LLM either calls another tool or produces the final answer
   → loop bounded by max_iterations (e.g., 6) to avoid runaway loops
```

**D. Feedback flow**
```
User clicks like/dislike on a RecommendationCard
   → record_feedback(user_id, book_id, sentiment, reason?) tool/direct call
   → feedback row inserted
   → next ranker.py call reads updated feedback table → adjusts score
```

**E. Memory flow**
```
Turn start: load short-term buffer (in-process) + long-term profile/history (SQLite)
Turn end:   append turn to short-term buffer;
            if agent called update_user_preference/record_feedback/add_to_favorites,
            those writes are already persisted to SQLite as part of the tool call
```

**F. RAG/retrieval flow**
```
"similar to X" or vibe-based request
   → embed query text (MiniLM, local)
   → Chroma.similarity_search(top_k=10)
   → merge with SQL candidate pool (or use alone if no genre/author filter given)
   → pass to ranker.py alongside other signals
```

---

## 16. Agent Decision Flow — Worked Example

**User:** "I want a short sci-fi book that is easy to understand and similar to *The Martian*."

```
1.  Agent receives request; system prompt + tool schemas + short-term memory in context.
2.  LLM parses intent: recommendation request.
    Extracted constraints: genre=science fiction, length=short, difficulty=easy,
    similar_to="The Martian".
3.  LLM calls get_user_profile(user_id) → learns user's stored reading_level="medium",
    favorite_genres includes "Science Fiction" already (reinforces confidence).
4.  LLM calls get_reading_history(user_id) → learns user has already read "The Martian"
    (rated 5) and "Project Hail Mary" (unread).
5.  LLM calls find_similar_books(book_id_or_text="The Martian") → Chroma returns 10
    candidates by embedding similarity (includes "Project Hail Mary", "Artemis",
    "The Long Way to a Small, Angry Planet", etc.)
6.  LLM (or backend automatically) also calls search_books(genre="science fiction",
    max_length_pages=350) to widen the structured pool given the "short" constraint.
7.  ranker.py merges both candidate pools, removes duplicates.
8.  ranker.py excludes "The Martian" itself (already read) — hard filter.
9.  ranker.py scores remaining candidates using Section 7's formula: heavy weight on
    semantic similarity (from step 5) + length_fit (short) + reading_level_fit (easy)
    + genre_match (sci-fi, already a favorite).
10. Top 3 candidates selected, e.g., "Artemis" (Andy Weir, 384pp, easy-medium),
    "The Martian"-adjacent picks with high similarity + short length.
11. LLM is given the top 3 records + their score reasons and writes one explanation
    sentence per book, referencing only real fields (author, similarity, length, rating).
12. Final structured response returned: {books: [...], explanations: [...], trace: [...]}.
13. UI renders RecommendationGallery cards + updates the Activity Panel with the
    exact tool calls from steps 3, 4, 5, 6 (name, args, short result summary).
14. `recommendations` table logs all 3 shown books with score + explanation + timestamp.
```

---

## 17. Prompts

### System prompt
```
You are a personalized reading recommendation assistant. You help users find books
based on their stated preferences, reading history, mood, and requests.

Rules you must always follow:
- Never invent a book, author, rating, or book detail that was not returned by a tool.
- Always check the user's profile and reading history before recommending, unless
  you already have that information in this conversation.
- Never recommend a book the user has already marked as read, unless they explicitly
  ask to revisit it.
- If a user expresses a new preference (likes/dislikes a genre, author, or length),
  call update_user_preference or record_feedback to save it.
- Keep responses concise, warm, and focused on the user's actual request.
- If no suitable books are found, say so honestly and suggest broadening the request
  rather than fabricating an answer.
- When explaining a recommendation, refer only to fields present in the book record
  provided to you (title, author, genre, rating, description, tags, similarity reason).
```

### Recommendation prompt (used internally to instruct explanation generation)
```
You are given a user's request, their profile, and a short list of candidate books
with the specific reasons each was selected (e.g., matched genre, semantic similarity
to a book they mentioned, rating, length fit). For each candidate, write 1-2 sentences
explaining why it fits THIS user's request, using only the provided fields. Do not
add facts not present in the data. Return a JSON list of {book_id, explanation}.
```

### Book explanation prompt (single-book "why this book?" on demand)
```
Explain in 2-3 sentences why the book "{title}" by {author} was recommended to this
user, given: user's favorite genres = {genres}, reading level = {level}, and the
match reasons = {match_reasons}. Use only these facts. Do not describe plot details
not present in the provided description: "{description}".
```

### Preference extraction prompt
```
Read the user's message. Identify any explicit statement of a reading preference:
favorite genre, favorite author, disliked genre/author, preferred book length,
reading level, or reading goal. If found, return a JSON object:
{"field": "<preferences field name>", "value": "<extracted value>"}.
If no explicit preference is stated, return {"field": null}.
Do not infer preferences from vague or ambiguous statements.
```

### Feedback analysis prompt
```
The user reacted to a book recommendation with: "{user_reaction}" regarding the book
"{title}" ({genre}, by {author}). Classify the sentiment as "like" or "dislike", and
if a reason is given (e.g., "too long", "not my genre"), extract it briefly.
Return JSON: {"sentiment": "like"|"dislike", "reason": "<short phrase or null>"}.
```

---

## 18. Error Handling

| Scenario | Behavior |
|---|---|
| Invalid/missing Groq API key | Fail fast at startup with a clear message; UI shows a banner; non-LLM features (browse/search/history) remain usable |
| Groq API unavailable / network error | Catch exception in orchestrator; return a friendly in-chat error message; do not crash the app |
| Empty book database | Ingestion script checks row count post-load and warns; app shows "no books loaded" state in Chat tab rather than silently returning empty results |
| No matching books for a request | Ranker returns empty list; LLM is instructed (Section 17) to say so honestly and suggest broadening filters, not to invent books |
| Malformed user input (empty message, only whitespace) | Validated client-side and server-side (`utils/validators.py`); ignored with a gentle prompt to try again |
| Tool failure (exception inside a tool function) | Wrapped in try/except inside each tool; returns a structured `{"error": "..."}` the LLM can react to gracefully instead of the whole agent loop crashing |
| Vector DB (Chroma) failure to initialize | Caught at startup; `find_similar_books` disabled with a logged warning; structured search still works |
| Missing user profile (new user edge case) | `get_user_profile` returns sensible defaults instead of raising; onboarding flow ensures a `preferences` row always exists at user creation |
| Rate limits (429 from Groq) | Retry with short backoff (2 attempts), then surface "please try again shortly" |
| LLM timeout | Set a reasonable request timeout (e.g., 30s) in `ChatGroq`; on timeout, same friendly-error path as network failure |

General principle: every external call (Groq, Chroma, SQLite) is wrapped; failures degrade a specific feature rather than the whole app.

---

## 19. Security

- **`.env` usage:** `GROQ_API_KEY` and all config live in `.env` (gitignored); `.env.example` checked into the repo with empty values as a template.
- **API key protection:** key is loaded only in `config/settings.py` on the server side; never sent to the browser/frontend; never logged (mask in any debug logs).
- **Input validation:** all free-text user input is length-capped and stripped of control characters before being passed to the LLM or SQL layer (`utils/validators.py`); all SQL uses parameterized queries — no string-concatenated SQL, ever (prevents injection even though this is a local single-user app).
- **Safe tool execution:** tools only ever read/write the app's own SQLite file and local Chroma directory — no filesystem access outside `database/`, no shell execution, no arbitrary file paths accepted as tool arguments.
- **Data privacy:** the app is local-only and single-machine; no reading data leaves the machine except the text sent to Groq for LLM reasoning (state this explicitly in the README/report as the data-flow boundary).

---

## 20. Performance

- **Caching:** cache `get_user_profile`/`get_reading_history` results within a single agent turn (avoid re-querying SQLite multiple times per turn if multiple tools need them).
- **Database loading:** books table and Chroma index are built once at setup (`scripts/build_database.py`), not on every app start; app start just opens existing connections.
- **Embedding reuse:** book embeddings are computed once at ingestion and persisted in Chroma; never re-embed the whole catalog at query time — only the (short) user query text is embedded per request.
- **Avoiding unnecessary LLM calls:** ranking/scoring is deterministic Python (Section 7), not an LLM call; preference/feedback extraction prompts are small and only triggered when relevant, not run on every message.
- **Limiting retrieved candidates:** cap `search_books`/`find_similar_books` results (e.g., 10-20) before scoring, and cap final recommendations shown (3-5), to keep LLM context small and responses fast.
- **Conversation history management:** use a windowed memory (e.g., last 6-10 turns) rather than unbounded history, to keep prompt size and latency predictable.

---

## 21. Testing Strategy

| Test case | Expected behavior |
|---|---|
| User onboarding | New user + default preferences row created; visible immediately in Profile sidebar |
| Profile creation/edit | Editing a preference via UI persists to SQLite and is reflected in the next recommendation |
| Basic recommendation | A generic request ("recommend me a book") returns 3-5 grounded books with explanations |
| Personalized recommendation | Two users with different favorite genres get different results for the same request text |
| Mood-based recommendation | Request mentioning mood (e.g., "something comforting") shifts results toward mood-tagged books |
| Similar-book recommendation | "More like X" returns books with high semantic similarity to X, excluding X itself |
| Previously-read filtering | A book already in reading_history never appears in new recommendations |
| Feedback | Disliking a book lowers the score of similar books in the next request (verify via scorer unit test with a fixed feedback fixture) |
| Memory | Preference stated mid-conversation ("I don't like long books") is present in `preferences` table after the turn and affects the very next recommendation |
| Tool calls | Mock the LLM tool-calling decision and assert the correct Python tool function is invoked with correct args (unit test on `tools/*`) |
| No-result cases | A request with contradictory/over-narrow filters returns an honest "no matches" message, not a crash or invented result |
| API failure | Simulate Groq exception; assert UI shows a friendly error and app remains responsive |
| Invalid input | Empty/whitespace-only message is rejected client-side with no agent call made |

Use `pytest` for `tests/test_scorer.py` (pure function, easiest to unit test thoroughly), `tests/test_db.py` (CRUD correctness), `tests/test_tools.py` (tool I/O contracts with a test SQLite fixture), and a lightweight `tests/test_agent_flow.py` that mocks the Groq LLM to test orchestration logic without real API calls (important — don't burn API quota on tests, and tests should not require network).

---

## 22. Demo Scenario (5–10 minutes)

1. **Start application** — `python app.py`; show the terminal confirming DB/Chroma loaded.
2. **Create/select a user** — create "Demo User," show the empty profile.
3. **Set preferences** — pick 2 favorite genres, one favorite author, reading level "medium."
4. **Ask a natural-language question** — "I want something short and fun, maybe fantasy."
5. **Show agent activity** — point at the Activity Panel showing `get_user_profile`, `get_reading_history`, `search_books` calls in real time.
6. **Show recommendations** — 3 cards appear, each with a grounded explanation referencing genre/length/rating.
7. **Open a book** — click a card to open the BookDetailDrawer with full description/tags.
8. **Like/dislike** — dislike one recommendation with reason "too long."
9. **Ask another recommendation** — repeat a similar request; show the disliked book/genre pattern no longer surfaces as strongly, and previously-shown books aren't repeated.
10. **Demonstrate personalization/memory** — switch to a second, pre-seeded user profile with different preferences and run the identical request text, showing different results side-by-side — this single moment is the clearest proof of "personalized," not "generic," for the evaluator.

---

## 23. Agentic AI Concepts to Explain in Viva

| Concept | Where it appears |
|---|---|
| LLM | Groq-hosted Llama model via `ChatGroq`, used for intent parsing and explanation generation |
| AI Agent | `AgentExecutor` in `agent/orchestrator.py`, which plans and calls tools autonomously |
| Tool calling / Function calling | The 7-8 `@tool` functions in `tools/`, invoked by the LLM via Groq's native tool-calling |
| Agent planning/decision-making | Section 3/16: deciding which tools to call and in what order based on parsed intent |
| Memory | Short-term (`ConversationBufferWindowMemory`) + long-term (SQLite preferences/history/feedback), Section 8 |
| RAG | `find_similar_books` pipeline over Chroma, Section 9 |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` vectors for book descriptions, Section 9 |
| Vector database | Chroma persistent store, `database/chroma/` |
| Prompt engineering | System prompt + 4 task-specific prompts, Section 17, with explicit grounding/anti-hallucination rules |
| Personalization | Weighted deterministic scorer combining profile + history + feedback + request, Section 7 |
| Feedback loop | `record_feedback` tool → `feedback` table → re-enters `scorer.py` on the next turn, Section 7/15D |
| Retrieval | Both structured (SQL `search_books`) and semantic (Chroma) retrieval feed the ranker |
| Context management | Windowed conversation memory + capped candidate lists keep LLM context small and relevant |

---

## 24. Possible Novelty (with difficulty)

| Idea | Difficulty |
|---|---|
| Mood-aware recommendations (mood as an explicit scoring signal) | Low — already in baseline scorer |
| "Why this book?" on-demand explanation button per card | Low |
| Feedback-driven personalization (dislikes measurably shift future results) | Low-Medium — mostly the scorer's feedback term |
| Reading-goal-aware nudging ("you said you wanted more nonfiction this month") | Medium — needs a small goal-progress heuristic (count of nonfiction read this period) |
| Adaptive reading-level ("this book was too hard" feedback nudges future difficulty selection) | Medium — extend feedback reason parsing + a level-adjustment rule |
| Two-user side-by-side personalization demo (Section 22 step 10) | Low — no new code, just a demo technique |
| "Reading twin" — compare two users' overlapping taste | Medium-High — skip unless ahead of schedule |
| Cover-image fetching from a public API for visual polish | Low, but adds an optional internet dependency — must degrade gracefully |
| Session-based mood decay (mood signal fades after N turns) | Low — small addition to scorer/memory logic |

Recommended novelty set for the report: mood-awareness, feedback-driven personalization, adaptive difficulty, and the two-user demo — all Low/Medium and clearly explainable.

---

## 25. Implementation Roadmap

| Phase | Build | Files | Depends on | Result | Test |
|---|---|---|---|---|---|
| 1. Setup | Repo skeleton, venv, `.env.example`, `requirements.txt` | root files, `config/settings.py` | — | App skeleton runs, prints config OK | Run `python -c "from config.settings import settings; print(settings)"` |
| 2. Dataset | Curate/download CSV, write `data/ingest.py`, run once to build `database/app.db` + Chroma | `data/`, `database/db.py` | Phase 1 | `books` table populated, Chroma collection populated | `tests/test_db.py`, manual row count check |
| 3. Basic UI | Gradio Blocks shell: user selector, static preferences form, empty chat | `ui/app_ui.py`, `app.py` | Phase 1 | App launches, tabs navigable, no agent yet | Manual click-through |
| 4. LangChain agent (no tools yet) | `ChatGroq` wired, system prompt, basic chat loop echoing LLM replies | `agent/orchestrator.py`, `agent/prompts.py` | Phase 1 | Can chat with the LLM in the UI | Manual: ask a question, get an LLM reply |
| 5. Tools | Implement all 7 core tools; bind to agent as `AgentExecutor` | `tools/*.py` | Phases 2, 4 | Agent can call tools and use real book data | `tests/test_tools.py`, manual trace check |
| 6. Personalization/ranking | `recommender/scorer.py`, `recommender/ranker.py`; wire into orchestrator before final LLM explanation pass | `recommender/*.py` | Phase 5 | Recommendations are ranked, not just raw search results | `tests/test_scorer.py` |
| 7. Memory | Windowed conversation memory; ensure profile/history/feedback persist and are reloaded correctly each turn | `memory/conversation_memory.py` | Phase 5 | Multi-turn coherence; preferences persist across restarts | Manual multi-turn test + restart app |
| 8. RAG | `rag/vector_store.py`, `find_similar_books` tool | `rag/*.py`, `tools/book_tools.py` | Phase 2 | "similar to X" requests work | Manual + `tests/test_tools.py` |
| 9. UI polish | Custom HTML components: RecommendationGallery, AgentTrace, BookDetailDrawer, styled CSS | `ui/components/*.py` | Phases 3, 5 | UI looks like a real app, not a default demo | Manual visual review |
| 10. Testing | Fill out `tests/`, run full suite, fix edge cases from Section 18/21 | `tests/*` | All above | Green test suite; graceful failure paths verified | `pytest` |
| 11. Deployment/demo | README, `.env.example` finalized, rehearse Section 22 demo script | `README.md` | All above | Ready for submission/demo | Full run-through of demo scenario |

---

## 26. requirements.txt

**Required Python dependencies**
```
langchain
langchain-groq
langchain-community
langchain-huggingface
chromadb
sentence-transformers
gradio
python-dotenv
pandas
pydantic
```

**Optional Python dependencies**
```
pytest
requests
```

The React frontend has its own `package.json` and should include only the dependencies actually needed by the implemented UI. Prefer a minimal Vite + React setup.

Do not add FastAPI/Flask, Redis, Docker, Kubernetes, microservices, or other infrastructure unless the final deployment design proves that a component is necessary.

---

## 27. Environment Variables (`.env.example`)

```
# Groq LLM -- SERVER SIDE ONLY
GROQ_API_KEY=
GROQ_MODEL_NAME=

# Local development storage
DATABASE_PATH=database/app.db
CHROMA_PERSIST_DIR=database/chroma

# Embeddings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Agent behavior
CONVERSATION_MEMORY_WINDOW=8
MAX_AGENT_ITERATIONS=6
MAX_RECOMMENDATIONS=5

# Production/deployment storage -- values depend on the selected provider
DATABASE_URL=
VECTOR_STORE_URL=
VECTOR_STORE_API_KEY=
```

Production-only variables must be configured through the deployment platform's environment-variable settings, not committed to Git. `GROQ_API_KEY`, database credentials, and vector-store credentials must never be included in React source, browser JavaScript, or the repository.

---

## 28. README Specification

The README must include:

1. Project title and one-line description
2. Problem statement and motivation
3. Core and advanced features
4. Architecture diagram
5. Exact Gradio + React architecture
6. Tech stack
7. Prerequisites: Python, Node.js/npm, Git
8. Python virtual-environment setup
9. React dependency installation
10. React build command
11. `.env` setup
12. Dataset setup and ingestion
13. Local database and Chroma initialization
14. Local launch command and expected URL
15. Example user requests
16. Agent/tool activity explanation
17. Testing commands
18. Vercel/deployment architecture
19. Production database/vector-store configuration
20. Deployment environment variables
21. Security notes
22. Known deployment limitations
23. Screenshots section
24. Demo script
25. Viva concepts
26. Future scope
27. Team/contributors

The README must never instruct the user to expose the Groq API key in frontend code.

---

## 29. College Project Documentation — Diagrams to Include

| Diagram | Should show |
|---|---|
| System architecture | Browser → React UI → Gradio/Python application → LangChain agent → tools → database/RAG → Groq |
| Local architecture | Gradio + React + Python + SQLite + Chroma running locally |
| Deployment architecture | React/static UI deployment path, Python/Gradio application path, external persistent storage, Groq API, and the boundary between ephemeral and persistent services |
| Agent architecture | LLM, system prompt, tools, memory and deterministic ranker |
| Data flow diagram | User → UI → agent → tools/retrieval → ranker → explanation → UI |
| Sequence diagram | User → React/Gradio → Agent → Tools → Ranker → LLM → UI |
| Use case diagram | User; Set Preferences, Request Recommendation, Give Feedback, View History, View Favorites |
| Database schema | Seven core tables and foreign keys |
| RAG pipeline | Book text → embeddings → vector store → similarity retrieval → candidate merge → ranker |
| Recommendation workflow | Candidate retrieval → hard filters → deterministic scoring → ranking → grounded explanation → display |
| UI architecture | Gradio shell plus React component hierarchy |

---

## 30. Deployment Architecture and Vercel Strategy

The project has two explicit targets:

### A. Local/college-demo target

```text
Browser
  ↓
Gradio Blocks
  ↓
React custom UI
  ↓
Python/LangChain agent
  ├── Groq
  ├── SQLite
  └── Chroma
```

This is the primary development and demonstration environment. It should work from a student laptop without requiring cloud infrastructure.

### B. Deployment target

Vercel should be treated as the deployment target for the web-facing portion of the application. The architecture must not assume that a persistent local Python process, SQLite file, or Chroma directory will behave like durable server storage in a serverless environment.

The implementation must therefore isolate storage and deployment-specific concerns behind interfaces. A practical production topology is:

```text
Browser
  ↓
React web UI / static assets
  ↓
Python application/agent endpoint hosted in a Python-compatible runtime
  ↓
LangChain + Groq
  ├── Persistent hosted relational database
  └── Persistent vector store (if RAG is enabled in production)
```

If the chosen Vercel runtime can support the required Python/Gradio interaction reliably, use the corresponding Vercel configuration. If it cannot support the long-lived Gradio server behavior required by the local app, **do not fake compatibility**: deploy the React/web-facing portion to Vercel and document the Python/Gradio service as a separate Python-compatible deployment. The codebase must keep these deployment boundaries clear so the local college demo remains unchanged.

The README must state exactly which parts are deployed to Vercel and which parts require the Python-compatible service.

### Storage abstraction

Local development:

```text
SQLite → database/app.db
Chroma → database/chroma/
```

Production:

```text
Database repository → persistent hosted relational database
Vector repository → persistent hosted vector store, if required
```

Do not scatter direct SQLite/Chroma calls throughout the agent. Use repository/storage modules so the implementation can switch storage backends.

### Security

- Groq API calls must be server-side.
- React must never contain `GROQ_API_KEY`.
- `.env` must be gitignored.
- Production secrets must be configured in deployment environment variables.
- Validate all tool inputs.
- Never return credentials in agent traces.

---

## 31. Definition of Done

The project is complete only when all of the following are true.

### Local

- Python environment installs successfully.
- React dependencies install successfully.
- React production build succeeds.
- Gradio application starts successfully.
- Website opens in a browser.
- User profile creation/selection works.
- Preferences work.
- Natural-language recommendation requests work.
- Groq integration works.
- LangChain agent and tools work.
- Books come from the real project dataset/database.
- Deterministic Python ranking works.
- Grounded explanations work.
- Reading history works.
- Favorites work.
- Like/dislike feedback affects future ranking.
- Agent Activity panel shows real tool activity.
- Similar-book/RAG functionality works if included in the MVP.
- Tests pass.
- No API key is exposed to the browser.

### Deployment

- Deployment architecture is documented.
- Vercel responsibilities are documented.
- Python/Gradio runtime requirements are documented.
- Persistent database strategy is documented.
- Persistent vector-store strategy is documented if RAG is deployed.
- Environment variables are documented.
- Secrets remain server-side.
- Known limitations are documented.
- The deployed web-facing application can perform the supported core recommendation flow.

---

## 32. Final Implementation Specification (summary)

This condenses Sections 1-31 into the copy-paste build instruction below. The Master Build Specification is authoritative for implementation and must not contradict the architecture above.

---

# MASTER BUILD SPECIFICATION FOR ANTIGRAVITY

Copy everything below this line into the Antigravity Claude instance as the build instruction.

```text
PROJECT: Personalized Reading Recommendation Agent

PRIMARY GOAL:
Build a working, locally runnable, browser-based Personalized Reading
Recommendation Agent for a 2nd-year CS/Data Science college project.
The project must use BOTH Gradio and React. It must demonstrate genuine
agentic AI behavior using LangChain + Groq, tool calling, memory, retrieval,
personalization, deterministic ranking, feedback, and grounded explanations.

The application must work locally first. Deployment to Vercel must be
considered from the beginning, but DO NOT falsely assume that a persistent
Gradio process, local SQLite file, or local Chroma directory automatically
becomes durable storage on Vercel. Keep local/demo and production storage
behind clear interfaces.

=== NON-NEGOTIABLE ARCHITECTURE ===

1. Gradio is mandatory.
2. React is mandatory; it is NOT an optional alternative.
3. Use Vite to build the React frontend into static assets.
4. Gradio remains the Python application shell for the local/college demo.
5. Python/LangChain owns the agent, tools, memory, ranking and data access.
6. Groq API calls are server-side only. Never expose GROQ_API_KEY to React.
7. Candidate retrieval may use SQL and semantic retrieval.
8. Final recommendation ranking MUST be deterministic Python, not an LLM
   judgment call.
9. The LLM generates grounded explanations only from retrieved records and
   ranker output.
10. Already-read and explicitly disliked books are hard-excluded.
11. Local development uses SQLite and Chroma unless unavailable.
12. Production persistence must use deployment-compatible persistent storage.
13. Do not add unnecessary microservices, Redis, Docker, Kubernetes, etc.

=== TECH STACK ===

Python 3.10+
LangChain
langchain-groq / ChatGroq
Groq tool-calling-capable model selected through GROQ_MODEL_NAME
Gradio Blocks
React
Vite
SQLite for local development
Chroma for local semantic retrieval
sentence-transformers/all-MiniLM-L6-v2 for local embeddings
Python-dotenv
pandas
pydantic
pytest for tests

React dependencies must be minimal and should be installed only if actually
used by the implementation.

=== LOCAL APPLICATION EXPERIENCE ===

The student must be able to build the React frontend and launch the Python
application so that a browser opens/displays a real website-like interface.
The README must document the exact commands. A preferred flow is:

1. python -m venv .venv
2. activate the virtual environment
3. pip install -r requirements.txt
4. cd frontend
5. npm install
6. npm run build
7. return to project root
8. python app.py

Use the exact commands appropriate to the implemented structure. Do not invent
commands that are not tested.

=== FOLDER STRUCTURE ===

reading-recommender-agent/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── vercel.json                  # only if actually required by the chosen deployment design
├── config/
│   └── settings.py
├── agent/
│   ├── orchestrator.py
│   └── prompts.py
├── tools/
│   ├── book_tools.py
│   ├── user_tools.py
│   └── composite_tools.py
├── data/
│   ├── raw/books_raw.csv
│   └── ingest.py
├── database/
│   ├── db.py
│   └── repositories.py
├── recommender/
│   ├── scorer.py
│   └── ranker.py
├── memory/
│   └── conversation_memory.py
├── rag/
│   └── vector_store.py
├── ui/
│   ├── app_ui.py
│   └── components/
│       ├── recommendation_gallery.py
│       ├── agent_trace.py
│       ├── profile_card.py
│       └── book_detail.py
├── utils/
│   ├── logging_utils.py
│   └── validators.py
├── scripts/
│   └── build_database.py
├── frontend/
│   ├── package.json
│   ├── vite.config.*
│   ├── index.html
│   ├── src/
│   │   ├── main.*
│   │   ├── App.*
│   │   ├── components/
│   │   └── styles/
│   └── dist/                  # generated; gitignore if appropriate
└── tests/
    ├── test_scorer.py
    ├── test_tools.py
    ├── test_db.py
    └── test_agent_flow.py

Do not create files that are not needed. Keep the structure understandable.

=== CORE FEATURES — MVP ===

- Create/select user profile
- Editable genres, authors, reading level, preferred length and goal
- Natural-language recommendation chat
- Structured book search
- Personalized ranked recommendations
- Grounded per-book explanation
- Reading history
- Hard exclusion of already-read books
- Favorites
- Like/dislike feedback
- Feedback affects future ranking
- Agent Activity panel showing real tool calls
- React recommendation cards
- React profile/preferences UI
- React history/favorites UI
- Book detail drawer

=== ADVANCED FEATURES — BUILD AFTER MVP IS STABLE ===

- Mood as a scoring signal
- Similar-to-X semantic retrieval using Chroma
- Recommendation history
- Session persistence
- Adaptive reading level
- Reading goals

Do not delay a working MVP in order to implement every advanced feature.

=== DATA MODEL ===

books(book_id PK, title, author, genre, sub_genre, pages, reading_level,
      avg_rating, publish_year, description, tags)
users(user_id PK, display_name, created_at)
preferences(user_id PK/FK, favorite_genres, favorite_authors, reading_level,
      preferred_length, reading_goal, current_mood, updated_at)
reading_history(id PK, user_id FK, book_id FK, status, rated, added_at)
favorites(id PK, user_id FK, book_id FK, added_at)
feedback(id PK, user_id FK, book_id FK, sentiment, reason, created_at)
recommendations(id PK, user_id FK, book_id FK, request_text, score,
      explanation, shown_at)

Use repository/storage functions so agent code does not directly depend on
SQLite-specific implementation details.

=== LOCAL DATASET ===

Use a curated 500-1500 book dataset, such as a trimmed Goodbooks-style dataset
or another legally usable/local dataset. Required fields:
book_id, title, author, genre, pages, reading_level, avg_rating, publish_year,
description, tags.

Ingest once into local SQLite and Chroma. Never download or rebuild the full
dataset on every request.

=== AGENT TOOLS ===

Implement LangChain @tool functions:

1. search_books(query?, genre?, author?, max_length_pages?, reading_level?)
2. get_book_details(book_id)
3. get_user_profile(user_id)
4. get_reading_history(user_id)
5. update_user_preference(user_id, field, value)
6. add_to_favorites(user_id, book_id)
7. mark_as_read(user_id, book_id)
8. record_feedback(user_id, book_id, sentiment, reason?)
9. find_similar_books(book_id? or free_text_description?, top_k=10)

Tools must validate input, catch expected internal errors and return structured
results/errors. Do not leak secrets or stack traces to the UI.

=== AGENT WORKFLOW ===

User request
  ↓
ChatGroq / LangChain agent
  ↓
Determine intent and constraints
  ↓
Retrieve profile/history as needed
  ↓
Search SQL and/or semantic candidates
  ↓
Hard-filter read/disliked books
  ↓
Python deterministic scorer/ranker
  ↓
Select top 3-5
  ↓
LLM creates short grounded explanations
  ↓
Structured result returned to UI
  ↓
React recommendation cards + Agent Activity panel

The LLM must not invent books, authors, ratings, pages or descriptions.

=== DETERMINISTIC RANKING ===

Implement recommender/scorer.py and ranker.py. The ranker may use weighted
signals such as:

- genre match
- author match
- semantic similarity
- rating
- reading-level fit
- length fit
- mood fit
- feedback adjustment

The exact weights should be configurable and documented. Ranking must be
pure Python and reproducible for the same inputs.

=== MEMORY ===

Short-term: windowed conversation memory, approximately 8 turns.
Long-term: structured preferences, reading history, feedback and recommendation
records. Do not persist raw conversations unless explicitly needed.

=== RAG ===

Local: sentence-transformers MiniLM → Chroma.
Use primarily for similar-book and semantic retrieval.
Do not use RAG for ordinary profile writes or simple structured operations.

If RAG is deployed to production, use a persistent deployment-compatible
vector store or clearly document RAG as a local/demo feature. Do not assume a
local Chroma directory is durable serverless storage.

=== REACT UI ===

React is mandatory. Build the following components:

- RecommendationGallery
- RecommendationCard
- AgentTracePanel
- ProfileCard
- PreferencesEditor
- BookDetailDrawer
- HistoryView
- FavoritesView

The interface should look like a custom reading application, not a default
Gradio demo. Use responsive styling.

The Agent Activity panel is especially important because it demonstrates the
agentic nature of the system during the viva.

=== GRADIO UI SHELL ===

Use Gradio Blocks for the Python application shell and local browser bridge.
Keep the Gradio layer responsible for application lifecycle and Python-side
events. Do not duplicate business logic in React.

=== SECURITY ===

- Store secrets only in .env locally or deployment environment variables.
- Add .env to .gitignore.
- Never put GROQ_API_KEY in React.
- Never put GROQ_API_KEY in frontend JavaScript.
- Never commit API keys.
- Validate tool inputs.
- Sanitize displayed user/data content where appropriate.
- Never expose database credentials in the Agent Activity panel.

=== ENVIRONMENT VARIABLES ===

Local .env.example:

GROQ_API_KEY=
GROQ_MODEL_NAME=
DATABASE_PATH=database/app.db
CHROMA_PERSIST_DIR=database/chroma
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
CONVERSATION_MEMORY_WINDOW=8
MAX_AGENT_ITERATIONS=6
MAX_RECOMMENDATIONS=5

Production-only values such as DATABASE_URL or vector-store credentials may
be added if the selected deployment backend requires them.

=== DEPLOYMENT / VERCEL ===

Treat Vercel as the web deployment target, but do not make unsupported claims.
The local Gradio process, local SQLite file and local Chroma directory are not
assumed to be durable cloud resources.

Design storage behind repository interfaces:

Local:
SQLite + local Chroma

Production:
persistent hosted relational database + persistent vector store if required

The React/static web-facing portion can be deployed to Vercel when appropriate.
If the exact Gradio server behavior required by the local application cannot be
reliably hosted as a Vercel serverless process, keep the Python/Gradio service
on a Python-compatible host and configure the React web deployment to communicate
with it through a secure backend interface. Document this limitation instead of
pretending an unsupported all-in-one deployment works.

If a Vercel configuration file is needed, generate only a configuration that
matches the actual implemented deployment. Test build commands before claiming
they work.

=== TESTING ===

Unit tests:
- scorer behavior
- hard exclusion of read/disliked books
- tool validation
- database repository operations
- missing profile defaults
- feedback adjustments

Integration tests:
- mocked agent flow
- mocked Groq failures
- mocked Chroma failures
- empty candidate sets

Do not call real Groq from the automated test suite.

=== IMPLEMENTATION ORDER ===

PHASE 1 — Setup
Create Python environment, repository, .env.example, .gitignore and basic
configuration.

PHASE 2 — Dataset and database
Create/curate dataset, database schema, repositories and ingestion.

PHASE 3 — Recommendation engine
Implement deterministic scorer and ranker with tests before connecting the LLM.

PHASE 4 — LangChain + Groq
Implement ChatGroq, system prompt and basic agent flow.

PHASE 5 — Tools
Implement and test all required tools.

PHASE 6 — Agent orchestration
Connect retrieval → ranking → grounded explanation.

PHASE 7 — Gradio shell
Create working local Gradio application and Python event wiring.

PHASE 8 — React
Create Vite React frontend, build the required components and integrate them
with the Gradio/Python data flow.

PHASE 9 — Memory and feedback
Add persistent structured preferences/history/feedback.

PHASE 10 — RAG
Add Chroma semantic retrieval after the core system is stable.

PHASE 11 — Testing
Run the full test suite and fix failures.

PHASE 12 — UI polish
Make the application look like a polished reading recommendation website.

PHASE 13 — Local final demo
Test the exact setup procedure from a clean environment.

PHASE 14 — Deployment preparation
Document Vercel/static frontend deployment, Python service requirements,
persistent storage and environment variables.

PHASE 15 — Documentation
Finalize README, diagrams, demo script, screenshots and viva notes.

=== DEFINITION OF DONE ===

The build is complete only if:

LOCAL:
- React build succeeds.
- Gradio starts.
- Browser UI works.
- Groq works with a server-side key.
- Agent calls tools.
- Real books are retrieved.
- Deterministic ranking works.
- Explanations are grounded.
- Profile/preferences work.
- History/favorites work.
- Feedback changes future ranking.
- Agent Activity panel shows real calls.
- RAG works if enabled in MVP.
- Tests pass.

DEPLOYMENT:
- Vercel responsibilities are explicitly documented.
- Python/Gradio hosting requirements are documented.
- Persistent database strategy is documented.
- Persistent vector strategy is documented if RAG is deployed.
- Environment variables are documented.
- Secrets are never exposed to the browser.
- Known deployment limitations are documented.

=== ANTIGRAVITY WORKING RULES ===

1. Build incrementally.
2. After each phase, run the relevant tests/checks before continuing.
3. Do not rewrite working modules unnecessarily.
4. Do not replace the deterministic ranker with LLM ranking.
5. Do not remove Gradio.
6. Do not remove React.
7. Do not expose the Groq key.
8. Do not invent books when retrieval fails.
9. Do not add infrastructure merely because it sounds impressive.
10. When a deployment limitation is encountered, explain it in README and use
    the simplest supported architecture rather than creating a fragile hack.
11. Keep the project easy for a 2nd-year student to understand and explain
    during a college viva.
12. At the end, provide the exact commands to install, build, run, test and
    deploy the completed project.
```
