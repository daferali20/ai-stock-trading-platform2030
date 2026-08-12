import sys
import os

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    print("⚠️ vaderSentiment not installed. Install with: pip install vaderSentiment")
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
                print("✅ VADER loaded successfully")
            except Exception as e:
                print(f"⚠️ Error loading VADER: {e}")
                self.vader = None
    
    def get_news_sentiment(self, symbol, days=7):
        """تحليل مشاعر الأخبار باستخدام VADER فقط"""
        try:
            # جلب الأخبار من yfinance
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
            
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
            print(f"⚠️ Error getting news: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
    
    def analyze_reddit(self, symbol, limit=10):
        """تحليل مشاعر Reddit (محاكاة)"""
        return {
            'sentiment': 'NEUTRAL',
            'score': 0,
            'posts_analyzed': 0
        }
