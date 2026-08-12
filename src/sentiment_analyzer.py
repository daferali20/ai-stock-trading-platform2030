import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# محاولة استيراد VADER
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    print("⚠️ VADER not available")
    VADER_AVAILABLE = False

# محاولة استيراد Transformers
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️ Transformers not available")
    TRANSFORMERS_AVAILABLE = False

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None
        self.finbert = None
        self.transformers_available = TRANSFORMERS_AVAILABLE
    
    def load_finbert(self):
        """تحميل نموذج FinBERT"""
        if not self.transformers_available:
            return None
        
        if self.finbert is None:
            try:
                self.finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception as e:
                print(f"⚠️ FinBERT error: {e}")
                self.finbert = None
        return self.finbert
    
    def get_news_sentiment(self, symbol, days=7):
        """تحليل مشاعر الأخبار"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
            
            sentiments = []
            
            for item in news[:10]:
                if 'title' in item:
                    text = item['title']
                    
                    # VADER
                    if self.vader:
                        try:
                            vader_score = self.vader.polarity_scores(text)
                            sentiments.append(vader_score['compound'])
                        except:
                            pass
                    
                    # FinBERT
                    if self.transformers_available:
                        try:
                            finbert = self.load_finbert()
                            if finbert:
                                result = finbert(text)[0]
                                if result['label'] == 'positive':
                                    sentiments.append(result['score'])
                                elif result['label'] == 'negative':
                                    sentiments.append(-result['score'])
                        except:
                            pass
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                
                if avg_sentiment > 0.05:
                    sentiment = 'POSITIVE'
                elif avg_sentiment < -0.05:
                    sentiment = 'NEGATIVE'
                else:
                    sentiment = 'NEUTRAL'
                
                return {
                    'sentiment': sentiment,
                    'score': avg_sentiment,
                    'sources': len(sentiments)
                }
            
            return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
            
        except Exception as e:
            print(f"⚠️ Sentiment error: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0, 'sources': 0}
