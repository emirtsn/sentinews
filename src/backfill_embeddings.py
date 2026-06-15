"""
backfill_embeddings.py

Veritabanındaki embedding'i olmayan haberleri toplu olarak embed eder.
Tek seferlik çalıştırılır; sonrasında ingest_news.py yeni haberleri
zaten vektörlü kaydeder.

Çalıştırma:
    python backfill_embeddings.py

1000 haber için tahmini süre:
    CPU  : ~2-3 dakika  (batch_size=64)
    GPU  : ~20-30 saniye
"""

from sqlalchemy.orm import sessionmaker
from src.models.models import engine, News
from src.utils.ai_engine import EmbeddingEngine

BATCH_SIZE = 64  # Bellek/hız dengesi — gerekirse düşür


def run_backfill() -> None:
    session     = sessionmaker(bind=engine)()
    emb_engine  = EmbeddingEngine()

    # Embedding'i olmayan haberleri çek
    pending = (
        session.query(News)
        .filter(News.embedding.is_(None))
        .all()
    )

    if not pending:
        print("Tüm haberler zaten embed edilmiş.")
        return

    print(f"{len(pending)} haber embed edilecek (batch_size={BATCH_SIZE})...")

    total_done = 0

    # BATCH_SIZE'lık gruplara böl
    for batch_start in range(0, len(pending), BATCH_SIZE):
        batch = pending[batch_start : batch_start + BATCH_SIZE]

        # embed_news_batch dict listesi bekliyor
        items = [{"title": n.title, "summary": n.summary or ""} for n in batch]
        embeddings = emb_engine.embed_news_batch(items)

        for news_obj, emb in zip(batch, embeddings):
            news_obj.embedding = emb

        session.commit()

        total_done += len(batch)
        pct = total_done / len(pending) * 100
        print(f"  [{total_done}/{len(pending)}] %{pct:.1f} tamamlandı")

    print(f"\nBackfill tamamlandı. {total_done} haber embed edildi.")


if __name__ == "__main__":
    run_backfill()