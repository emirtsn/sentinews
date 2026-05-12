from sqlalchemy import Column, Integer, String, Text, DateTime, Float, create_engine, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv

# .env dosyasındaki verileri sisteme yükle
load_dotenv()

# 1. TEMEL SINIF (Base): 
Base = declarative_base()

# 2. HABER TABLOSU (News):
class News(Base):
    __tablename__ = 'news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(100))
    url = Column(String(1000), unique=True, nullable=False)
    summary = Column(String, nullable=True)
    category = Column(String, default="General") 
    published_at = Column(DateTime)
    sentiment_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 3. KULLANICI TABLOSU (User)
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    preferences = Column(JSON, default=list) 
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 4. BAĞLANTI AYARLARI (Engine):
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. TABLOYU OLUŞTURMA FONKSİYONU:
def init_db():
    Base.metadata.create_all(engine)
    print("Veritabanı şeması (News ve Users) başarıyla oluşturuldu!")

if __name__ == "__main__":
    init_db()