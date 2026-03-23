from sqlalchemy.orm import sessionmaker
from src.models.models import engine, News
from sqlalchemy import func

Session = sessionmaker(bind=engine)
session = Session()

def generate_daily_report():
    print("\n" + "="*50)
    print("📰 SENTINEWS: GÜNLÜK HABER RAPORU")
    print("="*50 + "\n")

    # 1. Genel İstatistikler
    total_news = session.query(News).count()
    avg_sentiment = session.query(func.avg(News.sentiment_score)).scalar() or 0

    print(f"📊 Toplam Analiz Edilen Haber: {total_news}")
    print(f"🌡️ Günün Genel Duygu Puanı: {avg_sentiment:.2f}")
    
    mood = "POZİTİF 😊" if avg_sentiment > 0.1 else "NEGATİF 😟" if avg_sentiment < -0.1 else "NÖTR 😐"
    print(f"🎭 Bugünün Modu: {mood}\n")

    # 2. En Pozitif 3 Haber (Winners)
    print("🌟 GÜNÜN EN İYİ HABERLERİ:")
    top_positive = session.query(News).order_by(News.sentiment_score.desc()).limit(3).all()
    for i, n in enumerate(top_positive, 1):
        print(f"{i}. [+ {n.sentiment_score:.2f}] {n.title}")

    # 3. En Negatif 3 Haber (Criticals)
    print("\n⚠️ GÜNÜN EN KRİTİK HABERLERİ:")
    top_negative = session.query(News).order_by(News.sentiment_score.asc()).limit(3).all()
    for i, n in enumerate(top_negative, 1):
        print(f"{i}. [- {n.sentiment_score:.2f}] {n.title}")

    print("\n" + "="*50)

if __name__ == "__main__":
    generate_daily_report()