# Local Development Guide — Intelligent RAG Chatbot

This guide provides step-by-step instructions for running the application locally on Windows (PowerShell) or Unix (Linux/macOS).

---

## 1. Prerequisites

- **Python**: 3.11 or newer (Python 3.13 supported).
- **Node.js**: v18.0.0 or newer (v22 recommended).
- **npm**: 9.0+ or newer.

---

## 2. Backend Setup

### Windows PowerShell

1. Navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Create your `.env` configuration:
   ```powershell
   Copy-Item .env.example .env
   ```

5. Configure settings inside `.env`:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key (leave blank to run in offline/local mock mode).
   - `VECTOR_STORE_TYPE`: `local` (uses high-performance local NumPy cosine vector store).
   - `EMBEDDING_PROVIDER`: `local_mock` (for zero-cost local testing) or `openrouter`.

6. Run automated test suite:
   ```powershell
   pytest -v
   ```

7. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   API Swagger documentation is accessible at: `http://127.0.0.1:8000/docs`

---

### Unix / macOS (Bash)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -v
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 3. Frontend Setup

1. Open a second terminal and navigate to the frontend folder:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Create `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Ensure `VITE_API_URL=http://localhost:8000` is set.

4. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   Open your browser at `http://localhost:5173`.

---

## 4. Testing End-to-End Workflow

1. Navigate to `http://localhost:5173/login`.
2. Register a new user account (e.g. `test@example.com`, password `Password123!`).
3. In the **Documents** page, upload any text-based PDF (e.g. an article, invoice, or manual).
4. The system automatically extracts text, chunks it, generates vector embeddings, and marks it as **Indexed**.
5. Click **Query** or navigate to **Chat Workspace**.
6. Ask a question regarding the document content.
7. Receive an answer grounded in the document context along with expandable source citations showing exact page numbers and excerpts.
