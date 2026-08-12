import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# إعدادات الصفحة
st.set_page_config(
    page_title="AI Stock Trading Platform",
    page_icon="📈",
    layout="wide"
)

# عنوان التطبيق
st.title("📈 AI Stock Trading Platform")
st.markdown("---")

# تهيئة حالة الجلسة
if 'data' not in st.session_state:
    st.session_state.data = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = 'AAPL'
if 'period' not in st.session_state:
    st.session_state.period = '1y'

# الشريط الجانبي
with st.sidebar:
    st.header("⚙️ الإعدادات")
    
    # اختيار السهم
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META']
    symbol = st.selectbox("اختر السهم", symbols, index=0)
    
    # فترة البيانات
    period = st.selectbox(
        "الفترة الزمنية",
        ['1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3
    )
    
    # زر التحديث
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        with st.spinner('جاري تحميل البيانات...'):
            try:
                ticker = yf.Ticker(symbol)
                st.session_state.data = ticker.history(period=period)
                st.session_state.symbol = symbol
                st.session_state.period = period
                st.success("✅ تم تحديث البيانات")
            except Exception as e:
                st.error(f"❌ خطأ: {e}")

# جلب البيانات إذا لم تكن موجودة
if st.session_state.data is None or st.session_state.symbol != symbol or st.session_state.period != period:
    with st.spinner(f'جاري تحميل بيانات {symbol}...'):
        try:
            ticker = yf.Ticker(symbol)
            st.session_state.data = ticker.history(period=period)
            st.session_state.symbol = symbol
            st.session_state.period = period
        except Exception as e:
            st.error(f"❌ خطأ في تحميل البيانات: {e}")
            st.session_state.data = None

data = st.session_state.data

# عرض البيانات إذا كانت موجودة
if data is not None and not data.empty:
    try:
        # تبويبات
        tab1, tab2 = st.tabs(["📊 السعر والمؤشرات", "📈 التحليل الفني"])
        
        with tab1:
            st.header("📊 السعر والمؤشرات")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # الرسم البياني
                fig = go.Figure()
                
                # خط السعر
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=data['Close'],
                    name='Close',
                    line=dict(color='blue', width=2)
                ))
                
                # المتوسطات المتحركة
                sma20 = data['Close'].rolling(window=20).mean()
                sma50 = data['Close'].rolling(window=50).mean()
                
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=sma20,
                    name='SMA 20',
                    line=dict(color='orange', width=1, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=sma50,
                    name='SMA 50',
                    line=dict(color='green', width=1, dash='dash')
                ))
                
                fig.update_layout(
                    title=f'{symbol} - السعر',
                    height=500,
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
                
                st.markdown("### 📊 معلومات")
                st.markdown(f"""
                **أعلى:** ${data['High'].iloc[-1]:.2f}  
                **أدنى:** ${data['Low'].iloc[-1]:.2f}  
                **الافتتاح:** ${data['Open'].iloc[-1]:.2f}  
                **الحجم:** {data['Volume'].iloc[-1]:,.0f}
                """)
        
        with tab2:
            st.header("📈 التحليل الفني")
            
            # RSI
            st.subheader("مؤشر القوة النسبية (RSI)")
            
            # حساب RSI
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
                line=dict(color='purple', width=2)
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            fig_rsi.update_layout(height=300)
            st.plotly_chart(fig_rsi, use_container_width=True)
            
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                st.info(f"RSI الحالي: {current_rsi:.2f}")
            
            # Bollinger Bands
            st.subheader("Bollinger Bands")
            
            sma20 = data['Close'].rolling(window=20).mean()
            std20 = data['Close'].rolling(window=20).std()
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)
            
            fig_bb = go.Figure()
            fig_bb.add_trace(go.Scatter(
                x=data.index,
                y=data['Close'],
                name='Price',
                line=dict(color='blue')
            ))
            fig_bb.add_trace(go.Scatter(
                x=data.index,
                y=upper_band,
                name='Upper Band',
                line=dict(color='red', dash='dash')
            ))
            fig_bb.add_trace(go.Scatter(
                x=data.index,
                y=sma20,
                name='Middle Band',
                line=dict(color='gray', dash='dash')
            ))
            fig_bb.add_trace(go.Scatter(
                x=data.index,
                y=lower_band,
                name='Lower Band',
                line=dict(color='green', dash='dash')
            ))
            fig_bb.update_layout(height=300)
            st.plotly_chart(fig_bb, use_container_width=True)
            
            # حجم التداول
            st.subheader("حجم التداول")
            
            fig_volume = go.Figure()
            colors = ['green' if data['Close'].iloc[i] >= data['Open'].iloc[i] else 'red' 
                     for i in range(len(data))]
            fig_volume.add_trace(go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors
            ))
            fig_volume.update_layout(height=300)
            st.plotly_chart(fig_volume, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        st.info("💡 حاول تحديث الصفحة")

else:
    st.warning("⚠️ لا توجد بيانات متاحة")
    st.info("💡 اضغط على زر 'تحديث البيانات' في الشريط الجانبي")

# Footer
st.markdown("---")
st.caption("🚀 تم التطوير باستخدام Streamlit | بيانات من Yahoo Finance | لأغراض تعليمية فقط")
