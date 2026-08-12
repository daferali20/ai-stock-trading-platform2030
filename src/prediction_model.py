import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# محاولة استيراد TensorFlow (اختياري)
try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    TENSORFLOW_AVAILABLE = True
    print("✅ TensorFlow loaded successfully")
except ImportError:
    print("⚠️ TensorFlow not available. LSTM predictions disabled.")
    TENSORFLOW_AVAILABLE = False

# محاولة استيراد Prophet (اختياري)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    print("✅ Prophet loaded successfully")
except ImportError:
    print("⚠️ Prophet not available. Prophet predictions disabled.")
    PROPHET_AVAILABLE = False

class PredictionModel:
    def __init__(self, symbol):
        self.symbol = symbol
        self.scaler = MinMaxScaler()
        self.lstm_model = None
        self.prophet_model = None
        self.model_dir = 'models/'
        os.makedirs(self.model_dir, exist_ok=True)
        self.tensorflow_available = TENSORFLOW_AVAILABLE
        self.prophet_available = PROPHET_AVAILABLE
    
    def prepare_lstm_data(self, data, lookback=60):
        """تحضير البيانات لنموذج LSTM"""
        if not self.tensorflow_available:
            return None, None
            
        try:
            scaled_data = self.scaler.fit_transform(data['Close'].values.reshape(-1, 1))
            
            X, y = [], []
            for i in range(lookback, len(scaled_data)):
                X.append(scaled_data[i-lookback:i, 0])
                y.append(scaled_data[i, 0])
            
            return np.array(X), np.array(y)
        except Exception as e:
            print(f"⚠️ Error preparing LSTM data: {e}")
            return None, None
    
    def build_lstm_model(self, lookback=60):
        """بناء نموذج LSTM"""
        if not self.tensorflow_available:
            return None
            
        try:
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50),
                Dropout(0.2),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            return model
        except Exception as e:
            print(f"⚠️ Error building LSTM model: {e}")
            return None
    
    def train_lstm(self, data, epochs=50, batch_size=32, lookback=60):
        """تدريب نموذج LSTM"""
        if not self.tensorflow_available:
            print("⚠️ TensorFlow not available. LSTM training skipped.")
            return None
            
        try:
            X, y = self.prepare_lstm_data(data, lookback)
            if X is None or len(X) == 0:
                print("⚠️ Not enough data for LSTM training")
                return None
            
            # تقسيم البيانات
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # بناء النموذج
            self.lstm_model = self.build_lstm_model(lookback)
            if self.lstm_model is None:
                return None
            
            # تدريب
            history = self.lstm_model.fit(
                X_train, y_train,
                epochs=min(epochs, 10),  # تقليل epochs للتجربة
                batch_size=batch_size,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # حفظ النموذج
            model_path = f"{self.model_dir}{self.symbol}_lstm.h5"
            self.lstm_model.save(model_path)
            joblib.dump(self.scaler, f"{self.model_dir}{self.symbol}_scaler.pkl")
            
            print(f"✅ LSTM model trained and saved for {self.symbol}")
            return history
            
        except Exception as e:
            print(f"⚠️ Error training LSTM: {e}")
            return None
    
    def predict_lstm(self, data, days=5):
        """التنبؤ باستخدام LSTM"""
        if not self.tensorflow_available:
            print("⚠️ TensorFlow not available. LSTM prediction skipped.")
            return None
            
        try:
            if self.lstm_model is None:
                model_path = f"{self.model_dir}{self.symbol}_lstm.h5"
                if os.path.exists(model_path):
                    from tensorflow.keras.models import load_model
                    self.lstm_model = load_model(model_path)
                    self.scaler = joblib.load(f"{self.model_dir}{self.symbol}_scaler.pkl")
                else:
                    print(f"⚠️ No LSTM model found for {self.symbol}")
                    return None
            
            # تحضير البيانات للتنبؤ
            last_60 = data['Close'].values[-60:]
            scaled_last_60 = self.scaler.transform(last_60.reshape(-1, 1))
            
            predictions = []
            current_batch = scaled_last_60.reshape(1, 60, 1)
            
            for _ in range(days):
                next_pred = self.lstm_model.predict(current_batch, verbose=0)[0, 0]
                predictions.append(next_pred)
                current_batch = np.roll(current_batch, -1, axis=1)
                current_batch[0, -1, 0] = next_pred
            
            # إرجاع القيم إلى المقياس الأصلي
            predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1))
            return predictions.flatten()
            
        except Exception as e:
            print(f"⚠️ Error in LSTM prediction: {e}")
            return None
    
    def prophet_predict(self, data, days=5):
        """التنبؤ باستخدام Prophet"""
        if not self.prophet_available:
            print("⚠️ Prophet not available. Prophet prediction skipped.")
            return None
            
        try:
            # تحضير البيانات
            df = pd.DataFrame({
                'ds': data['Date'],
                'y': data['Close']
            })
            
            # تدريب النموذج
            model = Prophet()
            model.fit(df)
            
            # التنبؤ
            future = model.make_future_dataframe(periods=days)
            forecast = model.predict(future)
            
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days)
            
        except Exception as e:
            print(f"⚠️ Error in Prophet prediction: {e}")
            return None
    
    def simple_prediction(self, data, days=5):
        """تنبؤ بسيط باستخدام المتوسطات المتحركة (بدون نماذج معقدة)"""
        try:
            close_prices = data['Close'].values
            last_price = close_prices[-1]
            
            # حساب المتوسطات
            sma_5 = np.mean(close_prices[-5:]) if len(close_prices) >= 5 else last_price
            sma_10 = np.mean(close_prices[-10:]) if len(close_prices) >= 10 else last_price
            sma_20 = np.mean(close_prices[-20:]) if len(close_prices) >= 20 else last_price
            
            # اتجاه السعر
            trend = (sma_5 - sma_20) / sma_20 if sma_20 > 0 else 0
            
            # توقع السعر
            predictions = []
            current_price = last_price
            
            for i in range(days):
                # إضافة بعض التغير بناءً على الاتجاه
                change = trend * current_price * 0.1  # 10% من الاتجاه
                current_price = current_price * (1 + change / 100)
                predictions.append(current_price)
            
            return np.array(predictions)
            
        except Exception as e:
            print(f"⚠️ Error in simple prediction: {e}")
            return None
