import sys
import os

# محاولة استيراد VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    print("⚠️ vaderSentiment not installed. Install with: pip install vaderSentiment")
    SentimentIntensityAnalyzer = None

# محاولة استيراد Transformers (اختياري)
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️ transformers not installed. Install with: pip install transformers")
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

import yfinance as yf
import requests
from datetime import datetime, timedelta
import re

class SentimentAnalyzer:
    def __init__(self):
        self.vader = None
        if SentimentIntensityAnalyzer is not None:
            try:
                self.vader = SentimentIntensityAnalyzer()
            except:
                self.vader = None
        self.finbert = None
        self.transformers_available = TRANSFORMERS_AVAILABLE
    
    def load_finbert(self):
        """تحميل نموذج FinBERT"""
        if not self.transformers_available:
            print("⚠️ Transformers not available. FinBERT disabled.")
            return None
            
        if self.finbert is None:
            try:
                self.finbert = pipeline("sentiment-analysis", 
                                       model="ProsusAI/finbert")
                print("✅ FinBERT loaded successfully")
            except Exception as e:
                print(f"⚠️ Error loading FinBERT: {e}")
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
                    if self.vader is not None:
                        try:
                            vader_score = self.vader.polarity_scores(text)
                            sentiments.append(vader_score['compound'])
                        except:
                            pass
                    
                    # FinBERT (إذا كان متاحاً)
                    if self.transformers_available:
                        try:
                            finbert = self.load_finbert()
                            if finbert is not None:
                                result = finbert(text)[0]
                                # تحويل النتيجة إلى رقم
                                if result['label'] == 'positive':
                                    sentiments.append(result['score'])
                                elif result['label'] == 'negative':
                                    sentiments.append(-result['score'])
                        except:
                            pass
            
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
            print(f"⚠️ Error getting news: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0}
    
    def analyze_reddit(self, symbol, limit=10):
        """تحليل مشاعر Reddit (محاكاة)"""
        return {
            'sentiment': 'NEUTRAL',
            'score': 0,
            'posts_analyzed': 0
        }
