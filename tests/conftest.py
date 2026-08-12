import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_data():
    """إنشاء بيانات عينة للاختبارات"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    prices = np.random.randn(100).cumsum() + 100
    return pd.DataFrame({
        'Date': dates,
        'Open': prices + np.random.randn(100) * 2,
        'High': prices + np.random.randn(100) * 3 + 2,
        'Low': prices + np.random.randn(100) * 3 - 2,
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 100)
    })

@pytest.fixture
def sample_symbols():
    """قائمة رموز عينة"""
    return ['AAPL', 'GOOGL', 'MSFT']

@pytest.fixture
def sample_portfolio():
    """بيانات محفظة عينة"""
    return {
        'cash': 5000,
        'positions': {
            'AAPL': {'quantity': 10, 'avg_price': 150},
            'GOOGL': {'quantity': 5, 'avg_price': 100}
        }
    }
