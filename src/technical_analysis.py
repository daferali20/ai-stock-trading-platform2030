import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands

class TechnicalAnalyzer:
    def __init__(self, data):
        self.data = data
        self.indicators = {}
    
    def calculate_rsi(self, window=14):
        """حساب مؤشر RSI"""
        rsi = RSIIndicator(self.data['Close'], window=window)
        self.indicators['RSI'] = rsi.rsi()
        return self.indicators['RSI']
    
    def calculate_macd(self):
        """حساب مؤشر MACD"""
        macd = MACD(self.data['Close'])
        self.indicators['MACD'] = macd.macd()
        self.indicators['MACD_Signal'] = macd.macd_signal()
        self.indicators['MACD_Diff'] = macd.macd_diff()
        return self.indicators
    
    def calculate_bollinger_bands(self, window=20, std=2):
        """حساب Bollinger Bands"""
        bb = BollingerBands(self.data['Close'], window=window, window_dev=std)
        self.indicators['BB_High'] = bb.bollinger_hband()
        self.indicators['BB_Mid'] = bb.bollinger_mavg()
        self.indicators['BB_Low'] = bb.bollinger_lband()
        self.indicators['BB_Percent'] = bb.bollinger_pband()
        return self.indicators
    
    def calculate_sma_ema(self):
        """حساب SMA و EMA"""
        self.indicators['SMA_20'] = SMAIndicator(self.data['Close'], window=20).sma_indicator()
        self.indicators['SMA_50'] = SMAIndicator(self.data['Close'], window=50).sma_indicator()
        self.indicators['EMA_12'] = EMAIndicator(self.data['Close'], window=12).ema_indicator()
        self.indicators['EMA_26'] = EMAIndicator(self.data['Close'], window=26).ema_indicator()
        return self.indicators
    
    def get_technical_signals(self):
        """تحليل جميع المؤشرات الفنية"""
        signals = {}
        
        # RSI
        rsi = self.calculate_rsi()
        if not rsi.empty:
            last_rsi = rsi.iloc[-1]
            if last_rsi < 30:
                signals['RSI'] = 'BUY (Oversold)'
            elif last_rsi > 70:
                signals['RSI'] = 'SELL (Overbought)'
            else:
                signals['RSI'] = 'NEUTRAL'
        
        # MACD
        macd_data = self.calculate_macd()
        if 'MACD' in macd_data and 'MACD_Signal' in macd_data:
            if macd_data['MACD'].iloc[-1] > macd_data['MACD_Signal'].iloc[-1]:
                signals['MACD'] = 'BUY'
            else:
                signals['MACD'] = 'SELL'
        
        # Bollinger Bands
        bb = self.calculate_bollinger_bands()
        if 'BB_Percent' in bb and not bb['BB_Percent'].empty:
            bb_percent = bb['BB_Percent'].iloc[-1]
            if bb_percent < 0.2:
                signals['BB'] = 'BUY (Lower Band)'
            elif bb_percent > 0.8:
                signals['BB'] = 'SELL (Upper Band)'
            else:
                signals['BB'] = 'NEUTRAL'
        
        return signals
