import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================
# إعدادات الصفحة
# ============================================
st.set_page_config(
    page_title="AI Stock Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS مخصص
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #00ff87 0%, #60efff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .signal-buy {
        background: #00b09b;
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .signal-sell {
        background: #f5576c;
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .signal-hold {
        background: #f6d365;
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# تهيئة Session State
# ============================================
if 'data' not in st.session_state:
    st.session_state.data = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = 'AAPL'
if 'period' not in st.session_state:
    st.session_state.period = '1y'
if 'initialized' not in st.session_state:
    st.session_state.initialized = True

# ============================================
# العنوان الرئيسي
# ============================================
st.markdown('<div class="main-header">📈 منصة التداول بالذكاء الاصطناعي</div>', unsafe_allow_html=True)
st.markdown("---")

# ============================================
# الشريط الجانبي
# ============================================
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # قائمة الأسهم
    symbols_list = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'JPM', 'VTI']
    selected_symbol = st.selectbox(
        "📊 اختر السهم",
        symbols_list,
        index=symbols_list.index(st.session_state.symbol) if st.session_state.symbol in symbols_list else 0
    )
    
    # الفترة الزمنية
    period_options = {
        'شهر': '1mo',
        '3 أشهر': '3mo',
        '6 أشهر': '6mo',
        'سنة': '1y',
        'سنتان': '2y',
        '5 سنوات': '5y'
    }
    selected_period_label = st.selectbox(
        "📅 الفترة الزمنية",
        list(period_options.keys()),
        index=3
    )
    selected_period = period_options[selected_period_label]
    
    # زر التحديث
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        with st.spinner('جاري تحميل البيانات...'):
            try:
                ticker = yf.Ticker(selected_symbol)
                data = ticker.history(period=selected_period)
                if not data.empty:
                    st.session_state.data = data
                    st.session_state.symbol = selected_symbol
                    st.session_state.period = selected_period
                    st.success(f"✅ تم تحديث بيانات {selected_symbol}")
                else:
                    st.error("❌ لا توجد بيانات")
            except Exception as e:
                st.error(f"❌ خطأ: {str(e)}")
    
    st.markdown("---")
    
    # معلومات
    st.caption(f"🕐 آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("📊 بيانات من Yahoo Finance")

# ============================================
# تحميل البيانات
# ============================================
if st.session_state.data is None or st.session_state.symbol != selected_symbol or st.session_state.period != selected_period:
    with st.spinner(f'جاري تحميل بيانات {selected_symbol}...'):
        try:
            ticker = yf.Ticker(selected_symbol)
            data = ticker.history(period=selected_period)
            if not data.empty:
                st.session_state.data = data
                st.session_state.symbol = selected_symbol
                st.session_state.period = selected_period
            else:
                st.error("❌ لا توجد بيانات متاحة")
                st.stop()
        except Exception as e:
            st.error(f"❌ خطأ في تحميل البيانات: {str(e)}")
            st.stop()

data = st.session_state.data

# ============================================
# التحقق من البيانات
# ============================================
if data is None or data.empty:
    st.warning("⚠️ لا توجد بيانات متاحة")
    st.info("💡 اضغط على زر 'تحديث البيانات' في الشريط الجانبي")
    st.stop()

# ============================================
# تبويبات التطبيق
# ============================================
try:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 السعر والمؤشرات",
        "📈 التحليل الفني",
        "🧠 التنبؤ",
        "💼 المحفظة"
    ])
    
    # ============================================
    # TAB 1: السعر والمؤشرات
    # ============================================
    with tab1:
        st.header(f"📊 {selected_symbol} - السعر والمؤشرات")
        
        # أعمدة المعلومات
        col1, col2, col3, col4, col5 = st.columns(5)
        
        current_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close * 100) if prev_close != 0 else 0
        
        with col1:
            st.metric("السعر", f"${current_price:.2f}", f"{price_change_pct:+.2f}%")
        with col2:
            st.metric("أعلى", f"${data['High'].iloc[-1]:.2f}")
        with col3:
            st.metric("أدنى", f"${data['Low'].iloc[-1]:.2f}")
        with col4:
            st.metric("الافتتاح", f"${data['Open'].iloc[-1]:.2f}")
        with col5:
            st.metric("الحجم", f"{data['Volume'].iloc[-1]:,.0f}")
        
        # الرسم البياني الرئيسي
        st.subheader("📈 الرسم البياني")
        
        fig = go.Figure()
        
        # خط السعر
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            name='السعر',
            line=dict(color='#2196F3', width=2)
        ))
        
        # المتوسطات المتحركة
        sma20 = data['Close'].rolling(20).mean()
        sma50 = data['Close'].rolling(50).mean()
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=sma20,
            name='SMA 20',
            line=dict(color='#FF9800', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=sma50,
            name='SMA 50',
            line=dict(color='#4CAF50', width=1, dash='dash')
        ))
        
        fig.update_layout(
            height=500,
            xaxis_title='التاريخ',
            yaxis_title='السعر ($)',
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # بيانات الجدول
        with st.expander("📋 عرض البيانات"):
            st.dataframe(data.tail(20), use_container_width=True)
    
    # ============================================
    # TAB 2: التحليل الفني
    # ============================================
    with tab2:
        st.header("📈 التحليل الفني")
        
        # حساب المؤشرات
        col1, col2 = st.columns(2)
        
        with col1:
            # RSI
            st.subheader("📊 مؤشر القوة النسبية (RSI)")
            
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=data.index,
                y=rsi,
                name='RSI',
                line=dict(color='#9C27B0', width=2)
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="تشبع شرائي")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="تشبع بيعي")
            fig_rsi.update_layout(height=300, template='plotly_white')
            st.plotly_chart(fig_rsi, use_container_width=True)
            
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    st.warning(f"⚠️ RSI = {current_rsi:.2f} - منطقة تشبع شرائي")
                elif current_rsi < 30:
                    st.success(f"✅ RSI = {current_rsi:.2f} - منطقة تشبع بيعي")
                else:
                    st.info(f"ℹ️ RSI = {current_rsi:.2f} - منطقة محايدة")
        
        with col2:
            # MACD
            st.subheader("📊 مؤشر MACD")
            
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(
                x=data.index,
                y=macd,
                name='MACD',
                line=dict(color='#2196F3', width=2)
            ))
            fig_macd.add_trace(go.Scatter(
                x=data.index,
                y=signal,
                name='Signal',
                line=dict(color='#F44336', width=2)
            ))
            fig_macd.add_trace(go.Bar(
                x=data.index,
                y=histogram,
                name='Histogram',
                marker_color=['green' if x > 0 else 'red' for x in histogram]
            ))
            fig_macd.update_layout(height=300, template='plotly_white')
            st.plotly_chart(fig_macd, use_container_width=True)
        
        # Bollinger Bands
        st.subheader("📊 Bollinger Bands")
        
        sma20 = data['Close'].rolling(20).mean()
        std20 = data['Close'].rolling(20).std()
        upper = sma20 + (std20 * 2)
        lower = sma20 - (std20 * 2)
        
        fig_bb = go.Figure()
        fig_bb.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            name='السعر',
            line=dict(color='#2196F3', width=2)
        ))
        fig_bb.add_trace(go.Scatter(
            x=data.index,
            y=upper,
            name='Upper Band',
            line=dict(color='#F44336', width=1, dash='dash')
        ))
        fig_bb.add_trace(go.Scatter(
            x=data.index,
            y=sma20,
            name='Middle Band',
            line=dict(color='#9E9E9E', width=1, dash='dash')
        ))
        fig_bb.add_trace(go.Scatter(
            x=data.index,
            y=lower,
            name='Lower Band',
            line=dict(color='#4CAF50', width=1, dash='dash')
        ))
        fig_bb.update_layout(height=350, template='plotly_white')
        st.plotly_chart(fig_bb, use_container_width=True)
    
    # ============================================
    # TAB 3: التنبؤ
    # ============================================
    with tab3:
        st.header("🧠 التنبؤ بالأسعار")
        
        st.info("ℹ️ يتم استخدام طريقة بسيطة للتنبؤ بناءً على المتوسطات المتحركة")
        
        if st.button("🔮 تنبؤ الأسعار القادمة", use_container_width=True):
            with st.spinner('جاري حساب التنبؤ...'):
                try:
                    # حساب التنبؤ البسيط
                    last_price = data['Close'].iloc[-1]
                    sma20 = data['Close'].rolling(20).mean().iloc[-1]
                    sma50 = data['Close'].rolling(50).mean().iloc[-1]
                    
                    # تحديد الاتجاه
                    if sma20 > sma50:
                        trend = 0.02  # اتجاه صاعد
                        trend_text = "📈 صاعد"
                    elif sma20 < sma50:
                        trend = -0.02  # اتجاه هابط
                        trend_text = "📉 هابط"
                    else:
                        trend = 0
                        trend_text = "➡️ محايد"
                    
                    # توقع 10 أيام
                    predictions = []
                    future_prices = []
                    current = last_price
                    
                    for i in range(1, 11):
                        change = current * trend * np.random.normal(1, 0.005)
                        current = current + change
                        predictions.append(current)
                        future_prices.append(current)
                    
                    # رسم التنبؤ
                    dates = pd.date_range(start=data.index[-1], periods=11, freq='D')[1:]
                    
                    fig_pred = go.Figure()
                    
                    # البيانات التاريخية (آخر 30 يوم)
                    fig_pred.add_trace(go.Scatter(
                        x=data.index[-30:],
                        y=data['Close'].iloc[-30:],
                        name='تاريخي',
                        line=dict(color='#2196F3', width=2)
                    ))
                    
                    # التنبؤ
                    fig_pred.add_trace(go.Scatter(
                        x=dates,
                        y=predictions,
                        name='متوقع',
                        line=dict(color='#FF9800', width=2, dash='dash')
                    ))
                    
                    fig_pred.update_layout(
                        title=f'تنبؤ السعر - الاتجاه: {trend_text}',
                        height=400,
                        template='plotly_white',
                        xaxis_title='التاريخ',
                        yaxis_title='السعر ($)'
                    )
                    
                    st.plotly_chart(fig_pred, use_container_width=True)
                    
                    # جدول التنبؤات
                    pred_df = pd.DataFrame({
                        'التاريخ': dates.strftime('%Y-%m-%d'),
                        'السعر المتوقع': [f"${p:.2f}" for p in predictions],
                        'التغير': [f"{((p - last_price) / last_price * 100):+.2f}%" for p in predictions]
                    })
                    st.dataframe(pred_df, use_container_width=True)
                    
                    # توصية
                    if trend > 0:
                        st.success("📈 توصية: النظر في الشراء")
                    elif trend < 0:
                        st.warning("📉 توصية: النظر في البيع")
                    else:
                        st.info("➡️ توصية: الانتظار")
                        
                except Exception as e:
                    st.error(f"❌ خطأ في التنبؤ: {str(e)}")
    
    # ============================================
    # TAB 4: المحفظة
    # ============================================
    with tab4:
        st.header("💼 إدارة المحفظة")
        
        st.info("ℹ️ هذه أداة لتتبع المحفظة - للعرض فقط")
        
        # محفظة افتراضية
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 الرصيد النقدي", "$10,000")
        with col2:
            st.metric("📊 قيمة الأسهم", "$5,234")
        with col3:
            st.metric("💹 إجمالي المحفظة", "$15,234", "+2.3%")
        
        # أسهم محاكاة
        st.subheader("📈 المراكز المفتوحة")
        
        portfolio_data = pd.DataFrame({
            'السهم': ['AAPL', 'GOOGL', 'MSFT'],
            'الكمية': [10, 5, 8],
            'متوسط السعر': ['$150.00', '$120.00', '$80.00'],
            'السعر الحالي': ['$175.00', '$130.00', '$85.00'],
            'الربح/الخسارة': ['+$250.00', '+$50.00', '+$40.00'],
            'العائد %': ['+16.7%', '+8.3%', '+6.3%']
        })
        st.dataframe(portfolio_data, use_container_width=True)
        
        # إضافة سهم جديد
        st.subheader("➕ إضافة مركز جديد")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_symbol = st.selectbox("السهم", symbols_list, key="new_stock")
        with col2:
            quantity = st.number_input("الكمية", min_value=1, value=10, step=1)
        with col3:
            price = st.number_input("السعر", min_value=1.0, value=100.0, step=0.5)
        
        if st.button("🟢 شراء", use_container_width=True):
            st.success(f"✅ تم شراء {quantity} سهم من {new_symbol} بسعر ${price:.2f}")

except Exception as e:
    st.error(f"❌ حدث خطأ: {str(e)}")
    st.info("💡 حاول تحديث الصفحة (F5) أو إعادة تشغيل التطبيق")

# ============================================
# Footer
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 10px;">
    <p>🚀 منصة التداول بالذكاء الاصطناعي | بيانات من Yahoo Finance</p>
    <p style="font-size: 0.8rem;">⚠️ لأغراض تعليمية فقط - ليس نصيحة استثمارية</p>
</div>
""", unsafe_allow_html=True)
