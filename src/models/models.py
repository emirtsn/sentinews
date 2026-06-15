from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    Float, create_engine, Boolean, JSON,
    ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import enum
import os
from dotenv import load_dotenv

load_dotenv()

# 1. TEMEL SINIF
Base = declarative_base()


# 2. ENUM: Etkileşim türleri — DB seviyesinde kısıtlama + Python tip güvenliği
class InteractionType(str, enum.Enum):
    click    = "click"
    view     = "view"
    bookmark = "bookmark"


# 3. HABER TABLOSU
class News(Base):
    __tablename__ = "news"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    title           = Column(String(500), nullable=False)
    content         = Column(Text, nullable=True)
    source          = Column(String(100))
    url             = Column(String(1000), unique=True, nullable=False)
    summary         = Column(String, nullable=True)
    category        = Column(String, default="General")
    published_at    = Column(DateTime)
    sentiment_score = Column(Float, default=0.0)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    # YENİ: ARRAY(Float) — JSON'a kıyasla daha hızlı okuma ve daha az disk alanı.
    # pgvector eklentisine geçildiğinde VECTOR(dim) ile değiştirilebilir.
    embedding = Column(ARRAY(Float), nullable=True)

    interactions = relationship(
        "UserInteraction",
        back_populates="news",
        cascade="all, delete-orphan",
    )


# 4. KULLANICI TABLOSU
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255), nullable=True)
    is_active       = Column(Boolean, default=True)
    preferences     = Column(JSON, default=list)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    interactions = relationship(
        "UserInteraction",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# 5. ETKİLEŞİM TABLOSU
class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    news_id          = Column(Integer, ForeignKey("news.id",  ondelete="CASCADE"), nullable=False)
    interaction_type = Column(
        SAEnum(InteractionType, name="interactiontype", create_type=True),
        nullable=False,
    )
    timestamp        = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="interactions")
    news = relationship("News", back_populates="interactions")

    __table_args__ = (
        Index("ix_ui_user_timestamp", "user_id", "timestamp"),
        Index("ix_ui_news_type",      "news_id", "interaction_type"),
    )


# 6. BAĞLANTI AYARLARI
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 7. ŞEMA OLUŞTURMA
def init_db():
    Base.metadata.create_all(engine)
    print("Veritabanı şeması (News, Users, UserInteractions) başarıyla oluşturuldu!")


if __name__ == "__main__":
    init_db()