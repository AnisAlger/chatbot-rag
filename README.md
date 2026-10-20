# 🤖 Intelligent RAG Chatbot — Full-Stack AI Application

A production-minded, full-stack Web application that enables users to upload PDF documents, index their contents via vector embeddings, ask questions in natural language, and receive accurate answers strictly grounded in the uploaded files with verifiable citations (document name, page number, and source excerpts).

---

## ✨ Key Features

- **🔐 Robust Authentication & Security**:
  - User registration, login, and profile retrieval via JWT (HS256) and modern bcrypt password hashing.
  - Strict multi-tenant isolation: Users can never read, modify, or query another user's documents, vector chunks, or conversations.
  - Anti-prompt-injection defense: Document contents are treated as untrusted data inside protected prompt boundaries.

- **📄 PDF Processing & Text Extraction**:
  - Multi-layer PDF validation (magic byte check `%PDF-`, size ceiling, structural integrity, password encryption rejection).
  - Page-by-page text extraction via `pypdf`.
  - Automatic detection of scanned/image-only PDFs with clear notice that OCR is required.
  - SHA-256 duplicate file detection and UUID-based secure storage names.

- **✂️ Configurable Chunking**:
  - Sliding-window text chunker (~800 tokens with ~100 tokens overlap).
  - Preserves document ID, owner ID, page numbers, and chunk indices across all chunks.

- **🧠 Dedicated Embeddings & Vector Storage**:
  - Independent embedding provider architecture (OpenRouter, OpenAI, or local deterministic mock).
  - Vector Store abstraction supporting both **MongoDB Atlas Vector Search** (`$vectorSearch`) and high-performance **Local NumPy Vector Store** for local offline development.

- **🎯 Grounded RAG & Deterministic Citations**:
  - Synthesizes answers using only retrieved passages.
  - Admits when information is missing rather than inventing facts or dates.
  - Generates verifiable citations mapped directly to actual retrieved chunks.

- **💻 Premium Modern React Frontend**:
  - Built with React, TypeScript, and Vite.
  - Glassmorphic SaaS design with dark/light theme switching.
  - Document library with drag-and-drop PDF upload, progress indicators, and status badges.
  - Interactive chat workspace with multiline input, auto-scroll, document scope filtering, and expandable citation preview modal.

---

## 🏗️ Project Architecture

```
chatbot-rag/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & middleware
│   │   ├── config.py                # Pydantic settings & validation
│   │   ├── database.py              # MongoDB manager & in-memory fallback
│   │   ├── dependencies.py          # JWT authentication guard
│   │   ├── api/                     # REST API routers
│   │   │   ├── auth.py              # Register, login, me
│   │   │   ├── documents.py         # Upload, list, delete documents
│   │   │   ├── conversations.py     # Threads, messaging, RAG execution
│   │   │   └── health.py            # /health and /ready probes
│   │   ├── models/                  # Internal DB models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── security/                # Bcrypt & JWT logic
│   │   └── services/                # Core business logic
│   │       ├── pdf_service.py       # PDF parsing & OCR detection
│   │       ├── chunking_service.py  # Text splitting & page tracking
│   │       ├── embedding_service.py # Vector embedding provider
│   │       ├── vector_store.py      # Local NumPy & Atlas vector search
│   │       ├── retrieval_service.py # Isolated semantic retrieval
│   │       ├── llm_service.py       # OpenRouter client
│   │       └── rag_service.py       # Prompting & verified citations
│   ├── tests/                       # 20 automated pytest test cases
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                     # API client services
│   │   ├── components/              # Sidebar, CitationModal, etc.
│   │   ├── contexts/                # AuthContext & ThemeContext
│   │   ├── pages/                   # Login, Dashboard, Documents, Chat, Settings
│   │   ├── types/                   # TypeScript interfaces
│   │   ├── App.tsx                  # Protected routing
│   │   ├── index.css                # Glassmorphism design system
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docs/
│   ├── architecture.md              # Detailed data flow & diagrams
│   ├── local-development.md         # Local setup guide
│   └── deployment.md                # Vercel & Render deployment guide
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Start the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --reload --port 8000
```

> **Note**: In local development, the backend automatically uses `LocalVectorStore` and local in-memory/mock services if MongoDB or OpenRouter credentials are not populated, allowing zero-cost instant offline testing.

### 2. Start the Frontend

```powershell
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 🧪 Testing

The backend includes a comprehensive automated test suite verifying all 14 phases:

```powershell
cd backend
.\.venv\Scripts\pytest -v
```

**Test Coverage Highlights:**
- `/health` and `/ready` probes
- User registration, duplicate detection, and login password validation
- Unauthenticated access rejection (401 Unauthorized)
- Valid PDF extraction and character normalization
- Empty bytes, malformed PDFs, and scanned PDF OCR requirement detection
- Text chunking size, overlap, and page metadata preservation
- Vector store insertion and strict cross-user isolation
- End-to-end RAG question answering and citation integrity

---

## 📋 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness check (DB, Vector Store, LLM) |
| `POST` | `/auth/register` | Register new user account |
| `POST` | `/auth/login` | Authenticate and obtain JWT token |
| `GET` | `/auth/me` | Current authenticated user profile |
| `POST` | `/documents/upload` | Upload and index PDF document |
| `GET` | `/documents` | List current user's indexed documents |
| `GET` | `/documents/{id}` | Inspect document details |
| `GET` | `/documents/{id}/status` | Poll document processing status |
| `DELETE` | `/documents/{id}` | Delete document, file, and vector chunks |
| `POST` | `/conversations` | Create a new chat session |
| `GET` | `/conversations` | List user's conversations |
| `GET` | `/conversations/{id}` | Load conversation and message history |
| `POST` | `/conversations/{id}/messages` | Send question, execute RAG, receive citations |

---

## 🛡️ License

MIT License. Designed and built with production-grade practices.
