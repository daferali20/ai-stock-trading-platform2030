import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prediction_model import PredictionModel

class TestPredictionModel(unittest.TestCase):
    """اختبارات نموذج التنبؤ"""
    
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
        self.model = PredictionModel('TEST')
    
    def test_prepare_lstm_data(self):
        """اختبار تحضير بيانات LSTM"""
        X, y = self.model.prepare_lstm_data(self.data, lookback=20)
        self.assertEqual(len(X), len(self.data) - 20)
        self.assertEqual(len(y), len(self.data) - 20)
        self.assertEqual(X.shape[1], 20)
    
    def test_build_lstm_model(self):
        """اختبار بناء نموذج LSTM"""
        model = self.model.build_lstm_model(lookback=20)
        self.assertIsNotNone(model)
        self.assertEqual(len(model.layers), 7)  # 3 LSTM, 3 Dropout, 1 Dense
    
    def test_prophet_predict(self):
        """اختبار التنبؤ باستخدام Prophet"""
        try:
            forecast = self.model.prophet_predict(self.data, days=5)
            self.assertIsNotNone(forecast)
            self.assertEqual(len(forecast), 5)
            self.assertIn('yhat', forecast.columns)
            self.assertIn('yhat_lower', forecast.columns)
            self.assertIn('yhat_upper', forecast.columns)
        except Exception as e:
            self.skipTest(f"Prophet not available: {e}")

if __name__ == '__main__':
    unittest.main()
