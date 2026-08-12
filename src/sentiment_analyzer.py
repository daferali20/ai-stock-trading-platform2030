from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import yfinance as yf
import requests
from datetime import datetime, timedelta
import re

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        # تحميل نموذج FinBERT (سيتم تحميله عند الاستخدام الأول)
        self.finbert = None
    
    def load_finbert(self):
        """تحميل نموذج FinBERT"""
        if self.finbert is None:
            try:
                self.finbert = pipeline("sentiment-analysis", 
                                       model="ProsusAI/finbert")
            except Exception as e:
                print(f"Error loading FinBERT: {e}")
                self.finbert = None
        return self.finbert
    
    def get_news_sentiment(self, symbol, days=7):
        """تحليل مشاعر الأخبار"""
        try:
            # جلب الأخبار من yfinance
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {'sentiment': 'NEUTRAL', 'score': 0}
            
            # تحليل كل خبر
            sentiments = []
            for item in news[:10]:  # آخر 10 أخبار
                if 'title' in item:
                    text = item['title']
                    # VADER
                    vader_score = self.vader.polarity_scores(text)
                    sentiments.append(vader_score['compound'])
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                if avg_sentiment > 0.05:
                    sentiment = 'POSITIVE'
                elif avg_sentiment < -0.05:
                    sentiment = 'NEGATIVE'
                else:
                    sentiment = 'NEUTRAL'
                
                return {
                    'sentiment': sentiment,
                    'score': avg_sentiment,
                    'sources': len(sentiments)
                }
            
            return {'sentiment': 'NEUTRAL', 'score': 0}
            
        except Exception as e:
            print(f"Error getting news: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0}
    
    def analyze_reddit(self, symbol, limit=10):
        """تحليل مشاعر Reddit (محاكاة)"""
        # ملاحظة: هذه محاكاة، يمكن إضافة API حقيقي
        return {
            'sentiment': 'NEUTRAL',
            'score': 0,
            'posts_analyzed': 0
        }
