import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.technical_analysis import TechnicalAnalyzer

class TestTechnicalAnalysis(unittest.TestCase):
    """اختبارات التحليل الفني"""
    
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
            'Volume': np.random.randint(1000, 10000, 100)
        })
        self.analyzer = TechnicalAnalyzer(self.data)
    
    def test_calculate_rsi(self):
        """اختبار حساب RSI"""
        rsi = self.analyzer.calculate_rsi()
        self.assertIsNotNone(rsi)
        self.assertEqual(len(rsi), len(self.data))
        self.assertTrue((rsi >= 0).all())
        self.assertTrue((rsi <= 100).all())
    
    def test_calculate_macd(self):
        """اختبار حساب MACD"""
        macd_data = self.analyzer.calculate_macd()
        self.assertIn('MACD', macd_data)
        self.assertIn('MACD_Signal', macd_data)
        self.assertIn('MACD_Diff', macd_data)
        self.assertEqual(len(macd_data['MACD']), len(self.data))
    
    def test_calculate_bollinger_bands(self):
        """اختبار حساب Bollinger Bands"""
        bb = self.analyzer.calculate_bollinger_bands()
        self.assertIn('BB_High', bb)
        self.assertIn('BB_Mid', bb)
        self.assertIn('BB_Low', bb)
        self.assertIn('BB_Percent', bb)
        self.assertEqual(len(bb['BB_High']), len(self.data))
    
    def test_get_technical_signals(self):
        """اختبار الحصول على الإشارات الفنية"""
        signals = self.analyzer.get_technical_signals()
        self.assertIsNotNone(signals)
        self.assertIn('RSI', signals)
        self.assertIn('MACD', signals)
        self.assertIn('BB', signals)

if __name__ == '__main__':
    unittest.main()
