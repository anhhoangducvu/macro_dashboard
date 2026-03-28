import streamlit as st
import os
import sys
from datetime import datetime

# ─── DEBUG INITIALIZATION ────────────────────────────────────────────────────
# This ensures that even if imports fail later, we see something.
st.set_page_config(
    page_title="V-Macro Insights",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from utils.data_collector import get_global_indicators, scrape_gold_prices_domestic, get_market_news
    from utils.analyzer import MacroAnalyzer
except Exception as e:
    st.error(f"❌ Lỗi khởi tạo (Import Error): {e}")
    st.stop()

from dotenv import load_dotenv
load_dotenv()


# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, html, body { font-family: 'Inter', sans-serif !important; }
.stApp { background: #080e1a !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
/* Remove ugly gaps */
section[data-testid="stSidebar"] { background: #0d1424; border-right: 1px solid rgba(255,255,255,0.08); }

/* HEADER */
.vmacro-header { display:flex; justify-content:space-between; align-items:center;
  padding:16px 0 18px; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:22px; }
.vmacro-logo { font-size:26px; font-weight:800; color:white; letter-spacing:-0.5px; }
.vmacro-logo span { background:linear-gradient(90deg,#3b82f6,#60a5fa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.vmacro-sub { font-size:12px; color:#64748b; margin-top:3px; }
.vmacro-time { font-size:12px; color:#94a3b8; background:rgba(255,255,255,0.05);
  padding:6px 14px; border-radius:20px; border:1px solid rgba(255,255,255,0.1); }

/* INDICATOR CARDS */
.ind-card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
  border-radius:14px; padding:16px 18px; margin-bottom:14px;
  transition:transform .2s, border-color .2s; }
.ind-card:hover { transform:translateY(-2px); border-color:rgba(59,130,246,0.5); }
.ind-label { font-size:10.5px; font-weight:600; color:#475569; letter-spacing:0.9px;
  text-transform:uppercase; margin-bottom:8px; }
.ind-value { font-size:24px; font-weight:700; color:white; line-height:1.15; margin-bottom:8px; }
.dpos { display:inline-block; font-size:11.5px; font-weight:600; padding:3px 9px;
  border-radius:20px; background:rgba(34,197,94,.15); color:#22c55e; }
.dneg { display:inline-block; font-size:11.5px; font-weight:600; padding:3px 9px;
  border-radius:20px; background:rgba(239,68,68,.15); color:#ef4444; }
.dneu { display:inline-block; font-size:11.5px; font-weight:600; padding:3px 9px;
  border-radius:20px; background:rgba(100,116,139,.12); color:#94a3b8; }

/* SECTION TITLE */
.sec-title { font-size:15px; font-weight:700; color:white; display:flex;
  align-items:center; gap:8px; margin-bottom:16px; padding-bottom:10px;
  border-bottom:1px solid rgba(255,255,255,0.07); margin-top:10px; }

/* NEWS ITEMS */
.news-item { display:flex; gap:12px; margin-bottom:14px; align-items:flex-start; }
.news-dot  { width:6px; height:6px; border-radius:50%; background:#3b82f6; margin-top:6px; flex-shrink:0; }
.news-text { font-size:12.5px; color:#cbd5e1; line-height:1.6; }

/* SECTOR CARDS */
.sc-pos { background:rgba(34,197,94,.04); border:1px solid rgba(34,197,94,.15);
  border-left:4px solid #22c55e; border-radius:12px; padding:16px; margin-bottom:12px; }
.sc-neg { background:rgba(239,68,68,.04); border:1px solid rgba(239,68,68,.15);
  border-left:4px solid #ef4444; border-radius:12px; padding:16px; margin-bottom:12px; }
.sc-name-pos { font-size:14px; font-weight:800; color:#22c55e; margin-bottom:6px; }
.sc-name-neg { font-size:14px; font-weight:800; color:#ef4444; margin-bottom:6px; }
.sc-reason   { font-size:12.5px; color:#94a3b8; line-height:1.6; margin-bottom:10px; }
.chip-pos { display:inline-block; background:rgba(34,197,94,.12); color:#22c55e;
  border:1px solid rgba(34,197,94,.3); font-size:10.5px; font-weight:700;
  padding:3px 10px; border-radius:6px; margin:2px 4px 2px 0; }
.chip-neg { display:inline-block; background:rgba(239,68,68,.12); color:#ef4444;
  border:1px solid rgba(239,68,68,.3); font-size:10.5px; font-weight:700;
  padding:3px 10px; border-radius:6px; margin:2px 4px 2px 0; }

/* GOLD CARD UI */
.gold-card { background:rgba(251,191,36,.06); border:1px solid rgba(251,191,36,.15);
  border-radius:12px; padding:15px; margin-bottom:12px; }
.gold-card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.gold-card-brand { font-size:15px; font-weight:800; color:#fbbf24; }
.gold-card-type { font-size:11px; color:#94a3b8; font-weight:600; text-transform:uppercase; }
.gold-price-row { display:flex; justify-content:space-between; gap:10px; }
.gp-box { flex:1; background:rgba(255,255,255,0.03); border-radius:8px; padding:8px 12px; }
.gp-lbl { font-size:10px; color:#64748b; text-transform:uppercase; margin-bottom:2px; }
.gp-val-buy { font-size:16px; font-weight:700; color:#22c55e; }
.gp-val-sell { font-size:16px; font-weight:700; color:#ef4444; }

/* SENTIMENT */
.sent-wrap { border-radius:14px; padding:20px 24px; margin-bottom:22px;
  background:linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
  border:1px solid rgba(255,255,255,0.08); position:relative; overflow:hidden; }
.sent-badge { display:inline-block; padding:5px 18px; border-radius:20px;
  font-size:12px; font-weight:800; color:white; margin-bottom:12px; text-transform:uppercase; }
.s-greed   { background:linear-gradient(90deg, #22c55e, #16a34a); box-shadow: 0 4px 12px rgba(34,197,94,0.3); }
.s-fear    { background:linear-gradient(90deg, #ef4444, #dc2626); box-shadow: 0 4px 12px rgba(239,68,68,0.3); }
.s-neutral { background:linear-gradient(90deg, #f59e0b, #d97706); box-shadow: 0 4px 12px rgba(245,158,11,0.3); }
.sent-summary { font-size:14px; color:#e2e8f0; line-height:1.75; margin-bottom:14px; font-weight:400; }
.gold-advice-box { background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,0.2);
  border-left:4px solid #3b82f6; border-radius:4px 10px 10px 4px; padding:12px 16px; font-size:13.5px; color:#bfdbfe; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")

    # API key: prioritized from secrets/env (no hardcoding to prevent leaks)
    api_key_env = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    
    if api_key_env:
        api_key = api_key_env
        mask = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "****"
        st.success(f"✅ AI Connected ({mask})")
    else:
        api_key = st.text_input("🔑 Nhập Google API Key:", type="password", placeholder="AIzaSy...")
        if not api_key:
            st.warning("⚠️ Cần API Key để sử dụng AI.")

    if st.button("🔄 Làm mới dữ liệu", type="primary", use_container_width=True):
        st.cache_data.clear()
        if "analysis" in st.session_state:
            del st.session_state["analysis"]
        st.rerun()

    st.divider()
    st.caption("**V-Macro Insights v3.5**\nDữ liệu: CafeF, DNSE, Yahoo Finance\nVàng: BTMC, BTMH, SJC, DOJI, PNJ\n\n© 2026 Macro Dashboard Project")



# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="vmacro-header">
  <div>
    <div class="vmacro-logo">V-Macro <span>Insights</span></div>
    <div class="vmacro-sub">Hệ thống Phân tích Vĩ mô & Ngành ứng dụng AI</div>
  </div>
  <div class="vmacro-time">🕐 Cập nhật: {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}</div>
</div>
""", unsafe_allow_html=True)


# ─── DATA LOADING (cached) ────────────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def load_indicators():    return get_global_indicators()

@st.cache_data(ttl=1800, show_spinner=False)
def load_gold():         return scrape_gold_prices_domestic()

@st.cache_data(ttl=1800, show_spinner=False)
def load_news():         return get_market_news()


with st.spinner("⏳ Đang nạp dữ liệu thị trường..."):
    try:
        indicators = load_indicators()
    except Exception:
        indicators = {}
        
    try:
        gold_data  = load_gold()
    except Exception:
        gold_data = []
        
    try:
        news       = load_news()
    except Exception:
        news = {"world": [], "domestic": []}



# ─── HELPER: render indicator card ───────────────────────────────────────────
def _card(icon: str, label: str, val: dict, prefix: str = "", decimals: int = 2) -> str:
    v   = val.get("value", "N/A")
    pct = val.get("percent", 0.0)
    if isinstance(v, (int, float)):
        fmt = f"{prefix}{v:,.{decimals}f}"
    else:
        fmt = str(v)
    if pct > 0:
        delta = f'<span class="dpos">▲ +{pct:.2f}%</span>'
    elif pct < 0:
        delta = f'<span class="dneg">▼ {pct:.2f}%</span>'
    else:
        delta = f'<span class="dneu">— {pct:.2f}%</span>'
    return f"""<div class="ind-card">
  <div class="ind-label">{icon}&nbsp; {label}</div>
  <div class="ind-value">{fmt}</div>
  {delta}
</div>"""


# ─── 12 INDICATOR CARDS ──────────────────────────────────────────────────────
CARDS = [
    ("📈", "VN-INDEX",          "VN-Index",     "",  2),
    ("🌐", "S&P 500",           "S&P 500",      "",  2),
    ("₿",  "GIÁ BITCOIN",       "Bitcoin",      "",  2),
    ("💵", "CHỈ SỐ DXY",        "DXY",          "",  2),
    ("💹", "TỶ GIÁ USD/VND",    "USD/VND",      "",  0),
    ("🏆", "GIÁ VÀNG (OUNCE)",  "Gold (World)", "$", 2),
    ("🛢️", "DẦU BRENT",         "Oil (Brent)",  "$", 2),
    ("🏦", "LÃI SUẤT FED",      "FED Rate",     "",  2),
    ("😱", "VIX (FEAR INDEX)",  "VIX",          "",  2),
    ("📊", "US 10Y YIELD",      "US 10Y Yield", "",  2),
    ("🇭🇰","HANG SENG (HSI)",   "Hang Seng",    "",  2),
    ("🔶", "ĐỒNG (COPPER)",     "Copper",       "$", 2),
]

rows = [CARDS[i:i+4] for i in range(0, 12, 4)]
for row in rows:
    cols = st.columns(4)
    for col, (icon, label, key, prefix, dec) in zip(cols, row):
        with col:
            st.markdown(_card(icon, label, indicators.get(key, {"value": "N/A", "percent": 0}), prefix, dec),
                        unsafe_allow_html=True)

st.divider()


# ─── DOMESTIC GOLD PRICES ────────────────────────────────────────────────────
st.markdown('<div class="sec-title">🏅 Diễn biến Giá Vàng Trong Nước</div>', unsafe_allow_html=True)

def _gold_card(g):
    return f"""<div class="gold-card">
    <div class="gold-card-header">
        <span class="gold-card-brand">{g['brand']}</span>
        <span class="gold-card-type">{g['type']}</span>
    </div>
    <div class="gold-price-row">
        <div class="gp-box">
            <div class="gp-lbl">Mua vào</div>
            <div class="gp-val-buy">{g['buy']}</div>
        </div>
        <div class="gp-box">
            <div class="gp-lbl">Bán ra</div>
            <div class="gp-val-sell">{g['sell']}</div>
        </div>
    </div>
</div>"""

# Render gold prices in a clean grid
g_cols = st.columns(3)
for i, g in enumerate(gold_data):
    with g_cols[i % 3]:
        st.markdown(_gold_card(g), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)



# ─── AI ANALYSIS ─────────────────────────────────────────────────────────────
if api_key and "analysis" not in st.session_state:
    with st.status("🧠 AI đang phân tích dữ liệu vĩ mô...", expanded=True) as status:
        try:
            # Add a small timeout or check if indicators has any data
            if not indicators:
                raise ValueError("Không có dữ liệu kinh tế để phân tích.")
                
            analyzer = MacroAnalyzer(api_key)
            result = analyzer.analyze(indicators, gold_data, news)
            
            if result and (result.get("positive_sectors") or result.get("negative_sectors")):
                st.session_state["analysis"] = result
                status.update(label="💎 Phân tích hoàn tất!", state="complete", expanded=False)
            else:
                status.update(label="⚠️ AI trả về dữ liệu rỗng. Vui lòng thử lại.", state="error", expanded=True)
                st.session_state["analysis"] = None
        except Exception as e:
            status.update(label=f"❌ Lỗi: {str(e)[:100]}", state="error", expanded=True)
            st.session_state["analysis"] = None
elif not api_key:
    st.info("💡 Nhập Google API Key ở thanh bên trái để kích hoạt phân tích AI.")

analysis = st.session_state.get("analysis")

# Sentiment + summary
if analysis:
    sent = analysis.get("sentiment", "Trung lập")
    badge_cls = {"Hưng phấn": "s-greed", "Tích cực": "s-greed",
                 "Sợ hãi": "s-fear",   "Tiêu cực": "s-fear"}.get(sent, "s-neutral")
    st.markdown(f"""<div class="sent-wrap">
  <span class="sent-badge {badge_cls}">{sent}</span>
  <div class="sent-summary">{analysis.get('summary','')}</div>
  <div class="gold-advice-box">💡 <b>Tư vấn Vàng:</b> {analysis.get('gold_advice','')}</div>
</div>""", unsafe_allow_html=True)

st.divider()

# ─── 3-COLUMN LAYOUT: News | Positive | Negative ─────────────────────────────
col_news, col_pos, col_neg = st.columns([1, 1.1, 1.1], gap="large")

with col_news:
    st.markdown('<div class="sec-title">🌍 Tin Thế Giới</div>', unsafe_allow_html=True)
    for item in (news.get("world") or []):
        st.markdown(f'<div class="news-item"><span class="news-dot"></span>'
                    f'<span class="news-text">{item}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-title" style="margin-top:20px;">🇻🇳 Tin Trong Nước</div>', unsafe_allow_html=True)
    for item in (news.get("domestic") or []):
        st.markdown(f'<div class="news-item"><span class="news-dot" style="background:#22c55e"></span>'
                    f'<span class="news-text">{item}</span></div>', unsafe_allow_html=True)

with col_pos:
    st.markdown('<div class="sec-title">📈 Ngành Hưởng Lợi Tích Cực</div>', unsafe_allow_html=True)
    for s in (analysis or {}).get("positive_sectors", [])[:5]:
        chips = "".join(f'<span class="chip-pos">{t}</span>' for t in s.get("tickers", [])[:5])
        st.markdown(f"""<div class="sc-pos">
  <div class="sc-name-pos">{s.get('name','')}</div>
  <div class="sc-reason">{s.get('reason','')}</div>
  <div>{chips}</div>
</div>""", unsafe_allow_html=True)

with col_neg:
    st.markdown('<div class="sec-title">📉 Ngành Chịu Rủi Ro</div>', unsafe_allow_html=True)
    for s in (analysis or {}).get("negative_sectors", [])[:5]:
        chips = "".join(f'<span class="chip-neg">{t}</span>' for t in s.get("tickers", [])[:5])
        st.markdown(f"""<div class="sc-neg">
  <div class="sc-name-neg">{s.get('name','')}</div>
  <div class="sc-reason">{s.get('reason','')}</div>
  <div>{chips}</div>
</div>""", unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("""<div style="text-align:center;color:#334155;font-size:12px;margin-top:30px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06)">
  © 2026 Macro Dashboard | V-Macro Insights v3.0 | Dữ liệu mang tính chất tham khảo
</div>""", unsafe_allow_html=True)
