import yfinance as yf
import pandas as pd
import time

try:
    from src.sentiment_analyzer import SentimentAnalyzer
except ImportError:
    try:
        from sentiment_analyzer import SentimentAnalyzer
    except ImportError:
        SentimentAnalyzer = None

class DataFetcher:
    def __init__(self):
        self.cache = {}
        # ربط محلل المشاعر ليعمل تلقائياً مع الواجهة
        if SentimentAnalyzer is not None:
            try:
                self.sentiment_analyzer = SentimentAnalyzer()
            except Exception as e:
                print(f"Warning: Could not initialize SentimentAnalyzer: {e}")
                self.sentiment_analyzer = None
        else:
            self.sentiment_analyzer = None

    def fetch_stock_data(self, symbol, period='1y', interval='1d'):
        """جلب بيانات السهم من yfinance مع المعالجة الآمنة للبيانات والتواريخ"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            # التحقق من وجود بيانات
            if df is None or df.empty:
                print(f"⚠️ لا توجد بيانات للرمز: {symbol}")
                return None

            # إعادة ضبط المؤشر وتوحيد اسم عمود التاريخ
            df = df.reset_index()
            date_col = 'Date' if 'Date' in df.columns else ('Datetime' if 'Datetime' in df.columns else df.columns[0])
            df.rename(columns={date_col: 'Date'}, inplace=True)

            # إزالة المنطقة الزمنية لتفادي أخطاء Plotly وStreamlit
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)

            # حساب المتوسطات المتحركة بأمان
            if len(df) >= 20:
                df['SMA_20'] = df['Close'].rolling(window=20).mean()
            else:
                df['SMA_20'] = df['Close']

            if len(df) >= 50:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
            else:
                df['SMA_50'] = df['Close']

            df['Volume_SMA'] = df['Volume'].rolling(window=min(20, len(df))).mean()

            return df

        except Exception as e:
            print(f"❌ خطأ أثناء جلب بيانات {symbol}: {e}")
            return None

    def fetch_multiple_stocks(self, symbols, period='1mo'):
        """جلب بيانات عدة أسهم مع فاصل زمني آمن"""
        data = {}
        for symbol in symbols:
            df = self.fetch_stock_data(symbol, period)
            if df is not None and not df.empty:
                data[symbol] = df
            time.sleep(0.3)
        return data

    def get_current_price(self, symbol):
        """الحصول على السعر الحالي مع نظام دعم لآخر 5 أيام لتفادي إغلاق الأسواق"""
        try:
            ticker = yf.Ticker(symbol)
            # استخدام 5d لضمان جلب آخر سعر إغلاق في عطلات نهاية الأسبوع
            hist = ticker.history(period='5d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            if hasattr(ticker, 'fast_info') and 'lastPrice' in ticker.fast_info:
                return float(ticker.fast_info['lastPrice'])

            return None
        except Exception as e:
            print(f"❌ خطأ في جلب السعر الحالي لـ {symbol}: {e}")
            return None

    def get_market_data(self):
        """جلب بيانات مؤشرات السوق الرئيسية"""
        indices = {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'Dow Jones': '^DJI'
        }
        data = {}
        for name, symbol in indices.items():
            price = self.get_current_price(symbol)
            if price is not None:
                data[name] = price
        return data
