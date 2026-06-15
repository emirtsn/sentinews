"""
utils/ai_engine.py

Metin → 384 boyutlu vektör dönüşümlerini merkezi olarak yöneten modül.
Kullanılan model: sentence-transformers/all-MiniLM-L6-v2

Kurulum:
    pip install sentence-transformers

Kullanım:
    from src.utils.ai_engine import EmbeddingEngine

    engine = EmbeddingEngine()                    # model ilk çağrıda yüklenir
    vector = engine.embed_news(title, summary)    # haber vektörü
    vector = engine.embed_preferences(["AI", "Teknoloji", "Bilim"])  # tercih vektörü
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# all-MiniLM-L6-v2: 384 boyut, ~80 MB, CPU'da ~14ms/cümle
_MODEL_NAME = "all-MiniLM-L6-v2"
_EXPECTED_DIM = 384


class EmbeddingEngine:
    """
    SentenceTransformer tabanlı embedding motoru.

    Model ağır bir nesne olduğundan Singleton pattern ile sadece bir kez
    yüklenir; her endpoint çağrısında tekrar yüklenmez.

    Attributes:
        _instance : sınıfın tek örneği (Singleton)
        _model    : yüklü SentenceTransformer modeli
    """

    _instance: EmbeddingEngine | None = None
    _model: SentenceTransformer | None = None

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    def __new__(cls) -> EmbeddingEngine:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        """Modeli diskten veya HuggingFace cache'inden yükler."""
        logger.info("EmbeddingEngine: '%s' modeli yükleniyor...", _MODEL_NAME)
        self._model = SentenceTransformer(_MODEL_NAME)
        logger.info("EmbeddingEngine: Model hazır. Çıktı boyutu: %d", _EXPECTED_DIM)

    # ------------------------------------------------------------------
    # Temel encode yöntemi (private)
    # ------------------------------------------------------------------
    def _encode(self, text: str) -> List[float]:
        """
        Ham metni vektöre dönüştürür.

        Args:
            text: Encode edilecek metin (boş olamaz).

        Returns:
            384 elemanlı float listesi. DB'ye doğrudan yazılabilir.

        Raises:
            ValueError: text boş string ise.
        """
        if not text or not text.strip():
            raise ValueError("Encode edilecek metin boş olamaz.")

        vector: np.ndarray = self._model.encode(
            text,
            normalize_embeddings=True,   # cosine similarity için L2 normalize
            show_progress_bar=False,
        )
        return vector.tolist()

    # ------------------------------------------------------------------
    # Public API — Haber vektörü
    # ------------------------------------------------------------------
    def embed_news(self, title: str, summary: str | None = None) -> List[float]:
        """
        Bir haberin başlık ve özetini birleştirerek tek vektör üretir.

        Özet varsa modele daha fazla bağlam sağlar; yoksa yalnızca başlık
        kullanılır. İki alan arasına [SEP] token'ı eklenerek modelin
        cümle sınırını doğru algılaması sağlanır.

        Args:
            title  : Haber başlığı. Zorunlu.
            summary: Haber özeti. Opsiyonel.

        Returns:
            384 elemanlı float listesi.

        Example:
            >>> engine = EmbeddingEngine()
            >>> v = engine.embed_news("Apple yeni iPhone modelini tanıttı", "Etkinlikte...")
            >>> len(v)
            384
        """
        if summary and summary.strip():
            combined = f"{title.strip()} [SEP] {summary.strip()}"
        else:
            combined = title.strip()

        return self._encode(combined)

    # ------------------------------------------------------------------
    # Public API — Toplu haber vektörü
    # ------------------------------------------------------------------
    def embed_news_batch(
        self,
        items: List[dict],
        title_key: str = "title",
        summary_key: str = "summary",
    ) -> List[List[float]]:
        """
        Birden fazla haberi tek seferde (batch) encode eder.

        Tek tek çağırmaya kıyasla GPU/CPU kullanımı çok daha verimlidir.
        Haberleri DB'ye ilk kez toplu yazarken kullan.

        Args:
            items      : Her biri title ve summary içeren dict listesi.
            title_key  : Dict'teki başlık anahtarı (varsayılan: "title").
            summary_key: Dict'teki özet anahtarı (varsayılan: "summary").

        Returns:
            Her habere karşılık gelen 384-boyutlu vektör listesi.
            Sıra, giriş listesiyle birebir eşleşir.

        Example:
            >>> news_items = [{"title": "...", "summary": "..."}, ...]
            >>> vectors = engine.embed_news_batch(news_items)
        """
        texts: List[str] = []
        for item in items:
            title   = item.get(title_key, "").strip()
            summary = item.get(summary_key, "").strip()
            combined = f"{title} [SEP] {summary}" if summary else title
            texts.append(combined)

        if not texts:
            return []

        matrix: np.ndarray = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=64,           # bellek–hız dengesi için sabit tutuldu
            show_progress_bar=False,
        )
        return matrix.tolist()

    # ------------------------------------------------------------------
    # Public API — Kullanıcı tercih vektörü
    # ------------------------------------------------------------------
    def embed_preferences(self, preferences: List[str]) -> List[float]:
        """
        Kullanıcının kategori/ilgi alanı listesini tek bir vektöre indirger.

        Her tercih ayrı ayrı encode edilir, ardından ortalamaları alınarak
        "kullanıcı profil vektörü" oluşturulur. Bu vektör haber vektörleriyle
        cosine similarity hesaplamak için doğrudan kullanılabilir.

        Args:
            preferences: Kullanıcının ilgi alanları. Ör: ["AI", "Spor", "Bilim"]

        Returns:
            384 elemanlı float listesi (L2 normalize edilmiş).

        Raises:
            ValueError: Liste boş ise.

        Example:
            >>> engine = EmbeddingEngine()
            >>> v = engine.embed_preferences(["Yapay Zeka", "Teknoloji"])
            >>> len(v)
            384
        """
        clean = [p.strip() for p in preferences if p and p.strip()]
        if not clean:
            raise ValueError("En az bir tercih girilmelidir.")

        matrix: np.ndarray = self._model.encode(
            clean,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Ortalamanın ardından tekrar normalize et —
        # vektör uzunluğu 1 olmazsa cosine similarity hesabı bozulur.
        mean_vector: np.ndarray = matrix.mean(axis=0)
        norm = np.linalg.norm(mean_vector)
        if norm > 0:
            mean_vector = mean_vector / norm

        return mean_vector.tolist()

    # ------------------------------------------------------------------
    # Yardımcı: cosine similarity
    # ------------------------------------------------------------------
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        İki vektör arasındaki cosine similarity'yi hesaplar.

        embed_* metodları L2 normalize çıktı ürettiğinden bu fonksiyon
        sadece nokta çarpımı (dot product) hesaplar — sonuç aynıdır ve daha hızlıdır.

        Args:
            vec_a: 384-boyutlu vektör.
            vec_b: 384-boyutlu vektör.

        Returns:
            -1.0 ile 1.0 arasında float. 1.0 = tamamen aynı anlam.

        Example:
            >>> score = EmbeddingEngine.cosine_similarity(news_vec, user_vec)
            >>> print(f"Benzerlik: {score:.4f}")
        """
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        return float(np.dot(a, b))


# ===========================================================================
# Özet motoru
# ===========================================================================
import logging as _logging
import warnings as _warnings
from transformers import pipeline as hf_pipeline

# Transformers'ın verbose uyarılarını sustur
_logging.getLogger("transformers").setLevel(_logging.ERROR)
_logging.getLogger("transformers.generation").setLevel(_logging.ERROR)

_SUMMARY_MODEL = "t5-small"


class SummaryEngine:
    """
    T5-small tabanlı haber özet motoru.
    Singleton — model uygulama boyunca tek kez yüklenir.
    """

    _instance: "SummaryEngine | None" = None
    _pipeline = None

    def __new__(cls) -> "SummaryEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self) -> None:
        logger.info("SummaryEngine: '%s' modeli yükleniyor...", _SUMMARY_MODEL)
        with _warnings.catch_warnings():
            _warnings.simplefilter("ignore")
            self._pipeline = hf_pipeline(
                "summarization",
                model=_SUMMARY_MODEL,
                tokenizer=_SUMMARY_MODEL,
                truncation=True,
                framework="pt",
            )
        logger.info("SummaryEngine: Model hazır.")

    def summarize(self, text: str) -> str:
        """
        Verilen metni 2-3 cümleye özetler.

        Args:
            text: Özetlenecek metin. Başlık + içerik birleştirilerek verilebilir.

        Returns:
            Özet metni. Giriş çok kısaysa giriş metni aynen döner.
        """
        if not text or not text.strip():
            return ""

        text = text.strip()[:2000]

        # T5 için prefix zorunlu
        input_text = f"summarize: {text}"

        # Çok kısa metinleri özetleme
        word_count = len(text.split())
        if word_count < 30:
            return text

        # max_length'i dinamik ayarla — input'tan uzun özet üretme
        max_len = min(120, max(40, word_count // 2))
        min_len = min(30, max_len - 10)

        try:
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore")
                result = self._pipeline(
                    input_text,
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=False,
                )
            return result[0]["summary_text"].strip()
        except Exception as e:
            logger.warning("Özet üretilemedi: %s", e)
            return text[:200] + "..." if len(text) > 200 else text