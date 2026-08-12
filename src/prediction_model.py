import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

class PredictionModel:
    def __init__(self, symbol):
        self.symbol = symbol
        self.model_dir = 'models/'
        os.makedirs(self.model_dir, exist_ok=True)
    
    def simple_prediction(self, data, days=5):
        """تنبؤ بسيط باستخدام المتوسطات المتحركة"""
        try:
            close_prices = data['Close'].values
            last_price = close_prices[-1]
            
            # حساب المتوسطات
            sma_5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else last_price
            sma_20 = np.mean(close_prices[-20:]) if len(close_prices) >= 20 else last_price
            
            # اتجاه السعر
            trend = (sma_5 - sma_20) / sma_20 if sma_20 > 0 else 0
            
            # توقع السعر
            predictions = []
            current_price = last_price
            
            for i in range(days):
                change = trend * current_price * 0.1
                current_price = current_price * (1 + change / 100)
                predictions.append(current_price)
            
            return np.array(predictions)
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return None
    
    def predict_lstm(self, data, days=5):
        """LSTM غير متاح - استخدام التنبؤ البسيط"""
        print("ℹ️ LSTM not available. Using simple prediction.")
        return self.simple_prediction(data, days)
    
    def prophet_predict(self, data, days=5):
        """Prophet غير متاح - استخدام التنبؤ البسيط"""
        print("ℹ️ Prophet not available. Using simple prediction.")
        return self.simple_prediction(data, days)
