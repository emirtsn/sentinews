"""
main_pipeline.py

Her saat çalışan otomatik boru hattı:
    1. Haber toplama   — NewsAPI'den yeni haberler çekilir, embedding dahil kaydedilir
    2. Duygu analizi   — Embedding'i olan ama sentiment skoru 0 olan haberler analiz edilir
"""

from src.ingestion.ingest_news import fetch_and_save_news
from src.processing.sentiment_analysis import run_sentiment_analysis
import time

CATEGORIES = ["technology", "business", "science", "sports", "health", "entertainment"]


def start_pipeline() -> None:
    print("\n" + "=" * 50)
    print("Otomatik Boru Hattı Başlatıldı")
    print("=" * 50)

    print("\n--- 1. ADIM: HABER TOPLAMA + EMBEDDING ---")
    for cat in CATEGORIES:
        fetch_and_save_news(category=cat)

    print("\n--- 2. ADIM: DUYGU ANALİZİ ---")
    run_sentiment_analysis()

    print("\n✓ Pipeline tamamlandı. Veriler arayüze hazır.")


if __name__ == "__main__":
    while True:
        start_pipeline()
        print("\nBir sonraki tarama için 1 saat bekleniyor...")
        time.sleep(3600)