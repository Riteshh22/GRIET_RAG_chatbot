# HybridRAG Enterprise Platform

A production-grade Hybrid Retrieval-Augmented Generation (RAG) platform with Dense Search, BM25, Re-ranking, and Citation Verification.

![Architecture](https://img.shields.io/badge/React-18-blue?style=flat) ![Backend](https://img.shields.io/badge/FastAPI-0.111-green?style=flat) ![LLM](https://img://shapes-badge?label=Qwen3:8B-orange) ![VectorDB](https://img.shields.io/badge/Qdrant-VectorDB-cyan?style=flat)

## Overview

HybridRAG Enterprise is a full-stack AI platform that provides grounded answers from your documents using:

- **Hybrid Search**: Combines Dense (vector) retrieval with BM25 sparse retrieval using Reciprocal Rank Fusion
- **Re-ranking**: Cross-encoder re-ranking using BAAI/bge-reranker-base
- **Citation Verification**: Every answer includes document citations with page numbers
- **Streaming Responses**: Real-time token-by-token streaming via Server-Sent Events
- **Evaluation Dashboard**: RAGAS-based metrics for faithfulness, relevancy, and retrieval quality

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  React Frontend                       │
│         Vite + Tailwind + Framer Motion               │
└─────────────┬──────────────────────┬─────────────────┘
              │ REST API             │ SSE Stream
              ▼                      ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI Backend                       │
│                   Python 3.11+                         │
├────────────┬─────────────┬────────────┬──────────────┤
│ Document   │ Embedding   │ Retrieval  │ LLM          │
│ Processor  │ Service     │ Service    │ Service      │
│            │             │            │              │
│ • PDF      │ • BGE       │ • Dense    │ • Ollama     │
│ • DOCX     │ • Sentence  │ • BM25     │ • Qwen3:8B   │
│ • TXT      │   Transform │ • Hybrid   │ • Streaming  │
│ • CSV      │             │ • Re-rank  │              │
│ • Markdown │             │            │              │
├────────────┴─────────────┴────────────┴──────────────┤
│              Qdrant Vector Database                    │
└──────────────────────────────────────────────────────┘
```

## Folder Structure

```
hybrid-rag/
├── frontend/                    # React + Vite frontend
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API service layer
│   │   └── utils/               # Utility functions
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── backend/                     # Python FastAPI backend
│   ├── api/                     # API configuration
│   ├── config/                  # App settings
│   ├── database/                # Database connections
│   ├── embeddings/              # Embedding service
│   ├── document_processor/      # Document parsing + chunking
│   ├── llm/                     # LLM service (Ollama)
│   ├── models/                  # Pydantic models
│   ├── reranker/                # Re-ranking service
│   ├── retrieval/               # BM25 + Hybrid retrieval
│   ├── routes/                  # API routes
│   ├── services/                # Core services
│   ├── utils/                   # Utility functions
│   ├── vectorstore/             # Qdrant integration
│   ├── tests/                   # Test files
│   └── main.py                  # FastAPI entry point
├── documents/                   # Document storage
├── uploads/                     # Uploaded files
├── requirements.txt             # Python dependencies
└── README.md
```

## Tech Stack

### Frontend
- **React 18** with Vite
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Recharts** for data visualization
- **React Markdown** for markdown rendering
- **React Dropzone** for file uploads

### Backend
- **FastAPI** with Uvicorn
- **Pydantic** for data validation
- **LangChain** for document processing

### AI/ML
- **Ollama** running **Qwen3:8B** for generation
- **BAAI/bge-small-en-v1.5** for embeddings (384 dimensions)
- **BAAI/bge-reranker-base** for cross-encoder re-ranking
- **Qdrant** for vector storage
- **BM25 (rank_bm25)** for sparse retrieval
- **RAGAS** methodology for evaluation

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Node.js 18+**
3. **Ollama** ([install](https://ollama.ai))
4. **Qdrant** ([install](https://qdrant.tech/documentation/quickstart/))

### 1. Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 2. Pull Ollama Model

```bash
ollama pull qwen3:8b
```

### 3. Start Ollama

```bash
ollama serve
```

### 4. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### 5. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload and index a document |
| POST | `/api/chat` | Send a chat query (non-streaming) |
| POST | `/api/chat/stream` | Send a chat query (streaming SSE) |
| POST | `/api/search` | Search documents |
| POST | `/api/reindex/{doc_id}` | Re-index a document |
| DELETE | `/api/delete/{doc_id}` | Delete a document |
| GET | `/api/list-documents` | List all documents |
| GET | `/api/system-info` | Get system information |
| GET | `/api/system-health` | Get system health metrics |
| GET | `/api/evaluation/metrics` | Get evaluation metrics |

## Application Pages

1. **Landing Page** - Retro-modern design with animated pipeline visualization
2. **Dashboard** - System statistics, status, and evaluation overview
3. **AI Chat** - ChatGPT-style interface with streaming, sources panel, and pipeline viz
4. **Documents** - Drag & drop upload, document management, re-indexing
5. **Evaluation** - RAGAS metrics with interactive charts (Bar, Radar)
6. **Architecture** - Interactive system architecture diagram
7. **Settings** - Configure chunking, retrieval, generation, and model parameters

## How It Works

### Hybrid RAG Pipeline

1. **Upload**: User uploads a document (PDF, DOCX, TXT, CSV, MD)
2. **Process**: Document is parsed, text extracted, and split into chunks
3. **Embed**: Chunks are embedded using BGE-small-en-v1.5
4. **Store**: Embeddings + metadata stored in Qdrant
5. **Query**: User asks a question
6. **Dense Search**: Query embedding compared against all vectors
7. **BM25 Search**: Query tokenized and matched against chunk tokens
8. **Hybrid Fusion**: Results merged using Reciprocal Rank Fusion (RRF)
9. **Re-rank**: Cross-encoder re-ranks merged results
10. **Generate**: Qwen3 generates an answer using top-k context
11. **Cite**: Sources with document names, page numbers, and scores returned

## Future Improvements

- [ ] User authentication and multi-tenancy
- [ ] Persistent conversation history with database
- [ ] WebSocket-based streaming
- [ ] Batch document processing
- [ ] Custom embedding model fine-tuning
- [ ] A/B testing for retrieval strategies
- [ ] Document chunk visualization
- [ ] Export chat history
- [ ] Multi-language support
- [ ] Admin panel with usage analytics

