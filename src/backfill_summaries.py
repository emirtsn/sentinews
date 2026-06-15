"""
backfill_summaries.py

Veritabanındaki mevcut haberlere AI özeti ekler.
Tek seferlik çalıştırılır; sonrasında ingest_news.py
yeni haberleri zaten özetli kaydeder.

Çalıştırma:
    python -m src.backfill_summaries

1398 haber için tahmini süre:
    CPU : ~40-60 dakika (model her haberi tek tek işler)

Not: İşlem uzun süreceğinden terminal açık kalmalı.
Ctrl+C ile durdurulursa kalan haberler için tekrar çalıştırılabilir —
zaten özeti olan haberler atlanır.
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
from src.models.models import engine, News
from src.utils.ai_engine import SummaryEngine

BATCH_SIZE = 32


def run_backfill() -> None:
    session       = sessionmaker(bind=engine)()
    summary_engine = SummaryEngine()

    # Sadece özeti NULL olan haberleri işle
    pending = session.query(News).filter(News.summary.is_(None)).all()

    if not pending:
        print("Tüm haberlerin özeti zaten mevcut.")
        return

    print(f"{len(pending)} haber özetlenecek...")

    total_done = 0
    for news_obj in pending:
        # Başlık + içerik birleştir
        raw = news_obj.content or news_obj.title or ""
        input_text = f"{news_obj.title}. {raw}" if raw != news_obj.title else news_obj.title

        news_obj.summary = summary_engine.summarize(input_text)
        total_done += 1

        # Her 32 haberde bir commit — bellek ve hız dengesi
        if total_done % BATCH_SIZE == 0:
            session.commit()
            pct = total_done / len(pending) * 100
            print(f"  [{total_done}/{len(pending)}] %{pct:.1f} tamamlandı")

    session.commit()
    print(f"\nBackfill tamamlandı. {total_done} habere özet eklendi.")


if __name__ == "__main__":
    run_backfill()