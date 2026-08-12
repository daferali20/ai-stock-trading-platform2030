import sys
import os

# محاولة استيراد VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    print("⚠️ vaderSentiment not installed")
    VADER_AVAILABLE = False
    SentimentIntensityAnalyzer = None

import yfinance as yf
import requests
from datetime import datetime, timedelta
import re

class SentimentAnalyzer:
    def __init__(self):
        self.vader = None
        if VADER_AVAILABLE and SentimentIntensityAnalyzer is not None:
            try:
                self.vader = SentimentIntensityAnalyzer()
                print("✅ VADER loaded")
            except:
                self.vader = None
    
    def get_news_sentiment(self, symbol, days=7):
        """تحليل مشاعر الأخبار"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
            
            sentiments = []
            for item in news[:10]:
                if 'title' in item and self.vader is not None:
                    try:
                        text = item['title']
                        vader_score = self.vader.polarity_scores(text)
                        sentiments.append(vader_score['compound'])
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
            
            return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
    
    def analyze_reddit(self, symbol, limit=10):
        return {'sentiment': 'NEUTRAL', 'score': 0, 'posts_analyzed': 0}
