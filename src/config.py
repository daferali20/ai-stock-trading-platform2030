import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', '')
    TWELVE_DATA_KEY = os.getenv('TWELVE_DATA_KEY', '')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Email
    EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER', '')
    
    # Trading Settings
    INITIAL_CAPITAL = 10000
    MAX_POSITION_SIZE = 0.2  # 20% من رأس المال
    STOP_LOSS = 0.05  # 5%
    TAKE_PROFIT = 0.15  # 15%
    
    # Data Settings
    DATA_DIR = 'data/'
    DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    CACHE_DURATION = 300  # 5 دقائق
    
    # Model Settings
    LSTM_LOOKBACK = 60
    LSTM_EPOCHS = 50
    LSTM_BATCH_SIZE = 32
