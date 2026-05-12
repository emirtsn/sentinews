import httpx
from sqlalchemy.orm import sessionmaker
from src.models.models import engine, News
import datetime
import os
from dotenv import load_dotenv
from src.models.models import engine, News, Base


Base.metadata.create_all(bind=engine)

# .env dosyasındaki verileri sisteme yükle
load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/top-headlines"

# Veritabanı ile konuşmak için
Session = sessionmaker(bind=engine)
session = Session()

def fetch_and_save_news(category=None, source=None):

    params = {
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": 100,
    }
    
    if source:
        params["sources"] = source
    elif category:
        params["category"] = category

    print(f"{source or category} için haberler toplanıyor...")
    
    current_category = category if category else "General"
    
    try:
        response = httpx.get(BASE_URL, params=params, timeout=10.0)
        response.raise_for_status()
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return

    data = response.json()
    articles = data.get("articles", [])
    
    print(f" API'den gelen haber sayısı: {len(articles)}")
    
    new_count = 0
    for art in articles:
        
        exists = session.query(News).filter(News.url == art['url']).first()
        
        if not exists and art['title'] and art['url']:
            raw_summary = art.get('description') or art.get('content') or art['title']

            new_entry = News(
                title=art['title'],
                content=art['description'] or art['content'],
                source=art['source']['name'],
                url=art['url'],
                category=current_category.capitalize(),
                summary=raw_summary[:180] + "..." if len(raw_summary) > 180 else raw_summary,
                published_at=datetime.datetime.fromisoformat(art['publishedAt'].replace("Z", "+00:00"))
            )
            session.add(new_entry)
            new_count += 1
    
    
    session.commit()
    print(f"İşlem Tamam: {new_count} yeni haber rafa dizildi.")


if __name__ == "__main__":
    categories = ["technology", "business", "science", "sports", "health", "entertainment"]
    
    for cat in categories:
        fetch_and_save_news(category=cat)