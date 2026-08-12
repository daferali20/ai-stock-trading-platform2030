import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import sys
import os
import warnings
warnings.filterwarnings('ignore')

# إضافة المسار
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استيراد الملفات مع معالجة الأخطاء
try:
    from src.data_fetcher import DataFetcher
except Exception as e:
    st.error(f"❌ خطأ في استيراد DataFetcher: {e}")
    DataFetcher = None

try:
    from src.technical_analysis import TechnicalAnalyzer
except Exception as e:
    st.error(f"❌ خطأ في استيراد TechnicalAnalyzer: {e}")
    TechnicalAnalyzer = None

try:
    from src.sentiment_analyzer import SentimentAnalyzer
except Exception as e:
    st.error(f"❌ خطأ في استيراد SentimentAnalyzer: {e}")
    SentimentAnalyzer = None

try:
    from src.prediction_model import PredictionModel
except Exception as e:
    st.error(f"❌ خطأ في استيراد PredictionModel: {e}")
    PredictionModel = None

try:
    from src.signal_engine import SignalEngine
except Exception as e:
    st.error(f"❌ خطأ في استيراد SignalEngine: {e}")
    SignalEngine = None

try:
    from src.alert_system import AlertSystem
except Exception as e:
    st.error(f"❌ خطأ في استيراد AlertSystem: {e}")
    AlertSystem = None

try:
    from src.portfolio_manager import PortfolioManager
except Exception as e:
    st.error(f"❌ خطأ في استيراد PortfolioManager: {e}")
    PortfolioManager = None

try:
    from src.config import Config
except Exception as e:
    st.error(f"❌ خطأ في استيراد Config: {e}")
    Config = None

# إعدادات الصفحة
st.set_page_config(
    page_title="AI Stock Trading Platform",
    page_icon="📈",
    layout="wide"
)

# تهيئة الحالة
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META']
    st.session_state.data = None
    st.session_state.symbol = 'AAPL'
    st.session_state.period = '1y'
    st.session_state.data_fetcher = DataFetcher() if DataFetcher else None
    st.session_state.signal_engine = SignalEngine() if SignalEngine else None
    st.session_state.alert_system = AlertSystem() if AlertSystem else None
    st.session_state.portfolio = PortfolioManager(10000) if PortfolioManager else None

# العنوان
st.title("📈 AI Stock Trading Platform")
st.markdown("---")

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # اختيار السهم
    symbol = st.selectbox(
        "اختر السهم",
        st.session_state.symbols,
        index=0
    )
    
    # فترة البيانات
    period = st.selectbox(
        "الفترة الزمنية",
        ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3
    )
    
    # زر التحديث
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        with st.spinner('جاري تحميل البيانات...'):
            if st.session_state.data_fetcher:
                try:
                    st.session_state.data = st.session_state.data_fetcher.fetch_stock_data(symbol, period)
                    st.session_state.symbol = symbol
                    st.session_state.period = period
                    st.success("✅ تم تحديث البيانات")
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")
            else:
                st.error("❌ DataFetcher غير متاح")
    
    st.markdown("---")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

# جلب البيانات
if st.session_state.data is None or st.session_state.symbol != symbol or st.session_state.period != period:
    with st.spinner(f'جاري تحميل بيانات {symbol}...'):
        if st.session_state.data_fetcher:
            try:
                st.session_state.data = st.session_state.data_fetcher.fetch_stock_data(symbol, period)
                st.session_state.symbol = symbol
                st.session_state.period = period
            except Exception as e:
                st.error(f"❌ خطأ في تحميل البيانات: {e}")
                st.session_state.data = None
        else:
            st.error("❌ DataFetcher غير متاح")
            st.session_state.data = None

data = st.session_state.data

if data is not None and not data.empty:
    try:
        # تبويبات رئيسية
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 السعر والمؤشرات",
            "📈 التحليل الفني",
            "🧠 تحليل المشاعر والتنبؤ",
            "💼 إدارة المحفظة"
        ])
        
        with tab1:
            st.header("📊 السعر والمؤشرات")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # الرسم البياني للسعر
                fig = go.Figure()
                
                # سعر الإغلاق
                fig.add_trace(go.Scatter(
                    x=data['Date'],
                    y=data['Close'],
                    name='Close',
                    line=dict(color='blue', width=2)
                ))
                
                # المتوسطات المتحركة
                if 'SMA_20' in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data['Date'],
                        y=data['SMA_20'],
                        name='SMA 20',
                        line=dict(color='orange', width=1, dash='dash')
                    ))
                
                if 'SMA_50' in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data['Date'],
                        y=data['SMA_50'],
                        name='SMA 50',
                        line=dict(color='green', width=1, dash='dash')
                    ))
                
                fig.update_layout(
                    title=f'{symbol} - السعر',
                    height=400,
                    xaxis_title='التاريخ',
                    yaxis_title='السعر ($)',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # معلومات السعر
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
                change = current_price - prev_price
                change_pct = (change / prev_price * 100) if prev_price != 0 else 0
                
                st.metric(
                    "السعر الحالي",
                    f"${current_price:.2f}",
                    f"{change_pct:+.2f}%"
                )
                
                st.markdown("### 📊 معلومات إضافية")
                st.markdown(f"""
                **High:** ${data['High'].iloc[-1]:.2f}  
                **Low:** ${data['Low'].iloc[-1]:.2f}  
                **Open:** ${data['Open'].iloc[-1]:.2f}  
                **Volume:** {data['Volume'].iloc[-1]:,.0f}
                """)
        
        with tab2:
            st.header("📈 التحليل الفني")
            
            if TechnicalAnalyzer:
                try:
                    ta = TechnicalAnalyzer(data)
                    
                    # RSI
                    st.subheader("مؤشر القوة النسبية (RSI)")
                    rsi = ta.calculate_rsi()
                    
                    if rsi is not None and not rsi.empty:
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(
                            x=data['Date'],
                            y=rsi,
                            name='RSI',
                            line=dict(color='purple', width=2)
                        ))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                        fig_rsi.update_layout(height=300)
                        st.plotly_chart(fig_rsi, use_container_width=True)
                        
                        current_rsi = rsi.iloc[-1]
                        st.info(f"RSI الحالي: {current_rsi:.2f}")
                    
                    # MACD
                    st.subheader("مؤشر MACD")
                    macd_data = ta.calculate_macd()
                    
                    if macd_data:
                        fig_macd = go.Figure()
                        fig_macd.add_trace(go.Scatter(
                            x=data['Date'],
                            y=macd_data['MACD'],
                            name='MACD',
                            line=dict(color='blue')
                        ))
                        fig_macd.add_trace(go.Scatter(
                            x=data['Date'],
                            y=macd_data['MACD_Signal'],
                            name='Signal',
                            line=dict(color='red')
                        ))
                        fig_macd.update_layout(height=300)
                        st.plotly_chart(fig_macd, use_container_width=True)
                    
                    # Bollinger Bands
                    st.subheader("Bollinger Bands")
                    bb = ta.calculate_bollinger_bands()
                    
                    if bb:
                        fig_bb = go.Figure()
                        fig_bb.add_trace(go.Scatter(
                            x=data['Date'],
                            y=data['Close'],
                            name='Price',
                            line=dict(color='blue')
                        ))
                        fig_bb.add_trace(go.Scatter(
                            x=data['Date'],
                            y=bb['BB_High'],
                            name='Upper Band',
                            line=dict(color='red', dash='dash')
                        ))
                        fig_bb.add_trace(go.Scatter(
                            x=data['Date'],
                            y=bb['BB_Mid'],
                            name='Middle Band',
                            line=dict(color='gray', dash='dash')
                        ))
                        fig_bb.add_trace(go.Scatter(
                            x=data['Date'],
                            y=bb['BB_Low'],
                            name='Lower Band',
                            line=dict(color='green', dash='dash')
                        ))
                        fig_bb.update_layout(height=300)
                        st.plotly_chart(fig_bb, use_container_width=True)
                    
                    # ملخص الإشارات
                    st.subheader("📋 ملخص الإشارات الفنية")
                    signals = ta.get_technical_signals()
                    
                    if signals:
                        cols = st.columns(len(signals))
                        for col, (indicator, signal) in zip(cols, signals.items()):
                            color = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "🟡"
                            with col:
                                st.metric(indicator, f"{color} {signal}")
                
                except Exception as e:
                    st.error(f"❌ خطأ في التحليل الفني: {e}")
            else:
                st.warning("⚠️ TechnicalAnalyzer غير متاح")
        
        with tab3:
            st.header("🧠 تحليل المشاعر والتنبؤ")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📰 تحليل المشاعر")
                
                if SentimentAnalyzer:
                    if st.button("🔄 تحليل المشاعر"):
                        with st.spinner('جاري تحليل المشاعر...'):
                            try:
                                sa = SentimentAnalyzer()
                                sentiment = sa.get_news_sentiment(symbol)
                                
                                if sentiment:
                                    st.metric("المشاعر العامة", sentiment['sentiment'])
                                    st.metric("النتيجة", f"{sentiment['score']:.2f}")
                                    st.metric("المصادر", sentiment.get('sources', 0))
                                else:
                                    st.info("لا توجد بيانات مشاعر متاحة")
                            except Exception as e:
                                st.error(f"❌ خطأ: {e}")
                else:
                    st.warning("⚠️ SentimentAnalyzer غير متاح")
            
            with col2:
                st.subheader("🔮 التنبؤ بالأسعار")
                
                if PredictionModel:
                    if st.button("📈 تنبؤ"):
                        with st.spinner('جاري التنبؤ...'):
                            try:
                                pm = PredictionModel(symbol)
                                predictions = pm.simple_prediction(data, days=10)
                                
                                if predictions is not None:
                                    dates = pd.date_range(start=data['Date'].iloc[-1], periods=11, freq='D')[1:]
                                    
                                    fig_pred = go.Figure()
                                    fig_pred.add_trace(go.Scatter(
                                        x=data['Date'].iloc[-30:],
                                        y=data['Close'].iloc[-30:],
                                        name='Historical',
                                        line=dict(color='blue')
                                    ))
                                    fig_pred.add_trace(go.Scatter(
                                        x=dates,
                                        y=predictions,
                                        name='Prediction',
                                        line=dict(color='red', dash='dash')
                                    ))
                                    
                                    fig_pred.update_layout(
                                        title='تنبؤ السعر للأيام القادمة',
                                        height=400
                                    )
                                    st.plotly_chart(fig_pred, use_container_width=True)
                                    
                                    # عرض التنبؤات
                                    pred_df = pd.DataFrame({
                                        'التاريخ': dates,
                                        'السعر المتوقع': predictions
                                    })
                                    st.dataframe(pred_df, use_container_width=True)
                                else:
                                    st.warning("⚠️ لم يتمكن النموذج من عمل التنبؤ")
                            except Exception as e:
                                st.error(f"❌ خطأ: {e}")
                else:
                    st.warning("⚠️ PredictionModel غير متاح")
        
        with tab4:
            st.header("💼 إدارة المحفظة")
            
            if st.session_state.portfolio:
                try:
                    # حالة المحفظة
                    st.subheader("📊 حالة المحفظة")
                    
                    current_prices = {}
                    for sym in list(st.session_state.portfolio.positions.keys()):
                        if st.session_state.data_fetcher:
                            price = st.session_state.data_fetcher.get_current_price(sym)
                            if price:
                                current_prices[sym] = price
                    
                    status = st.session_state.portfolio.get_portfolio_status(current_prices)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("القيمة الإجمالية", f"${status['total_value']:.2f}")
                    with col2:
                        gain_loss = status.get('gain_loss', 0)
                        st.metric("الربح/الخسارة", f"${gain_loss:+.2f}")
                    with col3:
                        st.metric("النقدية", f"${status['cash']:.2f}")
                    
                    # المراكز المفتوحة
                    if status['positions']:
                        st.subheader("📈 المراكز المفتوحة")
                        positions_df = pd.DataFrame(status['positions']).T
                        st.dataframe(positions_df, use_container_width=True)
                    
                    # إضافة مركز جديد
                    st.subheader("➕ إضافة مركز جديد")
                    
                    add_symbol = st.selectbox(
                        "السهم",
                        st.session_state.symbols,
                        key="add_symbol"
                    )
                    
                    quantity = st.number_input(
                        "الكمية",
                        min_value=1,
                        step=1,
                        value=10
                    )
                    
                    if st.session_state.data_fetcher:
                        current_price = st.session_state.data_fetcher.get_current_price(add_symbol)
                        if current_price:
                            total_cost = quantity * current_price
                            st.info(f"السعر الحالي: ${current_price:.2f}")
                            st.warning(f"التكلفة الإجمالية: ${total_cost:.2f}")
                            
                            if st.button("🟢 شراء"):
                                if total_cost <= st.session_state.portfolio.cash:
                                    st.session_state.portfolio.add_position(add_symbol, quantity, current_price)
                                    st.success(f"✅ تم شراء {quantity} سهم من {add_symbol}")
                                    st.rerun()
                                else:
                                    st.error("❌ رصيد غير كافٍ")
                    
                    # تاريخ العمليات
                    if st.session_state.portfolio.history:
                        st.subheader("📜 تاريخ العمليات")
                        history_df = pd.DataFrame(st.session_state.portfolio.history)
                        st.dataframe(history_df, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"❌ خطأ في إدارة المحفظة: {e}")
            else:
                st.warning("⚠️ PortfolioManager غير متاح")
    
    except Exception as e:
        st.error(f"❌ خطأ عام في التطبيق: {e}")
        st.info("💡 حاول تحديث الصفحة أو إعادة التشغيل")

else:
    st.warning("⚠️ لا توجد بيانات متاحة")
    st.info("💡 اضغط على زر 'تحديث البيانات' في الشريط الجانبي")

# Footer
st.markdown("---")
st.caption("🚀 تم التطوير باستخدام Streamlit | بيانات من Yahoo Finance | لأغراض تعليمية فقط")
