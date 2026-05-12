from src.ingestion.ingest_news import fetch_and_save_news
from src.processing.sentiment_analysis import run_sentiment_analysis
import time

def start_pipeline():
    print("Otomatik Boru Hattı Başlatıldı...")
    
    categories = ["technology", "business", "science", "sports", "health", "entertainment"]
    
    print("\n--- 1. ADIM: HABER TOPLAMA ---")
    for cat in categories:
        fetch_and_save_news(category=cat) #
    

    print("\n--- 2. ADIM: DUYGU ANALİZİ ---")
    run_sentiment_analysis() #
    
    print("\n İşlem Başarıyla Tamamlandı. Veriler Arayüze Hazır!")

if __name__ == "__main__":
    while True:
        start_pipeline()
        print("Bir sonraki tarama için 1 saat bekleniyor...")
        time.sleep(3600)