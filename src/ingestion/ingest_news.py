import httpx
import datetime
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from src.models.models import engine, News, Base
from src.utils.ai_engine import EmbeddingEngine, SummaryEngine

load_dotenv()
Base.metadata.create_all(bind=engine)

API_KEY  = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/top-headlines"

Session = sessionmaker(bind=engine)
session = Session()

embedding_engine = EmbeddingEngine()
summary_engine   = SummaryEngine()


def fetch_and_save_news(category: str = None, source: str = None) -> None:
    params = {
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": 100,
    }
    if source:
        params["sources"] = source
    elif category:
        params["category"] = category

    current_category = (category or "General").capitalize()
    print(f"\n[{current_category}] haberler toplanıyor...")

    try:
        response = httpx.get(BASE_URL, params=params, timeout=10.0)
        response.raise_for_status()
    except Exception as e:
        print(f"  Bağlantı hatası: {e}")
        return

    articles = response.json().get("articles", [])
    print(f"  API'den gelen: {len(articles)} haber")

    # Yeni haberleri önce listele, sonra toplu embed et (batch daha hızlı)
    new_entries = []
    for art in articles:
        url   = art.get("url", "")
        title = art.get("title", "")
        if not url or not title:
            continue
        if session.query(News).filter(News.url == url).first():
            continue  # Zaten kayıtlı

        raw_content = art.get("content") or art.get("description") or title
        # Başlık + içerik birleştirilerek model girişi oluşturulur
        # content kırpılmışsa sadece title kullan
        clean_content = raw_content if '[+' not in raw_content else ''
        input_text = f"{title}. {clean_content}".strip('. ') if clean_content else title

        new_entries.append({
            "title":        title,
            "content":      raw_content,
            "source":       art["source"]["name"],
            "url":          url,
            "category":     current_category,
            "input_text":   input_text,   # özet için ham metin
            "published_at": datetime.datetime.fromisoformat(
                art["publishedAt"].replace("Z", "+00:00")
            ),
        })

    if not new_entries:
        print("  Yeni haber yok.")
        return

    # 1. Özet üret — tek tek (batch API yok)
    print(f"  {len(new_entries)} yeni haber için özet üretiliyor...")
    for entry in new_entries:
        entry["summary"] = summary_engine.summarize(entry["input_text"])

    # 2. Toplu embedding üret
    print(f"  Embedding üretiliyor...")
    embeddings = embedding_engine.embed_news_batch(new_entries)

    # 3. DB'ye kaydet
    for entry, emb in zip(new_entries, embeddings):
        news_obj = News(
            title        = entry["title"],
            content      = entry["content"],
            source       = entry["source"],
            url          = entry["url"],
            category     = entry["category"],
            summary      = entry["summary"],
            published_at = entry["published_at"],
            embedding    = emb,
        )
        session.add(news_obj)

    session.commit()
    print(f"  {len(new_entries)} yeni haber kaydedildi (embedding dahil).")


if __name__ == "__main__":
    categories = ["technology", "business", "science", "sports", "health", "entertainment"]
    for cat in categories:
        fetch_and_save_news(category=cat)