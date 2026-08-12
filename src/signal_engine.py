from src.technical_analysis import TechnicalAnalyzer
from src.sentiment_analyzer import SentimentAnalyzer
from src.prediction_model import PredictionModel
import numpy as np

class SignalEngine:
    def __init__(self):
        self.weights = {
            'technical': 0.4,
            'sentiment': 0.2,
            'prediction': 0.3,
            'market': 0.1
        }
    
    def generate_signal(self, data, symbol):
        """توليد إشارة تداول متكاملة"""
        scores = {}
        
        # 1. التحليل الفني
        ta = TechnicalAnalyzer(data)
        tech_signals = ta.get_technical_signals()
        tech_score = self._calculate_tech_score(tech_signals)
        scores['technical'] = tech_score
        
        # 2. تحليل المشاعر
        sa = SentimentAnalyzer()
        sentiment = sa.get_news_sentiment(symbol)
        sent_score = self._calculate_sentiment_score(sentiment)
        scores['sentiment'] = sent_score
        
        # 3. التنبؤ بالأسعار
        pm = PredictionModel(symbol)
        predictions = pm.predict_lstm(data, days=3)
        if predictions is not None:
            pred_score = self._calculate_prediction_score(predictions, data['Close'].iloc[-1])
        else:
            pred_score = 0
        scores['prediction'] = pred_score
        
        # 4. بيانات السوق
        market_score = self._get_market_score(data)
        scores['market'] = market_score
        
        # حساب النتيجة النهائية
        final_score = sum(scores[factor] * self.weights[factor] 
                         for factor in self.weights.keys())
        
        # توليد الإشارة
        if final_score > 0.3:
            signal = 'BUY'
            confidence = min(final_score * 2, 100)
        elif final_score < -0.3:
            signal = 'SELL'
            confidence = min(abs(final_score) * 2, 100)
        else:
            signal = 'HOLD'
            confidence = 50
        
        return {
            'signal': signal,
            'confidence': confidence,
            'score': final_score,
            'details': scores
        }
    
    def _calculate_tech_score(self, signals):
        """حساب نتيجة التحليل الفني"""
        score = 0
        for indicator, signal in signals.items():
            if 'BUY' in signal:
                score += 0.5
            elif 'SELL' in signal:
                score -= 0.5
        return score / max(len(signals), 1)
    
    def _calculate_sentiment_score(self, sentiment):
        """حساب نتيجة تحليل المشاعر"""
        if sentiment['sentiment'] == 'POSITIVE':
            return sentiment['score']
        elif sentiment['sentiment'] == 'NEGATIVE':
            return -abs(sentiment['score'])
        return 0
    
    def _calculate_prediction_score(self, predictions, current_price):
        """حساب نتيجة التنبؤ"""
        future_price = predictions[-1] if len(predictions) > 0 else current_price
        change_pct = (future_price - current_price) / current_price
        
        if change_pct > 0.02:
            return min(change_pct * 2, 1)
        elif change_pct < -0.02:
            return max(change_pct * 2, -1)
        else:
            return 0
    
    def _get_market_score(self, data):
        """تحليل اتجاه السوق العام"""
        sma_20 = data['SMA_20'].iloc[-1] if 'SMA_20' in data.columns else None
        sma_50 = data['SMA_50'].iloc[-1] if 'SMA_50' in data.columns else None
        
        if sma_20 is not None and sma_50 is not None:
            if sma_20 > sma_50:
                return 0.2
            else:
                return -0.2
        return 0
