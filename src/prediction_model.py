import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from prophet import Prophet
import joblib
import os

class PredictionModel:
    def __init__(self, symbol):
        self.symbol = symbol
        self.scaler = MinMaxScaler()
        self.lstm_model = None
        self.prophet_model = None
        self.model_dir = 'models/'
        os.makedirs(self.model_dir, exist_ok=True)
    
    def prepare_lstm_data(self, data, lookback=60):
        """تحضير البيانات لنموذج LSTM"""
        scaled_data = self.scaler.fit_transform(data['Close'].values.reshape(-1, 1))
        
        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, lookback=60):
        """بناء نموذج LSTM"""
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
    
    def train_lstm(self, data, epochs=50, batch_size=32, lookback=60):
        """تدريب نموذج LSTM"""
        X, y = self.prepare_lstm_data(data, lookback)
        
        # تقسيم البيانات
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # بناء النموذج
        self.lstm_model = self.build_lstm_model(lookback)
        
        # تدريب
        history = self.lstm_model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            verbose=0
        )
        
        # حفظ النموذج
        model_path = f"{self.model_dir}{self.symbol}_lstm.h5"
        self.lstm_model.save(model_path)
        joblib.dump(self.scaler, f"{self.model_dir}{self.symbol}_scaler.pkl")
        
        return history
    
    def predict_lstm(self, data, days=5):
        """التنبؤ باستخدام LSTM"""
        if self.lstm_model is None:
            model_path = f"{self.model_dir}{self.symbol}_lstm.h5"
            if os.path.exists(model_path):
                from tensorflow.keras.models import load_model
                self.lstm_model = load_model(model_path)
                self.scaler = joblib.load(f"{self.model_dir}{self.symbol}_scaler.pkl")
            else:
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
    
    def prophet_predict(self, data, days=5):
        """التنبؤ باستخدام Prophet"""
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
