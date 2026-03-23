from sqlalchemy.orm import sessionmaker
from src.models.models import engine, News
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 1. ANALİZ MOTORUNU HAZIRLAMA
analyzer = SentimentIntensityAnalyzer()

# 2. VERİTABANI BAĞLANTISI
Session = sessionmaker(bind=engine)
session = Session()

def run_sentiment_analysis():
    print("Sentinews Zekası: Analiz başlıyor...")
    
    unscored_news = session.query(News).filter(News.sentiment_score == 0.0).all()
    
    if not unscored_news:
        print("Analiz edilecek yeni haber bulunamadı.")
        return

    for news_item in unscored_news:
     
        full_text = f"{news_item.title}. {news_item.content or ''}"
        
        # 3. VADER İLE ANALİZ
        scores = analyzer.polarity_scores(full_text)
        compound_score = scores['compound']
        
        # 4. PUANI VERİTABANINA YAZMA
        news_item.sentiment_score = compound_score
        
        print(f"Skor: {compound_score:.2f} | Başlık: {news_item.title[:50]}...")

    # 5. TÜMÜNÜ KAYDETME
    session.commit()
    print(f"Toplam {len(unscored_news)} haber mühürlendi.")

if __name__ == "__main__":
    run_sentiment_analysis()