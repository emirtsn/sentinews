"""
src/recommender.py

Hibrit öneri motoru — 3 sinyali harmanlayarak haber puanı hesaplar:

    score(n) = w_cat  * category_score(n)
             + w_vec  * cosine_similarity(interest_vector, n.embedding)
             + w_rec  * recency_score(n)

Ağırlıklar toplamı 1'dir; her sinyal 0-1 aralığında normalize edilmiştir.
"""

from __future__ import annotations

import math
import datetime
from typing import List, Optional

from src.models.models import News, UserInteraction
from src.utils.ai_engine import EmbeddingEngine
from sqlalchemy.orm import Session


# Recency için üstel azalma sabiti
RECENCY_HALF_LIFE_HOURS = 24

# Tıklama geçmişinden kaç kayıt kullanılsın?
MAX_INTERACTION_HISTORY = 30

# ---------------------------------------------------------------------------
# Dinamik ağırlıklar — tıklama sayısına göre vektör sinyali güçlenir
# ---------------------------------------------------------------------------
def _get_weights(interaction_count: int) -> tuple[float, float, float]:
    """
    Tıklama sayısı arttıkça vektör sinyali ağırlığı artar,
    kategori sinyali azalır. Recency sabit kalır.

    interaction_count  w_cat  w_vec  w_rec
    0-5  (soğuk)        0.50   0.30   0.20
    6-15 (ısınıyor)     0.30   0.50   0.20
    16+  (sıcak)        0.10   0.70   0.20
    """
    if interaction_count <= 5:
        return 0.50, 0.30, 0.20
    elif interaction_count <= 15:
        return 0.30, 0.50, 0.20
    else:
        return 0.10, 0.70, 0.20


# ---------------------------------------------------------------------------
# Yardımcı: recency skoru  →  [0, 1]
# ---------------------------------------------------------------------------
def _recency_score(published_at: Optional[datetime.datetime]) -> float:
    """
    Üstel azalma: score = e^(-λ * hours_elapsed)
    λ = ln(2) / half_life  →  half_life saate göre yarıya düşer.

    published_at yoksa (None) en düşük puan döner.
    """
    if published_at is None:
        return 0.0

    now = datetime.datetime.utcnow()
    # timezone-naive karşılaştırma güvenliği
    if published_at.tzinfo is not None:
        published_at = published_at.replace(tzinfo=None)

    hours_elapsed = max((now - published_at).total_seconds() / 3600, 0)
    lam = math.log(2) / RECENCY_HALF_LIFE_HOURS
    return math.exp(-lam * hours_elapsed)


# ---------------------------------------------------------------------------
# Yardımcı: kategori skoru  →  {0.0, 1.0}
# ---------------------------------------------------------------------------
def _category_score(news_category: Optional[str], user_prefs: List[str]) -> float:
    if not user_prefs or not news_category:
        return 0.0
    return 1.0 if news_category in user_prefs else 0.0


# ---------------------------------------------------------------------------
# Ana fonksiyon: kullanıcı ilgi vektörünü tıklama geçmişinden üret
# ---------------------------------------------------------------------------
def _build_interest_vector(
    user_id: int,
    db: Session,
    engine: EmbeddingEngine,
) -> Optional[List[float]]:
    """
    Kullanıcının son MAX_INTERACTION_HISTORY tıklamasına ait haber
    embedding'lerinin ağırlıklı ortalamasını döner.

    Daha yeni tıklamalar daha yüksek ağırlık taşır (lineer azalma):
    en son tıklama N, bir önceki N-1, ... ilk tıklama 1 ağırlığına sahip.

    Hiç etkileşim yoksa veya tıklanan haberlerin embedding'i yoksa None döner.
    """
    recent_interactions = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == user_id)
        .order_by(UserInteraction.timestamp.desc())
        .limit(MAX_INTERACTION_HISTORY)
        .all()
    )

    if not recent_interactions:
        return None

    # Tıklanan haberlerin embedding'lerini çek
    news_ids = [i.news_id for i in recent_interactions]
    clicked_news = (
        db.query(News)
        .filter(News.id.in_(news_ids), News.embedding.isnot(None))
        .all()
    )

    if not clicked_news:
        return None

    # news_id → embedding map
    embedding_map = {n.id: n.embedding for n in clicked_news}

    # Ağırlıklı toplam — en yeni tıklama en yüksek ağırlık
    total_interactions = len(recent_interactions)
    weighted_sum = None
    total_weight  = 0.0

    for rank, interaction in enumerate(recent_interactions):
        emb = embedding_map.get(interaction.news_id)
        if emb is None:
            continue

        # Sıra 0 = en yeni → ağırlık = total_interactions
        # Sıra N-1 = en eski → ağırlık = 1
        weight = total_interactions - rank

        if weighted_sum is None:
            weighted_sum = [v * weight for v in emb]
        else:
            weighted_sum = [a + v * weight for a, v in zip(weighted_sum, emb)]

        total_weight += weight

    if weighted_sum is None or total_weight == 0:
        return None

    # Ortalama al ve L2 normalize et
    mean_vec = [v / total_weight for v in weighted_sum]
    norm = math.sqrt(sum(v * v for v in mean_vec))
    if norm == 0:
        return None

    return [v / norm for v in mean_vec]


# ---------------------------------------------------------------------------
# Public API: hibrit sıralama
# ---------------------------------------------------------------------------
def get_hybrid_recommendations(
    user_id: int,
    user_prefs: List[str],
    db: Session,
    limit: int = 50,
) -> List[News]:
    """
    3 sinyali harmanlayarak kişiselleştirilmiş haber listesi döner.

    Sinyal    Ağırlık  Açıklama
    --------- -------- --------------------------------------------------
    Kategori  %30      Kullanıcının seçtiği statik tercihlerle eşleşme
    Vektör    %50      Tıklama geçmişi ilgi vektörü ile cosine similarity
    Recency   %20      Üstel azalma; 24 saatte yarı değere iner

    Kullanıcının hiç tıklama geçmişi yoksa vektör skoru 0 alır,
    sistem kategori + recency ile çalışmaya devam eder (graceful fallback).

    Args:
        user_id   : Mevcut kullanıcının DB id'si.
        user_prefs: Kullanıcının seçtiği kategori listesi. Boş olabilir.
        db        : SQLAlchemy oturumu.
        limit     : Döndürülecek maksimum haber sayısı.

    Returns:
        Puana göre azalan sırada News nesneleri listesi.
    """
    emb_engine = EmbeddingEngine()

    # 1. Tıklama sayısını al ve dinamik ağırlıkları belirle
    interaction_count = (
        db.query(UserInteraction)
        .filter(UserInteraction.user_id == user_id)
        .count()
    )
    W_CATEGORY, W_VECTOR, W_RECENCY = _get_weights(interaction_count)

    # 2. Tıklama geçmişinden kategori bazlı bonus hesapla
    # Her kategorinin toplam tıklanma oranı → normalize edilmiş bonus
    from sqlalchemy import func
    category_clicks = (
        db.query(News.category, func.count(UserInteraction.id).label("cnt"))
        .join(UserInteraction, UserInteraction.news_id == News.id)
        .filter(UserInteraction.user_id == user_id)
        .group_by(News.category)
        .all()
    )
    total_clicks = sum(c.cnt for c in category_clicks) or 1
    # Kategori → normalize edilmiş oran (0-1 arası)
    click_ratio: dict = {c.category: c.cnt / total_clicks for c in category_clicks}

    # 3. Kullanıcı ilgi vektörünü tıklama geçmişinden üret
    interest_vector = _build_interest_vector(user_id, db, emb_engine)

    # 4. Aday havuzunu çek — tüm haberler değerlendirilir
    
    # Kullanıcının daha önce tıkladığı haberleri çıkar
    clicked_ids = {i.news_id for i in db.query(UserInteraction.news_id)
               .filter(UserInteraction.user_id == user_id).all()}
    
    candidates: List[News] = db.query(News).filter(
    News.id.notin_(clicked_ids)
).all() if clicked_ids else db.query(News).all()

    if not candidates:
        return []

    # 5. Her habere puan hesapla
    scored: List[tuple[float, News]] = []

    for news in candidates:
        # --- Sinyal 1: Kategori ---
        s_cat = _category_score(news.category, user_prefs)

        # --- Sinyal 2: Vektör benzerliği ---
        if interest_vector is not None and news.embedding is not None:
            s_vec = sum(a * b for a, b in zip(interest_vector, news.embedding))
            s_vec = (s_vec + 1.0) / 2.0
        else:
            s_vec = 0.0

        # --- Sinyal 3: Güncellik ---
        s_rec = _recency_score(news.published_at)

        # --- Sinyal 4: Tıklama bazlı kategori bonusu ---
        # Kullanıcı o kategoriye ne kadar tıkladıysa o kadar bonus alır
        s_click_bonus = click_ratio.get(news.category, 0.0)

        # --- Ağırlıklı toplam ---
        # Bonus, vektör sinyalinin yanına eklenir ama toplam 1'i aşmaz
        final_score = (
            W_CATEGORY * s_cat
            + W_VECTOR  * s_vec
            + W_RECENCY * s_rec
            + 0.15      * s_click_bonus  # sabit küçük bonus
        )

        scored.append((final_score, news))

    # 5. Puana göre azalan sırala, limit uygula
    scored.sort(key=lambda x: x[0], reverse=True)

    return [news for _, news in scored[:limit]]