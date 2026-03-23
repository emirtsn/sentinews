from sqlalchemy import Column, Integer, String, Text, DateTime, Float, create_engine
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
    __tablename__ = 'news' # Veritabanındaki tablonun fiziksel adı

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    title = Column(String(500), nullable=False)
    
    content = Column(Text, nullable=True)
    
    source = Column(String(100))
    
    url = Column(String(1000), unique=True, nullable=False)
    
    published_at = Column(DateTime)
    
    sentiment_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 3. BAĞLANTI AYARLARI (Engine):
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# 4. TABLOYU OLUŞTURMA FONKSİYONU:
def init_db():
    Base.metadata.create_all(engine)
    print("✅ Veritabanı şeması başarıyla oluşturuldu!")

if __name__ == "__main__":
    init_db()