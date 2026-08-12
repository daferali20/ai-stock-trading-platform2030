import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.signal_engine import SignalEngine

class TestSignalEngine(unittest.TestCase):
    """اختبارات محرك الإشارات"""
    
    def setUp(self):
        # إنشاء بيانات اختبار
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = np.random.randn(100).cumsum() + 100
        self.data = pd.DataFrame({
            'Date': dates,
            'Open': prices + np.random.randn(100) * 2,
            'High': prices + np.random.randn(100) * 3 + 2,
            'Low': prices + np.random.randn(100) * 3 - 2,
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, 100),
            'SMA_20': prices.rolling(20).mean(),
            'SMA_50': prices.rolling(50).mean()
        })
        self.engine = SignalEngine()
        self.symbol = 'TEST'
    
    def test_generate_signal(self):
        """اختبار توليد إشارة"""
        signal = self.engine.generate_signal(self.data, self.symbol)
        
        self.assertIsNotNone(signal)
        self.assertIn('signal', signal)
        self.assertIn('confidence', signal)
        self.assertIn('score', signal)
        self.assertIn('details', signal)
        self.assertIn(signal['signal'], ['BUY', 'HOLD', 'SELL'])
        self.assertGreaterEqual(signal['confidence'], 0)
        self.assertLessEqual(signal['confidence'], 100)
    
    def test_calculate_tech_score(self):
        """اختبار حساب النتيجة الفنية"""
        signals = {'RSI': 'BUY', 'MACD': 'BUY', 'BB': 'NEUTRAL'}
        score = self.engine._calculate_tech_score(signals)
        self.assertGreater(score, 0)
        
        signals = {'RSI': 'SELL', 'MACD': 'SELL', 'BB': 'SELL'}
        score = self.engine._calculate_tech_score(signals)
        self.assertLess(score, 0)
    
    def test_calculate_sentiment_score(self):
        """اختبار حساب نتيجة المشاعر"""
        sentiment = {'sentiment': 'POSITIVE', 'score': 0.5}
        score = self.engine._calculate_sentiment_score(sentiment)
        self.assertGreater(score, 0)
        
        sentiment = {'sentiment': 'NEGATIVE', 'score': -0.5}
        score = self.engine._calculate_sentiment_score(sentiment)
        self.assertLess(score, 0)
    
    def test_get_market_score(self):
        """اختبار حساب نتيجة السوق"""
        score = self.engine._get_market_score(self.data)
        self.assertIsNotNone(score)

if __name__ == '__main__':
    unittest.main()
