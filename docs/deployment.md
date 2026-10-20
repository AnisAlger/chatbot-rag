# Production Deployment Guide — Intelligent RAG Chatbot

This document details how to deploy the application to production:
- **Frontend**: Vercel
- **Backend**: Render (or any Docker/Python PaaS)
- **Database & Vectors**: MongoDB Atlas with Vector Search

---

## 1. MongoDB Atlas Setup

1. Create a free M0 cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
2. Create a database user with read/write permissions.
3. Add your backend server IP (or `0.0.0.0/0` with secure credentials) to IP Access List.
4. Retrieve the connection URI:
   `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Creating the Atlas Search Index (for `$vectorSearch`)
Navigate to **Atlas Search** > **Create Search Index** > **JSON Editor**:
- Database: `chatbot_rag`
- Collection: `chunks`
- Index Name: `rag_vector_index`
- Definition:
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "owner_id"
    },
    {
      "type": "filter",
      "path": "document_id"
    }
  ]
}
```

---

## 2. Backend Deployment (Render)

1. Connect your GitHub repository to [Render](https://render.com).
2. Create a new **Web Service**:
   - **Environment**: Docker (uses `backend/Dockerfile`) or Python 3.11.
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Configure Environment Variables in the Render Dashboard:
   - `APP_ENV`: `production`
   - `APP_SECRET_KEY`: Generate a 32+ character random secret.
   - `JWT_SECRET_KEY`: Generate a 32+ character random secret.
   - `MONGODB_URI`: Your MongoDB Atlas connection URI.
   - `MONGODB_DATABASE`: `chatbot_rag`
   - `OPENROUTER_API_KEY`: Your OpenRouter API key.
   - `OPENROUTER_BASE_URL`: `https://openrouter.ai/api/v1`
   - `OPENROUTER_CHAT_MODEL`: `meta-llama/llama-3.3-70b-instruct:free`
   - `EMBEDDING_PROVIDER`: `openrouter` (or `openai`)
   - `EMBEDDING_API_KEY`: Your embedding API key.
   - `EMBEDDING_MODEL`: `text-embedding-3-small`
   - `VECTOR_STORE_TYPE`: `atlas` (or `local` if persistent disk is attached)
   - `FRONTEND_ORIGINS`: `https://your-frontend.vercel.app`

---

## 3. Frontend Deployment (Vercel)

1. Connect your GitHub repository to [Vercel](https://vercel.com).
2. Configure project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add Environment Variable:
   - `VITE_API_URL`: Your deployed backend URL (e.g. `https://chatbot-rag-backend.onrender.com`).
4. Deploy!

---

## 4. Free-Tier Limitations & Operational Considerations

- **Render Cold Starts**: Render's free tier spins down web services after 15 minutes of inactivity. The first request after sleeping may take 30–50 seconds to respond.
- **Ephemeral Storage on Render**: The container filesystem is ephemeral on the free tier unless a Render Disk is attached. For production document storage, attach a persistent disk or connect AWS S3 / Cloudflare R2 object storage.
- **Atlas Vector Search**: Available on Atlas M0 free clusters in select cloud regions (AWS us-east-1, etc.). If your Atlas cluster region does not support `$vectorSearch`, set `VECTOR_STORE_TYPE=local` on a persistent volume.
- **OpenRouter Free Tier Limits**: Models with `:free` suffix may enforce rate limits (e.g., 20 requests per minute). Configure fallback models or upgrade credits for high concurrency.
