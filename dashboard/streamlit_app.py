"""
لوحة تحكم إضافية متقدمة لمنصة التداول
Dashboard - Streamlit Advanced Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import sys
import os

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalyzer
from src.sentiment_analyzer import SentimentAnalyzer
from src.prediction_model import PredictionModel
from src.signal_engine import SignalEngine
from src.alert_system import AlertSystem
from src.portfolio_manager import PortfolioManager
from src.config import Config

# إعدادات الصفحة
st.set_page_config(
    page_title="📊 Trading Dashboard Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00ff87 0%, #60efff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .signal-buy {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .signal-sell {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        padding: 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .signal-hold {
        background: linear-gradient(135deg, #f6d365, #fda085);
        padding: 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        text-align: center;
    }
    .sidebar-content {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# تهيئة الجلسة
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data_fetcher = DataFetcher()
    st.session_state.signal_engine = SignalEngine()
    st.session_state.alert_system = AlertSystem()
    st.session_state.portfolio = PortfolioManager(Config.INITIAL_CAPITAL)
    st.session_state.watchlist = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META']
    st.session_state.last_update = None
    st.session_state.historical_data = {}
    st.session_state.auto_refresh = False

# وظائف مساعدة
def format_currency(value):
    """تنسيق العملة"""
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"

def get_stock_info(symbol):
    """جلب معلومات السهم"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except:
        return {}

def calculate_performance_metrics(data):
    """حساب مقاييس الأداء"""
    if data is None or len(data) < 2:
        return {}
    
    returns = data['Close'].pct_change().dropna()
    
    metrics = {
        'total_return': ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100,
        'daily_return': returns.iloc[-1] * 100 if len(returns) > 0 else 0,
        'volatility': returns.std() * np.sqrt(252) * 100,
        'max_drawdown': ((data['Close'].cummax() - data['Close']) / data['Close'].cummax()).max() * 100,
        'sharpe_ratio': (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0,
        'volume_avg': data['Volume'].mean(),
        'volume_last': data['Volume'].iloc[-1]
    }
    
    return metrics

# الشريط الجانبي
with st.sidebar:
    st.markdown("### 📊 Dashboard Pro")
    st.markdown("---")
    
    # اختيار الأسهم
    st.markdown("#### 🔍 إدارة الأسهم")
    
    # إضافة سهم جديد
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input("إضافة سهم", placeholder="مثال: AAPL", key="add_symbol")
    with col2:
        if st.button("➕", use_container_width=True):
            if new_symbol and new_symbol.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_symbol.upper())
                st.rerun()
    
    # قائمة الأسهم
    st.markdown("#### 📋 قائمة المتابعة")
    
    # حذف الأسهم
    for symbol in st.session_state.watchlist:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"• {symbol}")
        with col2:
            if st.button("✖", key=f"del_{symbol}"):
                if len(st.session_state.watchlist) > 1:
                    st.session_state.watchlist.remove(symbol)
                    st.rerun()
                else:
                    st.warning("لا يمكن حذف السهم الأخير")
    
    # اختيار السهم للتحليل
    selected_symbol = st.selectbox(
        "📌 السهم المحدد",
        st.session_state.watchlist,
        index=0
    )
    
    st.markdown("---")
    
    # الإعدادات
    st.markdown("#### ⚙️ الإعدادات")
    
    period = st.selectbox(
        "الفترة الزمنية",
        ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'],
        index=5
    )
    
    interval = st.selectbox(
        "الفاصل الزمني",
        ['1m', '5m', '15m', '30m', '1h', '1d', '5d', '1wk', '1mo'],
        index=5
    )
    
    st.session_state.auto_refresh = st.checkbox("تحديث تلقائي", value=False)
    
    if st.session_state.auto_refresh:
        refresh_interval = st.slider("فترة التحديث (ثانية)", 5, 60, 30)
        
        # تحديث تلقائي
        if st.session_state.last_update is None or \
           (datetime.now() - st.session_state.last_update).seconds > refresh_interval:
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    if st.button("🔄 تحديث يدوي", use_container_width=True):
        st.session_state.last_update = datetime.now()
        st.rerun()
    
    st.markdown("---")
    
    # معلومات النظام
    st.markdown("#### ℹ️ معلومات")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
    st.caption(f"الأسهم: {len(st.session_state.watchlist)}")
    st.caption(f"الإصدار: v2.0.0")

# المحتوى الرئيسي
st.markdown('<div class="main-header">📊 منصة التداول المتقدمة</div>', unsafe_allow_html=True)

# جلب البيانات للسهم المحدد
@st.cache_data(ttl=300)
def load_stock_data(symbol, period, interval):
    """تحميل بيانات السهم مع التخزين المؤقت"""
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data(symbol, period, interval)
    return data

# جلب البيانات لجميع الأسهم
def load_all_stocks_data():
    """جلب بيانات جميع الأسهم في قائمة المتابعة"""
    data = {}
    for symbol in st.session_state.watchlist:
        df = load_stock_data(symbol, period, interval)
        if df is not None and not df.empty:
            data[symbol] = df
    return data

# تحميل البيانات
with st.spinner(f'جاري تحميل بيانات {selected_symbol}...'):
    stock_data = load_stock_data(selected_symbol, period, interval)
    all_data = load_all_stocks_data()

if stock_data is not None and not stock_data.empty:
    
    # بطاقات المعلومات السريعة
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # السعر الحالي والتغير
    current_price = stock_data['Close'].iloc[-1]
    prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price * 100) if prev_price != 0 else 0
    
    # معلومات إضافية
    stock_info = get_stock_info(selected_symbol)
    market_cap = stock_info.get('marketCap', 0)
    pe_ratio = stock_info.get('trailingPE', 'N/A')
    dividend_yield = stock_info.get('dividendYield', 0)
    if dividend_yield:
        dividend_yield = dividend_yield * 100
    
    # حساب المقاييس
    metrics = calculate_performance_metrics(stock_data)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.8rem; opacity:0.8;">السعر الحالي</div>
            <div style="font-size:1.8rem; font-weight:bold;">${current_price:.2f}</div>
            <div style="color: {'green' if price_change >= 0 else 'red'};">
                {price_change:+.2f} ({price_change_pct:+.2f}%)
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb, #f5576c);">
            <div style="font-size:0.8rem; opacity:0.8;">القيمة السوقية</div>
            <div style="font-size:1.8rem; font-weight:bold;">{format_currency(market_cap)}</div>
            <div style="font-size:0.8rem;">نسبة PE: {pe_ratio}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe, #00f2fe);">
            <div style="font-size:0.8rem; opacity:0.8;">الحجم</div>
            <div style="font-size:1.3rem; font-weight:bold;">{metrics.get('volume_last', 0):,.0f}</div>
            <div style="font-size:0.8rem;">المتوسط: {metrics.get('volume_avg', 0):,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b, #38f9d7);">
            <div style="font-size:0.8rem; opacity:0.8;">العائد الكلي</div>
            <div style="font-size:1.8rem; font-weight:bold; color: {'green' if metrics.get('total_return', 0) >= 0 else 'red'};">
                {metrics.get('total_return', 0):+.2f}%
            </div>
            <div style="font-size:0.8rem;">التذبذب: {metrics.get('volatility', 0):.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #fa709a, #fee140);">
            <div style="font-size:0.8rem; opacity:0.8;">نسبة Sharpe</div>
            <div style="font-size:1.8rem; font-weight:bold;">{metrics.get('sharpe_ratio', 0):.2f}</div>
            <div style="font-size:0.8rem;">الحد الأقصى للانخفاض: {metrics.get('max_drawdown', 0):.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# التبويبات الرئيسية
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 الرسم البياني المتقدم",
    "📊 التحليل الفني",
    "🧠 الذكاء الاصطناعي",
    "💼 المحفظة",
    "📰 الأخبار والمشاعر",
    "📊 المقارنة"
])

# Tab 1: الرسم البياني المتقدم
with tab1:
    st.subheader("📈 الرسم البياني المتقدم")
    
    # اختيار نوع الرسم البياني
    chart_type = st.radio(
        "نوع الرسم البياني",
        ['Candlestick', 'Line', 'OHLC', 'Area'],
        horizontal=True
    )
    
    # اختيار المؤشرات
    indicators = st.multiselect(
        "المؤشرات الفنية",
        ['SMA 20', 'SMA 50', 'EMA 12', 'EMA 26', 'Bollinger Bands', 'Volume'],
        default=['SMA 20', 'SMA 50']
    )
    
    # إنشاء الرسم البياني
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{selected_symbol} - السعر', 'حجم التداول')
    )
    
    # بيانات السعر
    if chart_type == 'Candlestick':
        fig.add_trace(
            go.Candlestick(
                x=stock_data['Date'],
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name='Candlestick'
            ),
            row=1, col=1
        )
    elif chart_type == 'OHLC':
        fig.add_trace(
            go.Ohlc(
                x=stock_data['Date'],
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name='OHLC'
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=stock_data['Date'],
                y=stock_data['Close'],
                name='Close',
                line=dict(color='blue', width=2),
                fill='tonexty' if chart_type == 'Area' else None
            ),
            row=1, col=1
        )
    
    # إضافة المؤشرات
    for indicator in indicators:
        if indicator == 'SMA 20':
            sma20 = stock_data['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=sma20,
                    name='SMA 20',
                    line=dict(color='orange', width=1.5)
                ),
                row=1, col=1
            )
        elif indicator == 'SMA 50':
            sma50 = stock_data['Close'].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=sma50,
                    name='SMA 50',
                    line=dict(color='green', width=1.5)
                ),
                row=1, col=1
            )
        elif indicator == 'EMA 12':
            ema12 = stock_data['Close'].ewm(span=12, adjust=False).mean()
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=ema12,
                    name='EMA 12',
                    line=dict(color='red', width=1.5)
                ),
                row=1, col=1
            )
        elif indicator == 'EMA 26':
            ema26 = stock_data['Close'].ewm(span=26, adjust=False).mean()
            fig.add_trace(
                go.Scatter(
                    x=stock_data['Date'],
                    y=ema26,
                    name='EMA 26',
                    line=dict(color='purple', width=1.5)
                ),
                row=1, col=1
            )
        elif indicator == 'Bollinger Bands':
            bb = TechnicalAnalyzer(stock_data).calculate_bollinger_bands()
            if 'BB_High' in bb and 'BB_Low' in bb:
                fig.add_trace(
                    go.Scatter(
                        x=stock_data['Date'],
                        y=bb['BB_High'],
                        name='BB Upper',
                        line=dict(color='rgba(255,0,0,0.5)', dash='dash')
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=stock_data['Date'],
                        y=bb['BB_Mid'],
                        name='BB Middle',
                        line=dict(color='rgba(128,128,128,0.5)', dash='dash')
                    ),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=stock_data['Date'],
                        y=bb['BB_Low'],
                        name='BB Lower',
                        line=dict(color='rgba(0,255,0,0.5)', dash='dash')
                    ),
                    row=1, col=1
                )
    
    # حجم التداول
    colors = ['green' if close >= open else 'red' 
              for close, open in zip(stock_data['Close'], stock_data['Open'])]
    fig.add_trace(
        go.Bar(
            x=stock_data['Date'],
            y=stock_data['Volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.5
        ),
        row=2, col=1
    )
    
    # تحديث التخطيط
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_yaxes(title_text="السعر ($)", row=1, col=1)
    fig.update_yaxes(title_text="الحجم", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # إحصائيات إضافية
    with st.expander("📊 إحصائيات إضافية"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("أعلى سعر", f"${stock_data['High'].max():.2f}")
            st.metric("أقل سعر", f"${stock_data['Low'].min():.2f}")
        with col2:
            st.metric("متوسط السعر", f"${stock_data['Close'].mean():.2f}")
            st.metric("الانحراف المعياري", f"${stock_data['Close'].std():.2f}")
        with col3:
            st.metric("أعلى حجم", f"{stock_data['Volume'].max():,.0f}")
            st.metric("أقل حجم", f"{stock_data['Volume'].min():,.0f}")
        with col4:
            st.metric("متوسط الحجم", f"{stock_data['Volume'].mean():,.0f}")
            st.metric("عدد الأيام", f"{len(stock_data)}")

# Tab 2: التحليل الفني
with tab2:
    st.subheader("📊 التحليل الفني المتقدم")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # RSI
        st.markdown("#### 📈 مؤشر القوة النسبية (RSI)")
        ta = TechnicalAnalyzer(stock_data)
        rsi = ta.calculate_rsi()
        
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=stock_data['Date'],
            y=rsi,
            name='RSI',
            line=dict(color='purple', width=2)
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", 
                         annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green",
                         annotation_text="Oversold")
        fig_rsi.update_layout(height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
        
        # قيمة RSI الحالية
        current_rsi = rsi.iloc[-1] if not rsi.empty else 50
        rsi_status = "محايد"
        if current_rsi > 70:
            rsi_status = "منطقة شراء (Overbought) 🔴"
        elif current_rsi < 30:
            rsi_status = "منطقة بيع (Oversold) 🟢"
        
        st.info(f"RSI الحالي: {current_rsi:.2f} - {rsi_status}")
    
    with col2:
        # MACD
        st.markdown("#### 📈 مؤشر MACD")
        macd_data = ta.calculate_macd()
        
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(
            x=stock_data['Date'],
            y=macd_data['MACD'],
            name='MACD',
            line=dict(color='blue')
        ))
        fig_macd.add_trace(go.Scatter(
            x=stock_data['Date'],
            y=macd_data['MACD_Signal'],
            name='Signal',
            line=dict(color='red')
        ))
        
        # Histogram
        macd_diff = macd_data['MACD_Diff']
        colors = ['green' if x > 0 else 'red' for x in macd_diff]
        fig_macd.add_trace(go.Bar(
            x=stock_data['Date'],
            y=macd_diff,
            name='Histogram',
            marker_color=colors
        ))
        
        fig_macd.update_layout(height=300)
        st.plotly_chart(fig_macd, use_container_width=True)
        
        # إشارة MACD
        if not macd_data['MACD'].empty and not macd_data['MACD_Signal'].empty:
            if macd_data['MACD'].iloc[-1] > macd_data['MACD_Signal'].iloc[-1]:
                st.success("✅ إشارة شراء (MACD فوق خط الإشارة)")
            else:
                st.warning("⚠️ إشارة بيع (MACD تحت خط الإشارة)")
    
    # Bollinger Bands
    st.markdown("#### 📊 Bollinger Bands")
    bb = ta.calculate_bollinger_bands()
    
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(
        x=stock_data['Date'],
        y=stock_data['Close'],
        name='Price',
        line=dict(color='blue')
    ))
    fig_bb.add_trace(go.Scatter(
        x=stock_data['Date'],
        y=bb['BB_High'],
        name='Upper Band',
        line=dict(color='red', dash='dash')
    ))
    fig_bb.add_trace(go.Scatter(
        x=stock_data['Date'],
        y=bb['BB_Mid'],
        name='Middle Band',
        line=dict(color='gray', dash='dash')
    ))
    fig_bb.add_trace(go.Scatter(
        x=stock_data['Date'],
        y=bb['BB_Low'],
        name='Lower Band',
        line=dict(color='green', dash='dash')
    ))
    fig_bb.update_layout(height=400)
    st.plotly_chart(fig_bb, use_container_width=True)
    
    # ملخص المؤشرات
    st.markdown("#### 📋 ملخص المؤشرات الفنية")
    signals = ta.get_technical_signals()
    
    cols = st.columns(len(signals))
    for col, (indicator, signal) in zip(cols, signals.items()):
        color = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "🟡"
        with col:
            st.metric(indicator, f"{color} {signal}")

# Tab 3: الذكاء الاصطناعي
with tab3:
    st.subheader("🧠 الذكاء الاصطناعي والتنبؤ")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔮 تنبؤ LSTM")
        
        if st.button("🤖 تشغيل نموذج LSTM", use_container_width=True):
            with st.spinner('جاري تدريب النموذج والتنبؤ...'):
                pm = PredictionModel(selected_symbol)
                
                # تدريب النموذج
                progress_bar = st.progress(0)
                st.text("جاري تدريب النموذج...")
                
                pm.train_lstm(stock_data, epochs=20)
                progress_bar.progress(50)
                
                # التنبؤ
                st.text("جاري التنبؤ...")
                predictions = pm.predict_lstm(stock_data, days=10)
                progress_bar.progress(100)
                
                if predictions is not None:
                    # عرض النتائج
                    dates = pd.date_range(
                        start=stock_data['Date'].iloc[-1], 
                        periods=11, 
                        freq='D'
                    )[1:]
                    
                    # رسم التنبؤات
                    fig_pred = go.Figure()
                    fig_pred.add_trace(go.Scatter(
                        x=stock_data['Date'].iloc[-30:],
                        y=stock_data['Close'].iloc[-30:],
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
                    
                    # عرض التنبؤات كجدول
                    pred_df = pd.DataFrame({
                        'التاريخ': dates,
                        'السعر المتوقع': predictions,
                        'التغير المتوقع': [0] + [predictions[i] - predictions[i-1] 
                                                for i in range(1, len(predictions))]
                    })
                    pred_df['التغير المتوقع %'] = (pred_df['التغير المتوقع'] / 
                                                   pred_df['السعر المتوقع'].shift(1) * 100)
                    st.dataframe(pred_df, use_container_width=True)
                    
                    # التوصية
                    future_trend = predictions[-1] - predictions[0]
                    if future_trend > 0:
                        st.success(f"📈 اتجاه صاعد متوقع: +{future_trend:.2f}")
                    else:
                        st.warning(f"📉 اتجاه هابط متوقع: {future_trend:.2f}")
                else:
                    st.error("❌ فشل في التنبؤ")
    
    with col2:
        st.markdown("#### 📈 تنبؤ Prophet")
        
        if st.button("📊 تشغيل نموذج Prophet", use_container_width=True):
            with st.spinner('جاري تحليل البيانات...'):
                pm = PredictionModel(selected_symbol)
                forecast = pm.prophet_predict(stock_data, days=10)
                
                if forecast is not None:
                    fig_prophet = go.Figure()
                    fig_prophet.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast['yhat'],
                        name='Prediction',
                        line=dict(color='green', width=2)
                    ))
                    fig_prophet.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast['yhat_upper'],
                        name='Upper Bound',
                        line=dict(color='lightgreen', dash='dash')
                    ))
                    fig_prophet.add_trace(go.Scatter(
                        x=forecast['ds'],
                        y=forecast['yhat_lower'],
                        name='Lower Bound',
                        line=dict(color='lightgreen', dash='dash'),
                        fill='tonexty'
                    ))
                    
                    fig_prophet.update_layout(
                        title='تنبؤ Prophet',
                        height=400
                    )
                    st.plotly_chart(fig_prophet, use_container_width=True)
                    
                    # عرض التنبؤات
                    st.dataframe(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], 
                                use_container_width=True)
    
    # إشارة التداول
    st.markdown("---")
    st.markdown("#### 🎯 إشارة التداول المتكاملة")
    
    if st.button("🔄 توليد إشارة", use_container_width=True):
        with st.spinner('جاري التحليل...'):
            signal = st.session_state.signal_engine.generate_signal(stock_data, selected_symbol)
            
            if signal:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if signal['signal'] == 'BUY':
                        st.markdown("""
                        <div class="signal-buy">
                            🟢 شراء<br>
                            <span style="font-size:0.8rem;">BUY</span>
                        </div>
                        """, unsafe_allow_html=True)
                    elif signal['signal'] == 'SELL':
                        st.markdown("""
                        <div class="signal-sell">
                            🔴 بيع<br>
                            <span style="font-size:0.8rem;">SELL</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="signal-hold">
                            🟡 انتظار<br>
                            <span style="font-size:0.8rem;">HOLD</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("الثقة", f"{signal['confidence']:.1f}%")
                
                with col3:
                    st.metric("النتيجة النهائية", f"{signal['score']:.2f}")
                
                with col4:
                    st.metric("المخاطرة", "متوسطة")
                
                # التفاصيل
                st.markdown("##### 📊 تفاصيل التحليل")
                details_df = pd.DataFrame([{
                    'العامل': factor,
                    'النتيجة': f"{score:.2f}",
                    'التقييم': '🟢 قوي' if score > 0.2 else '🟡 محايد' if score > -0.2 else '🔴 ضعيف'
                } for factor, score in signal['details'].items()])
                st.dataframe(details_df, use_container_width=True)

# Tab 4: المحفظة
with tab4:
    st.subheader("💼 إدارة المحفظة")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # ملخص المحفظة
        st.markdown("#### 📊 ملخص المحفظة")
        
        # جلب الأسعار الحالية لجميع الأسهم في المحفظة
        portfolio_symbols = list(st.session_state.portfolio.positions.keys())
        current_prices = {}
        for sym in portfolio_symbols:
            price = st.session_state.data_fetcher.get_current_price(sym)
            if price:
                current_prices[sym] = price
        
        status = st.session_state.portfolio.get_portfolio_status(current_prices)
        
        # عرض المقاييس الرئيسية
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("القيمة الإجمالية", f"${status['total_value']:,.2f}")
        with m2:
            gain_loss = status.get('gain_loss', 0)
            st.metric("الربح/الخسارة", 
                     f"${gain_loss:+,.2f}",
                     f"{status.get('gain_loss_pct', 0):+.2f}%")
        with m3:
            st.metric("النقدية", f"${status['cash']:,.2f}")
        with m4:
            st.metric("عدد المراكز", len(status['positions']))
        
        # تفاصيل المراكز
        if status['positions']:
            st.markdown("#### 📈 المراكز المفتوحة")
            positions_df = pd.DataFrame(status['positions']).T
            positions_df.index.name = 'السهم'
            st.dataframe(positions_df, use_container_width=True)
            
            # رسم توزيع المحفظة
            st.markdown("#### 🎯 توزيع المحفظة")
            fig_pie = px.pie(
                values=[p['value'] for p in status['positions'].values()],
                names=list(status['positions'].keys()),
                title='توزيع الاستثمارات'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("#### ➕ إضافة مركز جديد")
        
        # اختيار السهم
        add_symbol = st.selectbox(
            "السهم",
            st.session_state.watchlist,
            key="portfolio_add"
        )
        
        # كمية الشراء
        quantity = st.number_input(
            "الكمية",
            min_value=1,
            step=1,
            value=10
        )
        
        # السعر الحالي
        current_price = st.session_state.data_fetcher.get_current_price(add_symbol)
        if current_price:
            total_cost = quantity * current_price
            st.info(f"السعر الحالي: ${current_price:.2f}")
            st.warning(f"التكلفة الإجمالية: ${total_cost:,.2f}")
            
            if st.button("🟢 شراء", use_container_width=True):
                if total_cost <= st.session_state.portfolio.cash:
                    st.session_state.portfolio.add_position(add_symbol, quantity, current_price)
                    st.success(f"✅ تم شراء {quantity} سهم من {add_symbol}")
                    st.rerun()
                else:
                    st.error("❌ رصيد غير كافٍ")
        
        # بيع مركز
        st.markdown("#### 🔴 بيع مركز")
        
        if st.session_state.portfolio.positions:
            sell_symbol = st.selectbox(
                "اختر السهم للبيع",
                list(st.session_state.portfolio.positions.keys()),
                key="portfolio_sell"
            )
            
            max_quantity = st.session_state.portfolio.positions[sell_symbol]['quantity']
            sell_quantity = st.number_input(
                "الكمية للبيع",
                min_value=1,
                max_value=max_quantity,
                step=1,
                key="sell_qty"
            )
            
            current_price = st.session_state.data_fetcher.get_current_price(sell_symbol)
            if current_price and st.button("🔴 بيع", use_container_width=True):
                success = st.session_state.portfolio.remove_position(
                    sell_symbol,
                    sell_quantity,
                    current_price
                )
                if success:
                    st.success(f"✅ تم بيع {sell_quantity} سهم من {sell_symbol}")
                    st.rerun()
                else:
                    st.error("❌ حدث خطأ في عملية البيع")
    
    # تاريخ العمليات
    st.markdown("---")
    st.markdown("#### 📜 تاريخ العمليات")
    
    if st.session_state.portfolio.history:
        history_df = pd.DataFrame(st.session_state.portfolio.history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df = history_df.sort_values('timestamp', ascending=False)
        st.dataframe(history_df, use_container_width=True)

# Tab 5: الأخبار والمشاعر
with tab5:
    st.subheader("📰 الأخبار وتحليل المشاعر")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 تحليل المشاعر")
        
        if st.button("🔄 تحليل المشاعر", use_container_width=True):
            with st.spinner('جاري تحليل المشاعر...'):
                sentiment_analyzer = SentimentAnalyzer()
                sentiment = sentiment_analyzer.get_news_sentiment(selected_symbol)
                
                if sentiment:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("المشاعر العامة", sentiment['sentiment'])
                    with col_b:
                        st.metric("النتيجة", f"{sentiment['score']:.3f}")
                    with col_c:
                        st.metric("المصادر", sentiment.get('sources', 0))
                    
                    # عرض المشاعر بشكل بياني
                    fig_sent = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = sentiment['score'] * 100,
                        title = {'text': "مؤشر المشاعر"},
                        delta = {'reference': 0},
                        gauge = {
                            'axis': {'range': [-100, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [-100, -30], 'color': "red"},
                                {'range': [-30, 30], 'color': "yellow"},
                                {'range': [30, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "black", 'width': 4},
                                'thickness': 0.75,
                                'value': sentiment['score'] * 100
                            }
                        }
                    ))
                    fig_sent.update_layout(height=300)
                    st.plotly_chart(fig_sent, use_container_width=True)
                else:
                    st.warning("لا توجد بيانات مشاعر متاحة")
    
    with col2:
        st.markdown("#### 📰 آخر الأخبار")
        
        if st.button("📰 جلب الأخبار", use_container_width=True):
            with st.spinner('جاري جلب الأخبار...'):
                try:
                    ticker = yf.Ticker(selected_symbol)
                    news = ticker.news
                    
                    if news:
                        for i, item in enumerate(news[:5]):
                            with st.expander(f"📰 {item.get('title', 'خبر')[:50]}..."):
                                st.markdown(f"**العنوان:** {item.get('title', 'N/A')}")
                                st.markdown(f"**المصدر:** {item.get('publisher', 'N/A')}")
                                if 'link' in item:
                                    st.markdown(f"**الرابط:** [اضغط هنا]({item['link']})")
                                st.markdown(f"**التوقيت:** {datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.info("لا توجد أخبار حالية")
                except Exception as e:
                    st.error(f"خطأ في جلب الأخبار: {e}")

# Tab 6: المقارنة
with tab6:
    st.subheader("📊 مقارنة الأسهم")
    
    # اختيار الأسهم للمقارنة
    compare_symbols = st.multiselect(
        "اختر الأسهم للمقارنة",
        st.session_state.watchlist,
        default=st.session_state.watchlist[:3]
    )
    
    if compare_symbols:
        # جلب البيانات للمقارنة
        compare_data = {}
        for sym in compare_symbols:
            df = load_stock_data(sym, period, interval)
            if df is not None and not df.empty:
                compare_data[sym] = df
        
        if compare_data:
            # رسم المقارنة
            fig_compare = go.Figure()
            
            # تطبيع البيانات للمقارنة
            for sym, df in compare_data.items():
                normalized = (df['Close'] / df['Close'].iloc[0] - 1) * 100
                fig_compare.add_trace(go.Scatter(
                    x=df['Date'],
                    y=normalized,
                    name=sym,
                    line=dict(width=2)
                ))
            
            fig_compare.update_layout(
                title='مقارنة أداء الأسهم (%)',
                xaxis_title='التاريخ',
                yaxis_title='التغير المئوي (%)',
                height=500,
                hovermode='x unified'
            )
            st.plotly_chart(fig_compare, use_container_width=True)
            
            # جدول المقارنة
            st.markdown("#### 📋 جدول المقارنة")
            
            comparison_data = []
            for sym, df in compare_data.items():
                metrics = calculate_performance_metrics(df)
                comparison_data.append({
                    'السهم': sym,
                    'السعر الحالي': f"${df['Close'].iloc[-1]:.2f}",
                    'التغير %': f"{metrics.get('daily_return', 0):.2f}%",
                    'العائد الكلي %': f"{metrics.get('total_return', 0):.2f}%",
                    'التذبذب %': f"{metrics.get('volatility', 0):.2f}%",
                    'نسبة Sharpe': f"{metrics.get('sharpe_ratio', 0):.2f}"
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
        else:
            st.warning("لا توجد بيانات للمقارنة")

else:
    st.error(f"❌ فشل في تحميل بيانات {selected_symbol}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>🚀 Dashboard Pro v2.0 | Developed with ❤️</p>
    <p style="font-size: 0.8rem;">بيانات من Yahoo Finance | لأغراض تعليمية فقط</p>
</div>
""", unsafe_allow_html=True)
