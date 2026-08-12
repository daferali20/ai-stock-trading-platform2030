import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import sys
import os

# إضافة المسار الرئيسي للمشروع
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استيراد الملفات من src
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
    page_title="AI Stock Trading Platform",
    page_icon="📈",
    layout="wide"
)

# تهيئة الحالة
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.data_fetcher = DataFetcher()
    st.session_state.signal_engine = SignalEngine()
    st.session_state.alert_system = AlertSystem()
    st.session_state.portfolio = PortfolioManager(Config.INITIAL_CAPITAL)
    st.session_state.symbols = Config.DEFAULT_SYMBOLS

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
    
    # أزرار التحكم
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.session_state.data = st.session_state.data_fetcher.fetch_stock_data(symbol, period)
            st.rerun()
    
    with col2:
        if st.button("📊 تحليل", use_container_width=True):
            st.session_state.analyze = True
    
    st.markdown("---")
    
    # معلومات المحفظة
    st.header("💼 المحفظة")
    if st.button("📋 عرض حالة المحفظة"):
        current_prices = {}
        for sym in st.session_state.positions:
            price = st.session_state.data_fetcher.get_current_price(sym)
            if price:
                current_prices[sym] = price
        
        status = st.session_state.portfolio.get_portfolio_status(current_prices)
        st.json(status)

# جلب البيانات
if 'data' not in st.session_state or st.session_state.get('symbol') != symbol:
    with st.spinner(f'جاري تحميل بيانات {symbol}...'):
        st.session_state.data = st.session_state.data_fetcher.fetch_stock_data(symbol, period)
        st.session_state.symbol = symbol

data = st.session_state.data

if data is not None and not data.empty:
    # تبويبات رئيسية
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 السعر والمؤشرات",
        "📈 التحليل الفني",
        "🧠 تحليل المشاعر والتنبؤ",
        "🎯 الإشارات والتوصيات",
        "💼 إدارة المحفظة"
    ])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # الرسم البياني للسعر
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=('السعر مع المتوسطات المتحركة', 'حجم التداول', 'RSI'),
                row_heights=[0.6, 0.2, 0.2]
            )
            
            # سعر الإغلاق
            fig.add_trace(
                go.Scatter(
                    x=data['Date'],
                    y=data['Close'],
                    name='Close',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
            
            # المتوسطات المتحركة
            for window, color in [(20, 'orange'), (50, 'green')]:
                sma = data[f'SMA_{window}'] if f'SMA_{window}' in data.columns else None
                if sma is not None and not sma.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=data['Date'],
                            y=sma,
                            name=f'SMA {window}',
                            line=dict(color=color, width=1, dash='dash')
                        ),
                        row=1, col=1
                    )
            
            # الحجم
            fig.add_trace(
                go.Bar(
                    x=data['Date'],
                    y=data['Volume'],
                    name='Volume',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
            
            # RSI
            ta = TechnicalAnalyzer(data)
            rsi = ta.calculate_rsi()
            if rsi is not None and not rsi.empty:
                fig.add_trace(
                    go.Scatter(
                        x=data['Date'],
                        y=rsi,
                        name='RSI',
                        line=dict(color='purple', width=2)
                    ),
                    row=3, col=1
                )
                # خطوط RSI
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            fig.update_layout(height=700, showlegend=True)
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
            
            # معلومات إضافية
            st.markdown("### 📊 معلومات إضافية")
            st.markdown(f"""
            **High:** ${data['High'].iloc[-1]:.2f}  
            **Low:** ${data['Low'].iloc[-1]:.2f}  
            **Open:** ${data['Open'].iloc[-1]:.2f}  
            **Volume:** {data['Volume'].iloc[-1]:,.0f}
            """)
            
            # معلومات السوق
            st.markdown("### 🌍 السوق")
            market_data = st.session_state.data_fetcher.get_market_data()
            for name, value in market_data.items():
                st.metric(name, f"{value:.2f}")
    
    with tab2:
        st.header("📈 التحليل الفني المتقدم")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bollinger Bands
            st.subheader("Bollinger Bands")
            bb = ta.calculate_bollinger_bands()
            
            if 'BB_High' in bb and 'BB_Low' in bb:
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
                
                fig_bb.update_layout(height=400)
                st.plotly_chart(fig_bb, use_container_width=True)
        
        with col2:
            # MACD
            st.subheader("MACD")
            macd_data = ta.calculate_macd()
            
            if 'MACD' in macd_data and 'MACD_Signal' in macd_data:
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
                
                # Histogram
                colors = ['green' if x > 0 else 'red' for x in macd_data['MACD_Diff']]
                fig_macd.add_trace(go.Bar(
                    x=data['Date'],
                    y=macd_data['MACD_Diff'],
                    name='Histogram',
                    marker_color=colors
                ))
                
                fig_macd.update_layout(height=400)
                st.plotly_chart(fig_macd, use_container_width=True)
        
        # جميع المؤشرات في جدول
        st.subheader("📋 ملخص المؤشرات الفنية")
        signals = ta.get_technical_signals()
        df_signals = pd.DataFrame([signals]).T
        df_signals.columns = ['الإشارة']
        st.dataframe(df_signals, use_container_width=True)
    
    with tab3:
        st.header("🧠 تحليل المشاعر والتنبؤ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # تحليل المشاعر
            st.subheader("📰 تحليل المشاعر")
            
            if st.button("🔄 تحليل المشاعر"):
                with st.spinner('جاري تحليل المشاعر...'):
                    sentiment = st.session_state.data_fetcher.sentiment_analyzer.get_news_sentiment(symbol)
                    
                    if sentiment:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        with col_s1:
                            st.metric("المشاعر", sentiment['sentiment'])
                        with col_s2:
                            st.metric("النتيجة", f"{sentiment['score']:.2f}")
                        with col_s3:
                            st.metric("المصادر", sentiment.get('sources', 0))
            
            # التحليل الأساسي
            st.subheader("📊 البيانات الأساسية")
            if st.button("📊 عرض البيانات الأساسية"):
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    # عرض المعلومات الأساسية
                    key_metrics = {
                        'السوق': info.get('market', 'N/A'),
                        'القطاع': info.get('sector', 'N/A'),
                        'القيمة السوقية': info.get('marketCap', 'N/A'),
                        'نسبة PE': info.get('trailingPE', 'N/A'),
                        'نسبة التوزيع': info.get('dividendYield', 'N/A'),
                        'بيتا': info.get('beta', 'N/A')
                    }
                    
                    for key, value in key_metrics.items():
                        st.text(f"{key}: {value}")
                except Exception as e:
                    st.error(f"خطأ في جلب البيانات الأساسية: {e}")
        
        with col2:
            # التنبؤ بالأسعار
            st.subheader("🔮 التنبؤ بالأسعار")
            
            if st.button("🤖 تنبؤ LSTM"):
                with st.spinner('جاري التنبؤ...'):
                    pm = PredictionModel(symbol)
                    
                    # تدريب النموذج
                    if st.checkbox("تدريب النموذج من جديد"):
                        with st.spinner('جاري تدريب النموذج...'):
                            pm.train_lstm(data, epochs=10)  # epochs قليلة للعرض
                    
                    # التنبؤ
                    predictions = pm.predict_lstm(data, days=10)
                    
                    if predictions is not None:
                        # عرض النتائج
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
                        
                        # عرض التنبؤات كجدول
                        pred_df = pd.DataFrame({
                            'التاريخ': dates,
                            'السعر المتوقع': predictions
                        })
                        st.dataframe(pred_df, use_container_width=True)
                    else:
                        st.warning("لم يتمكن النموذج من عمل التنبؤ. تأكد من تدريب النموذج.")
            
            if st.button("📈 تنبؤ Prophet"):
                with st.spinner('جاري التنبؤ...'):
                    pm = PredictionModel(symbol)
                    forecast = pm.prophet_predict(data, days=10)
                    
                    if forecast is not None:
                        fig_prophet = go.Figure()
                        fig_prophet.add_trace(go.Scatter(
                            x=forecast['ds'],
                            y=forecast['yhat'],
                            name='Prediction',
                            line=dict(color='green')
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
    
    with tab4:
        st.header("🎯 الإشارات والتوصيات")
        
        # توليد الإشارة
        if st.button("🔄 توليد إشارة جديدة", use_container_width=True):
            with st.spinner('جاري التحليل...'):
                signal = st.session_state.signal_engine.generate_signal(data, symbol)
                
                if signal:
                    # عرض الإشارة
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        color = {
                            'BUY': 'green',
                            'HOLD': 'orange',
                            'SELL': 'red'
                        }
                        st.markdown(f"""
                        <div style="
                            text-align: center;
                            padding: 20px;
                            background-color: {color[signal['signal']]}20;
                            border-radius: 10px;
                            border: 2px solid {color[signal['signal']]};
                        ">
                            <h2 style="color: {color[signal['signal']]}; margin: 0;">
                                {signal['signal']}
                            </h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.metric("الثقة", f"{signal['confidence']:.1f}%")
                    
                    with col3:
                        st.metric("النتيجة النهائية", f"{signal['score']:.2f}")
                    
                    # التفاصيل
                    st.subheader("📋 تفاصيل التحليل")
                    details_df = pd.DataFrame([{
                        'العامل': factor,
                        'النتيجة': f"{score:.2f}"
                    } for factor, score in signal['details'].items()])
                    st.dataframe(details_df, use_container_width=True)
                    
                    # إرسال التنبيه
                    if st.button("📤 إرسال التنبيه"):
                        st.session_state.alert_system.send_signal_alert(signal, symbol)
                        st.success("✅ تم إرسال التنبيه")
        
        # التوصيات المباشرة
        st.subheader("📌 التوصيات المباشرة")
        
        # عرض الإشارات الفنية
        if 'data' in st.session_state:
            ta = TechnicalAnalyzer(data)
            tech_signals = ta.get_technical_signals()
            
            for indicator, signal in tech_signals.items():
                st.markdown(f"**{indicator}:** {signal}")
    
    with tab5:
        st.header("💼 إدارة المحفظة")
        
        # حالة المحفظة الحالية
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 حالة المحفظة")
            
            # الحصول على الأسعار الحالية
            current_prices = {}
            for sym in st.session_state.portfolio.positions:
                price = st.session_state.data_fetcher.get_current_price(sym)
                if price:
                    current_prices[sym] = price
            
            status = st.session_state.portfolio.get_portfolio_status(current_prices)
            
            # عرض المقاييس الرئيسية
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            with metrics_col1:
                st.metric("القيمة الإجمالية", f"${status['total_value']:.2f}")
            with metrics_col2:
                gain_loss = status.get('gain_loss', 0)
                gain_loss_pct = status.get('gain_loss_pct', 0)
                st.metric(
                    "الربح/الخسارة",
                    f"${gain_loss:+.2f}",
                    f"{gain_loss_pct:+.2f}%"
                )
            with metrics_col3:
                st.metric("النقدية", f"${status['cash']:.2f}")
            
            # المراكز المفتوحة
            if status['positions']:
                st.subheader("📈 المراكز المفتوحة")
                positions_df = pd.DataFrame(status['positions']).T
                st.dataframe(positions_df, use_container_width=True)
        
        with col2:
            st.subheader("➕ إضافة مركز جديد")
            
            # اختيار السهم
            new_symbol = st.selectbox(
                "السهم",
                st.session_state.symbols,
                key='new_symbol'
            )
            
            # كمية الشراء
            quantity = st.number_input(
                "الكمية",
                min_value=1,
                step=1,
                value=10
            )
            
            # السعر الحالي
            current_price = st.session_state.data_fetcher.get_current_price(new_symbol)
            if current_price:
                st.info(f"السعر الحالي: ${current_price:.2f}")
                total_cost = quantity * current_price
                st.warning(f"التكلفة الإجمالية: ${total_cost:.2f}")
                
                if st.button("🟢 شراء"):
                    if total_cost <= st.session_state.portfolio.cash:
                        st.session_state.portfolio.add_position(new_symbol, quantity, current_price)
                        st.success(f"✅ تم شراء {quantity} سهم من {new_symbol}")
                        st.rerun()
                    else:
                        st.error("❌ رصيد غير كافٍ")
            
            # بيع مركز
            st.subheader("🔴 بيع مركز")
            
            if st.session_state.portfolio.positions:
                sell_symbol = st.selectbox(
                    "اختر السهم للبيع",
                    list(st.session_state.portfolio.positions.keys()),
                    key='sell_symbol'
                )
                
                sell_quantity = st.number_input(
                    "الكمية للبيع",
                    min_value=1,
                    max_value=st.session_state.portfolio.positions[sell_symbol]['quantity'],
                    step=1,
                    key='sell_quantity'
                )
                
                current_price = st.session_state.data_fetcher.get_current_price(sell_symbol)
                if current_price and st.button("🔴 بيع"):
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
        st.subheader("📜 تاريخ العمليات")
        if st.session_state.portfolio.history:
            history_df = pd.DataFrame(st.session_state.portfolio.history)
            st.dataframe(history_df, use_container_width=True)

else:
    st.error(f"❌ حدث خطأ في جلب بيانات {symbol}")

# Footer
st.markdown("---")
st.caption("🚀 تم التطوير باستخدام Streamlit | بيانات من Yahoo Finance | لأغراض تعليمية فقط")
