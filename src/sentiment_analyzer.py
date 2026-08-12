import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# محاولة استيراد VADER من مصدرين محتملين
VADER_AVAILABLE = False
vader_analyzer = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader_analyzer = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    try:
        import nltk
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        nltk.download('vader_lexicon', quiet=True)
        vader_analyzer = SentimentIntensityAnalyzer()
        VADER_AVAILABLE = True
    except Exception:
        VADER_AVAILABLE = False

# محاولة استيراد Transformers
TRANSFORMERS_AVAILABLE = False
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SentimentAnalyzer:
    def __init__(self):
        self.vader = vader_analyzer if VADER_AVAILABLE else None
        self.finbert = None
        self.transformers_available = TRANSFORMERS_AVAILABLE

        # قاموس كلمات مفتاحية احتياطي في حال عدم توفر أي مكتبة خارجية
        self.pos_words = {'up', 'growth', 'gain', 'buy', 'bullish', 'profit', 'higher', 'record', 'surge', 'strong', 'outperform', 'positive'}
        self.neg_words = {'down', 'fall', 'loss', 'sell', 'bearish', 'drop', 'lower', 'risk', 'plunge', 'weak', 'underperform', 'negative'}

    def load_finbert(self):
        """تحميل نموذج FinBERT بكسل وإدارته بأمان"""
        if not self.transformers_available:
            return None
        
        if self.finbert is None:
            try:
                self.finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception as e:
                print(f"⚠️ FinBERT error: {e}")
                self.finbert = None
        return self.finbert

    def _extract_title(self, item):
        """استخراج عنوان الخبر بتوافق مع إصدارات yfinance القديمة والحديثة"""
        if isinstance(item, dict):
            if 'title' in item and item['title']:
                return item['title']
            if 'content' in item and isinstance(item['content'], dict):
                return item['content'].get('title', '')
        return ''

    def _fallback_lexicon_score(self, text):
        """قاموس بسيط لحساب المشاعر في حالة عدم توفر VADER أو FinBERT"""
        words = text.lower().split()
        score = 0
        for w in words:
            if w in self.pos_words:
                score += 1
            elif w in self.neg_words:
                score -= 1
        total = len(words)
        return (score / total) if total > 0 else 0.0

    def get_news_sentiment(self, symbol, days=7):
        """تحليل مشاعر الأخبار بشكل آمن ومحسّن"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                return {'sentiment': 'NEUTRAL', 'score': 0.0, 'sources': 0}

            article_scores = []
            
            # جلب الموديل مرة واحدة فقط خارج الحلقة لتفادي استهلاك الذاكرة
            finbert_model = self.load_finbert() if self.transformers_available else None

            for item in news[:10]:
                title = self._extract_title(item)
                if not title:
                    continue

                scores = []

                # 1. تحليل VADER
                if self.vader:
                    try:
                        v_res = self.vader.polarity_scores(title)
                        scores.append(v_res['compound'])
                    except Exception:
                        pass

                # 2. تحليل FinBERT
                if finbert_model:
                    try:
                        f_res = finbert_model(title)[0]
                        if f_res['label'] == 'positive':
                            scores.append(f_res['score'])
                        elif f_res['label'] == 'negative':
                            scores.append(-f_res['score'])
                        else:
                            scores.append(0.0)
                    except Exception:
                        pass

                # 3. القاموس الاحتياطي
                if not scores:
                    scores.append(self._fallback_lexicon_score(title))

                # حساب متوسط تقييم المقالة الواحدة
                if scores:
                    article_scores.append(sum(scores) / len(scores))

            if article_scores:
                avg_sentiment = sum(article_scores) / len(article_scores)
                
                if avg_sentiment > 0.05:
                    sentiment = 'POSITIVE'
                elif avg_sentiment < -0.05:
                    sentiment = 'NEGATIVE'
                else:
                    sentiment = 'NEUTRAL'

                return {
                    'sentiment': sentiment,
                    'score': round(float(avg_sentiment), 3),
                    'sources': len(article_scores)
                }

            return {'sentiment': 'NEUTRAL', 'score': 0.0, 'sources': 0}

        except Exception as e:
            print(f"⚠️ Sentiment error for {symbol}: {e}")
            return {'sentiment': 'NEUTRAL', 'score': 0.0, 'sources': 0}
