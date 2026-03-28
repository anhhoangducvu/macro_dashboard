import streamlit as st
import os
from datetime import datetime
from utils.data_collector import get_global_indicators, scrape_gold_prices_domestic, get_market_news
from utils.analyzer import MacroAnalyzer
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="V-Macro Insights | Phân tích Vĩ mô Việt Nam",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
.sec-title { font-size:14px; font-weight:700; color:white; display:flex;
  align-items:center; gap:8px; margin-bottom:14px; padding-bottom:10px;
  border-bottom:1px solid rgba(255,255,255,0.07); margin-top:6px; }

/* GOLD TABLE */
.gold-wrap { background:rgba(251,191,36,.04); border:1px solid rgba(251,191,36,.18);
  border-radius:14px; padding:14px 18px; margin-bottom:24px; }
.gold-row { display:flex; justify-content:space-between; align-items:center;
  padding:9px 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:13px; }
.gold-row:last-child { border-bottom:none; }
.gold-brand { font-weight:700; color:#fbbf24; min-width:60px; }
.gold-type  { color:#64748b; font-size:12px; flex:1; padding:0 12px; }
.gold-buy   { color:#22c55e; font-weight:700; text-align:right; min-width:110px; }
.gold-sell  { color:#ef4444; font-weight:700; text-align:right; min-width:110px; }
.gold-header { font-size:11px; color:#475569; font-weight:600; letter-spacing:0.7px;
  text-transform:uppercase; display:flex; justify-content:space-between; margin-bottom:6px; }

/* NEWS */
.news-item { display:flex; gap:10px; margin-bottom:12px; align-items:flex-start; }
.news-dot  { width:5px; height:5px; border-radius:50%; background:#3b82f6; margin-top:8px; flex-shrink:0; }
.news-text { font-size:12.5px; color:#cbd5e1; line-height:1.6; }

/* SECTOR CARDS */
.sc-pos { background:rgba(34,197,94,.04); border:1px solid rgba(34,197,94,.2);
  border-left:4px solid #22c55e; border-radius:12px; padding:14px; margin-bottom:10px; }
.sc-neg { background:rgba(239,68,68,.04); border:1px solid rgba(239,68,68,.2);
  border-left:4px solid #ef4444; border-radius:12px; padding:14px; margin-bottom:10px; }
.sc-name-pos { font-size:13.5px; font-weight:700; color:#22c55e; margin-bottom:5px; }
.sc-name-neg { font-size:13.5px; font-weight:700; color:#ef4444; margin-bottom:5px; }
.sc-reason   { font-size:12px; color:#94a3b8; line-height:1.55; margin-bottom:9px; }
.chip-pos { display:inline-block; background:rgba(34,197,94,.12); color:#22c55e;
  border:1px solid rgba(34,197,94,.3); font-size:11px; font-weight:700;
  padding:2px 8px; border-radius:5px; margin:2px 4px 2px 0; }
.chip-neg { display:inline-block; background:rgba(239,68,68,.12); color:#ef4444;
  border:1px solid rgba(239,68,68,.3); font-size:11px; font-weight:700;
  padding:2px 8px; border-radius:5px; margin:2px 4px 2px 0; }

/* SENTIMENT */
.sent-wrap { border-radius:14px; padding:18px 22px; margin-bottom:22px;
  background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); }
.sent-badge { display:inline-block; padding:4px 16px; border-radius:20px;
  font-size:12px; font-weight:700; color:white; margin-bottom:10px; }
.s-greed   { background:#22c55e; }
.s-fear    { background:#ef4444; }
.s-neutral { background:#f59e0b; }
.sent-summary { font-size:13.5px; color:#cbd5e1; line-height:1.7; margin-bottom:10px; }
.gold-advice-box { background:rgba(59,130,246,.08); border-left:4px solid #3b82f6;
  border-radius:0 8px 8px 0; padding:10px 14px; font-size:13px; color:#93c5fd; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")

    # API key: secrets → env → manual input
    api_key = ""
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        api_key = st.text_input("🔑 Google API Key:", type="password", placeholder="AIza...")

    if st.button("🔄 Làm mới dữ liệu", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("analysis", None)
        st.rerun()

    st.divider()
    st.caption("**V-Macro Insights v3.0**\nDữ liệu: Yahoo Finance, SJC, BTMC, DOJI, CafeF\n⚠️ Chỉ mang tính chất tham khảo – không phải khuyến nghị đầu tư.")


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


with st.spinner("⏳ Đang tải dữ liệu thị trường..."):
    indicators = load_indicators()
    gold_data  = load_gold()
    news       = load_news()


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
st.markdown('<div class="sec-title">🏅 Giá Vàng Trong Nước (Triệu đồng/lượng)</div>', unsafe_allow_html=True)

gold_html = """<div class="gold-wrap">
  <div class="gold-header">
    <span>Thương hiệu</span><span>Loại</span>
    <span style="min-width:110px;text-align:right">Mua vào</span>
    <span style="min-width:110px;text-align:right">Bán ra</span>
  </div>"""
for g in gold_data:
    gold_html += f"""<div class="gold-row">
  <span class="gold-brand">{g['brand']}</span>
  <span class="gold-type">{g['type']}</span>
  <span class="gold-buy">▲ {g['buy']}</span>
  <span class="gold-sell">▼ {g['sell']}</span>
</div>"""
gold_html += "</div>"
st.markdown(gold_html, unsafe_allow_html=True)


# ─── AI ANALYSIS ─────────────────────────────────────────────────────────────
if api_key and "analysis" not in st.session_state:
    with st.status("🧠 AI đang phân tích dữ liệu vĩ mô…", expanded=True) as status:
        try:
            st.session_state["analysis"] = MacroAnalyzer(api_key).analyze(indicators, gold_data, news)
            status.update(label="💎 Phân tích hoàn tất!", state="complete", expanded=False)
        except Exception as e:
            status.update(label=f"❌ Lỗi: {e}", state="error", expanded=True)
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
  © 2026 TEXO Engineering | V-Macro Insights v3.0 | Dữ liệu chỉ mang tính chất tham khảo
</div>""", unsafe_allow_html=True)
