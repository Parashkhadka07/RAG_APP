# NotebookRAG

A self-hosted, NotebookLM-style RAG (Retrieval-Augmented Generation) application built with Django. Upload documents into notebooks and ask questions about them — answers are generated using only your own content, with source citations.

## Features

- **Notebooks** — organize documents into separate, isolated collections
- **Multi-format upload** — PDF, DOCX, and TXT supported
- **Multi-document retrieval** — ask a question and get answers drawn from across all documents in a notebook
- **Source citations** — every answer shows which file (and page, for PDFs) it was drawn from
- **Markdown-formatted answers** — responses are rendered with headings, bullet points, and bold text for readability
- **Delete notebooks/documents** — remove a document and the notebook's index rebuilds automatically; delete a whole notebook and everything (files, chunks, index) is cleaned up
- **User accounts** — signup/login/logout, notebooks are private per user
- **Dark theme UI** — built with Tailwind CSS (via CDN), no build step required

## Architecture

```
Upload flow:
  file(s) → ingestion.py (LangChain loaders) → chunking.py (text splitter)
          → embedding_store.py (sentence-transformers + FAISS) → saved to disk

Query flow:
  question → embedding_store.py (load FAISS index)
           → llm.py (RetrievalQA chain: retrieve top-k chunks → prompt → Groq/Llama 3.3)
           → answer + source citations → rendered in chat UI
```

Each notebook gets its own isolated FAISS index, stored under `indexes/notebook_<id>/`, so retrieval never crosses between notebooks.

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django |
| Document loading | LangChain (`PyPDFLoader`, `Docx2txtLoader`, `TextLoader`) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) via `langchain-huggingface` |
| Vector store | FAISS (local, file-based) |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Frontend | Django templates + Tailwind CSS (CDN) + vanilla JS |
| Markdown rendering | `marked.js` (CDN) |

## Project structure

```
pipeline/
├── models.py            # Notebook, Document, Chunk
├── views.py              # views + upload/ask/delete endpoints
├── urls.py                # routes
├── admin.py               # Django admin registration
├── ingestion.py            # file -> LangChain Document objects
├── chunking.py              # Document objects -> chunks
├── embedding_store.py        # chunks -> FAISS index (build/save/load)
├── llm.py                     # FAISS index + question -> answer + sources
└── templates/pipeline/
    ├── notebook_app.html       # notebook list + chat UI (single combined template)
    ├── login.html
    └── signup.html
```

## Setup

### 1. Clone and create a virtual environment

```bash
python -m venv myenv
myenv\Scripts\activate        # Windows
source myenv/bin/activate     # macOS/Linux
```

### 2. Install dependencies

```bash
pip install django langchain langchain-community langchain-classic langchain-groq langchain-huggingface faiss-cpu pypdf docx2txt sentence-transformers python-dotenv
```

### 3. Configure environment variables

Create a `.env` file in the project root (same level as `manage.py`):

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key from [console.groq.com](https://console.groq.com/keys).

### 4. Configure Django settings

In `settings.py`, ensure:

```python
INSTALLED_APPS = [
    ...
    'pipeline',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'notebook_list'
LOGOUT_REDIRECT_URL = 'login'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Include the app's URLs in the project's root `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pipeline.urls")),
]
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Run the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`, sign up for an account, and start creating notebooks.

## Usage

1. **Sign up / log in**
2. **Create a notebook** from the notebook list page
3. **Upload documents** (PDF/DOCX/TXT) — they're chunked, embedded, and indexed automatically
4. **Ask questions** in the chat panel — answers are generated from your documents only, with cited sources
5. **Delete** a document or an entire notebook using the × buttons; the index is rebuilt or removed accordingly

## Known limitations / future improvements

- Index rebuilds happen synchronously on upload/delete — fine for small notebooks, but re-embeds all remaining documents each time, which could get slow with many large files. A background task queue (e.g. Celery) would fix this.
- No document preview or per-document "scope this question to one file" toggle yet.
- No streaming responses — the full answer is generated before anything is shown in the chat.

## License

Personal / academic project — no license specified.