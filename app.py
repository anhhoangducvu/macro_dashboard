import streamlit as st
import pandas as pd
import time
import os
from datetime import datetime
from utils.data_collector import get_global_indicators, scrape_gold_prices, get_market_news
from utils.analyzer import MacroAnalyzer
from dotenv import load_dotenv

# Tải biến môi trường từ .env
load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Chiến lược Vĩ mô & Tài chính",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stMetric { background: rgba(255, 255, 255, 0.03); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .main-title { background: linear-gradient(90deg, #00d4ff, #0055ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.2rem; }
    .gold-card { background: rgba(255, 215, 0, 0.03); padding: 0.8rem; border-radius: 8px; border: 1px solid rgba(255, 215, 0, 0.15); margin-bottom: 8px; }
    .ticker-chip { display: inline-block; background: rgba(255,255,255,0.08); padding: 2px 8px; border-radius: 4px; margin-right: 5px; margin-bottom: 5px; font-size: 0.8rem; font-weight: bold; border: 1px solid rgba(255,255,255,0.1); }
    .sector-card { padding: 15px; border-radius: 12px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.08); }
    .positive { border-left: 5px solid #28a745; background-color: rgba(40, 167, 69, 0.05); }
    .negative { border-left: 5px solid #f44336; background-color: rgba(244, 67, 54, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- APP HEADER ---
st.markdown("<h1 class='main-title'>Chiến lược Vĩ mô</h1>", unsafe_allow_html=True)
st.markdown(f"**TEXO Engineering** | Đồng bộ: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- SIDEBAR & API SECURITY ---
with st.sidebar:
    st.image("https://texo.vn/wp-content/uploads/2021/03/logo-texo.png", width=180)
    st.divider()
    
    # Bảo mật API Key: Ưu tiên Streamlit Secrets, sau đó là biến môi trường, cuối cùng mới nhập tay
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("Nhập Google API Key (Bảo mật):", type="password")
        if not api_key:
            st.warning("⚠️ Vui lòng cung cấp API Key để sử dụng phân tích AI.")
    
    if st.button("🔄 Cập nhật Dữ liệu", type="primary", use_container_width=True):
        st.cache_data.clear()
        if 'analysis' in st.session_state: del st.session_state['analysis']
        st.rerun()
    st.info("Bản cập nhật 3.3 - Bảo mật API")

# --- DATA LOADING ---
def load_data():
    with st.status("🔄 Đang quét đa nguồn (DNSE/Vietstock/Cafef)...", expanded=True) as status:
        indicators = get_global_indicators()
        gold_prices = scrape_gold_prices()
        news = get_market_news()
        status.update(label="✅ Đã cập nhật xong dữ liệu!", state="complete", expanded=False)
        return indicators, gold_prices, news

indicators, gold_prices, news = load_data()

# --- 1. CHỈ BÁO THỊ TRƯỜNG ---
st.markdown("### 📊 Chỉ báo Kinh tế")
indicator_names = {
    "VN-Index": "VN-Index (VNI)",
    "VN30-Index": "VN30-Index",
    "HNX-Index": "HNX-Index",
    "DXY": "Chỉ số Dollar (DXY)",
    "S&P 500": "S&P 500 (Mỹ)",
    "Gold (World)": "Vàng Thế giới",
    "Oil (WTI)": "Dầu Thô (WTI)",
    "Bitcoin": "Bitcoin (BTC)",
    "USD/VND": "Tỷ giá USD/VND",
    "US 10Y Yield": "Lãi suất Mỹ 10Y"
}

cols = st.columns(4)
for i, (key, label) in enumerate(indicator_names.items()):
    val = indicators.get(key, {"value": "N/A", "percent": 0})
    with cols[i % 4]:
        st.metric(
            label=label,
            value=f"{val['value']:,}" if isinstance(val['value'], (int, float)) else val['value'],
            delta=f"{val['percent']}%" if val['percent'] != 0 else None
        )

st.divider()

# --- 2. GIÁ VÀNG & TIN TỨC ---
col_gold, col_news = st.columns([1.2, 1])
with col_gold:
    st.markdown("### 🏆 Vàng Nhẫn Trong nước")
    for brand, prices in gold_prices.items():
        st.markdown(f"<div class='gold-card'><b style='color: #FFD700;'>{brand}</b> | Mua: <span style='color: #28a745;'>{prices['buy']}</span> | Bán: <span style='color: #f44336;'>{prices['sell']}</span></div>", unsafe_allow_html=True)

with col_news:
    st.markdown("### 📰 Tin tiêu điểm")
    for idx, item in enumerate(news[:6]): st.markdown(f"🔹 {item}")

st.divider()

# --- 3. AI ANALYSIS ---
if api_key:
    if 'analysis' not in st.session_state:
        with st.status("🧠 AI đang phân tích dữ liệu vĩ mô (5x5)...", expanded=True) as status:
            try:
                analyzer = MacroAnalyzer(api_key)
                st.session_state['analysis'] = analyzer.analyze(indicators, gold_prices, news)
                status.update(label="💎 Phân tích hoàn tất!", state="complete", expanded=False)
            except Exception as e:
                status.update(label=f"❌ Lỗi AI: {str(e)}", state="error", expanded=True)
                st.session_state['analysis'] = {"sentiment": "Lỗi", "summary": "Không thể kết nối với Gemini. Vui lòng kiểm tra lại API Key.", "positive_sectors": [], "negative_sectors": [], "gold_advice": ""}

    analysis = st.session_state['analysis']
    sentiment = analysis.get("sentiment", "Trung lập")
    bg_color = "#28a745" if sentiment in ["Greed", "Hưng phấn", "Tích cực"] else ("#f44336" if sentiment in ["Fear", "Sợ hãi", "Tiêu cực"] else "#ffcc00")
    
    st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);'>
            <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 10px;'>
                <div style='background: {bg_color}; padding: 4px 12px; border-radius: 15px; font-weight: bold; color: white;'>{sentiment}</div>
                <h4 style='margin: 0;'>NHẬN ĐỊNH CHIẾN LƯỢC VĨ MÔ</h4>
            </div>
            <p>{analysis.get('summary', '')}</p>
            <div style='padding: 8px; background: rgba(0,212,255,0.06); border-radius: 6px; border-left: 4px solid #00d4ff;'>
                <b>💡 Tư vấn Vàng:</b> {analysis.get('gold_advice', '')}
            </div>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📈 **5 NGÀNH HƯỞNG LỢI**")
        for s in analysis.get("positive_sectors", [])[:5]:
            t_html = "".join([f"<span class='ticker-chip'>{t}</span>" for t in s.get('tickers', [])[:5]])
            st.markdown(f"<div class='sector-card positive'><b>{s['name']}</b><p style='font-size: 0.85rem;'>{s['reason']}</p><div>{t_html}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("#### 📉 **5 NGÀNH RỦI RO**")
        for s in analysis.get("negative_sectors", [])[:5]:
            t_html = "".join([f"<span class='ticker-chip' style='color: #f44336;'>{t}</span>" for t in s.get('tickers', [])[:5]])
            st.markdown(f"<div class='sector-card negative'><b>{s['name']}</b><p style='font-size: 0.85rem;'>{s['reason']}</p><div>{t_html}</div></div>", unsafe_allow_html=True)

st.divider()
st.caption("© 2026 TEXO Engineering | Dữ liệu chỉ mang tính chất tham khảo.")
