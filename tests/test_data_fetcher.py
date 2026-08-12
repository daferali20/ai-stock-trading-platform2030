import unittest
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import DataFetcher

class TestDataFetcher(unittest.TestCase):
    """اختبارات لجلب البيانات"""
    
    def setUp(self):
        self.fetcher = DataFetcher()
        self.symbol = 'AAPL'
    
    def test_fetch_stock_data(self):
        """اختبار جلب بيانات السهم"""
        df = self.fetcher.fetch_stock_data(self.symbol, period='5d')
        self.assertIsNotNone(df)
        self.assertFalse(df.empty)
        self.assertIn('Close', df.columns)
        self.assertIn('Open', df.columns)
        self.assertIn('High', df.columns)
        self.assertIn('Low', df.columns)
        self.assertIn('Volume', df.columns)
    
    def test_fetch_multiple_stocks(self):
        """اختبار جلب عدة أسهم"""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        data = self.fetcher.fetch_multiple_stocks(symbols, period='5d')
        
        self.assertEqual(len(data), len(symbols))
        for symbol in symbols:
            self.assertIn(symbol, data)
            self.assertIsNotNone(data[symbol])
            self.assertFalse(data[symbol].empty)
    
    def test_get_current_price(self):
        """اختبار الحصول على السعر الحالي"""
        price = self.fetcher.get_current_price(self.symbol)
        self.assertIsNotNone(price)
        self.assertGreater(price, 0)
    
    def test_get_market_data(self):
        """اختبار جلب بيانات السوق"""
        market_data = self.fetcher.get_market_data()
        self.assertIsNotNone(market_data)
        self.assertIn('S&P 500', market_data)

if __name__ == '__main__':
    unittest.main()
