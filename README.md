# SentiNews — AI-Powered News Curation Platform

> A personalized news platform that learns from user behavior using machine learning and NLP.

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green) ![Next.js](https://img.shields.io/badge/Next.js-16-black) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue) ![Docker](https://img.shields.io/badge/Docker-✓-2496ED)

---

## 🚀 Features

- **Hybrid Recommendation Engine** — 3-signal algorithm combining category preference, embedding similarity and recency score
- **AI Summarization** — Automatic 2-3 sentence summaries using T5-small
- **Sentiment Analysis** — Positive/negative/neutral classification with VADER
- **Vector-Based Personalization** — 384-dimensional semantic embeddings via all-MiniLM-L6-v2
- **Modern UI** — Editorial design, dark/light mode, skeleton loading animations
- **Automated Pipeline** — Hourly news ingestion and processing loop

---

## 🏗️ Architecture

```
NewsAPI → ingest_news.py → [T5 Summary + Embedding + VADER] → PostgreSQL
                                                                    ↓
Frontend (Next.js) ← FastAPI ← recommender.py ← UserInteraction
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Python 3.11, SQLAlchemy |
| Database | PostgreSQL 15 (Docker) |
| ML/NLP | sentence-transformers, T5-small, VADER |
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Auth | JWT (python-jose), bcrypt |

---

## ⚡ Getting Started

### Prerequisites
- Docker
- Python 3.11
- Node.js 18+

### Setup

```bash
# Clone the repository
git clone https://github.com/emirtsn/sentinews.git
cd sentinews

# Create environment file
cp .env.example .env  # fill in your values

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd web && npm install && cd ..

# Start everything with one command
chmod +x start.sh && ./start.sh
```

### Initial Data Load

```bash
# Fetch news articles
python -m src.main_pipeline

# Generate embeddings for existing articles
python -m src.backfill_embeddings

# Generate AI summaries
python -m src.backfill_summaries
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/news` | All news articles |
| GET | `/news/me` | Personalized feed (JWT required) |
| POST | `/log-interaction` | Log user interaction |
| POST | `/auth/register` | Register new user |
| POST | `/auth/token` | Login |
| PUT | `/users/me/preferences` | Update category preferences |

---

## 📁 Project Structure

```
sentinews/
├── src/
│   ├── api/main.py          # FastAPI endpoints
│   ├── models/models.py     # Database schema
│   ├── ingestion/           # News fetching
│   ├── processing/          # Sentiment analysis
│   ├── utils/ai_engine.py   # Embedding + Summary engines
│   └── recommender.py       # Hybrid recommendation algorithm
├── web/                     # Next.js frontend
├── main_pipeline.py         # Automated pipeline
└── start.sh                 # One-command launcher
```

---

## 👨‍💻 Developer

**Ahmet Emir TOSUN**