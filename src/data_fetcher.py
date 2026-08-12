import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import os
from src.config import Config

class DataFetcher:
    def __init__(self):
        self.cache = {}
        
    def fetch_stock_data(self, symbol, period='1y', interval='1d'):
        """جلب بيانات السهم من yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            df.reset_index(inplace=True)
            
            # حساب المؤشرات الأساسية
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            
            return df
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def fetch_multiple_stocks(self, symbols, period='1mo'):
        """جلب بيانات عدة أسهم"""
        data = {}
        for symbol in symbols:
            df = self.fetch_stock_data(symbol, period)
            if df is not None:
                data[symbol] = df
            time.sleep(1)  # تجنب حظر API
        return data
    
    def get_current_price(self, symbol):
        """الحصول على السعر الحالي"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period='1d')['Close'].iloc[-1]
        except:
            return None
    
    def get_market_data(self):
        """جلب بيانات السوق العامة"""
        try:
            indices = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'Dow Jones': '^DJI'
            }
            data = {}
            for name, symbol in indices.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    data[name] = hist['Close'].iloc[-1]
            return data
        except:
            return {}
