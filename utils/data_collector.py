import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _yf(symbol: str) -> dict:
    """Fetch latest close + % change from Yahoo Finance."""
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if not hist.empty:
            cur  = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else cur
            pct  = round((cur - prev) / prev * 100, 2) if prev else 0.0
            return {"value": round(cur, 2), "percent": pct}
    except Exception:
        pass
    return {"value": "N/A", "percent": 0.0}


def _vn_dnse(symbol: str) -> dict | None:
    """DNSE API fallback for VN market indices."""
    try:
        ts  = int(time.time())
        url = (f"https://api.dnse.com.vn/chart-api/v2/ohlcs/index"
               f"?symbol={symbol}&resolution=1D&from={ts-604800}&to={ts}")
        d = requests.get(url, headers=HEADERS, timeout=8).json()
        if "c" in d and d["c"]:
            cur  = float(d["c"][-1])
            prev = float(d["c"][-2]) if len(d["c"]) > 1 else cur
            return {"value": round(cur, 2), "percent": round((cur - prev) / prev * 100, 2)}
    except Exception:
        pass
    return None


# ─── 12 GLOBAL INDICATORS ─────────────────────────────────────────────────────

def get_global_indicators() -> dict:
    """
    Return dict of 12 macro indicators matching the V-Macro Insights dashboard.
    Keys: VN-Index, S&P 500, Bitcoin, DXY, USD/VND, Gold (World),
          Oil (Brent), FED Rate, VIX, US 10Y Yield, Hang Seng, Copper
    """
    YF_MAP = {
        "S&P 500":      "^GSPC",
        "Bitcoin":      "BTC-USD",
        "DXY":          "DX-Y.NYB",
        "USD/VND":      "USDVND=X",
        "Gold (World)": "GC=F",
        "Oil (Brent)":  "BZ=F",
        "FED Rate":     "^IRX",      # 13-week T-bill ≈ Fed rate proxy
        "VIX":          "^VIX",
        "US 10Y Yield": "^TNX",
        "Hang Seng":    "^HSI",
        "Copper":       "HG=F",
    }
    data = {name: _yf(sym) for name, sym in YF_MAP.items()}

    # VN-INDEX with DNSE fallback
    vni = _yf("^VNINDEX")
    if vni["value"] == "N/A":
        vni = _vn_dnse("VNINDEX") or {"value": "N/A", "percent": 0.0}
    data["VN-Index"] = vni

    return data


# ─── DOMESTIC GOLD PRICES ─────────────────────────────────────────────────────

def _clean(raw: str) -> str:
    return raw.strip().replace("\xa0", "").replace("\u202f", "").strip() if raw else "N/A"


def scrape_gold_prices_domestic() -> list[dict]:
    """
    Scrape Vietnamese domestic gold prices from multiple sources.
    Returns list of dicts: {brand, type, buy, sell}
    Priority order: SJC → BTMC → DOJI → giavang.org (PNJ/fallback)
    """
    results = []

    # ── 1. SJC ──────────────────────────────────────────────────────────────
    try:
        resp = requests.get("https://sjc.com.vn/", headers=HEADERS, timeout=12)
        soup = BeautifulSoup(resp.content, "html.parser")
        # Try to find the main gold price table
        table = soup.find("table", {"id": "gia-vang-sjc"}) or soup.find("table")
        if table:
            for row in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) >= 3:
                    name_up = cols[0].upper()
                    if any(k in name_up for k in ["MIẾNG", "VÀNG SJC", "VÀNG S."]):
                        results.append({"brand": "SJC", "type": "Vàng Miếng SJC", "buy": _clean(cols[1]), "sell": _clean(cols[2])})
                    elif any(k in name_up for k in ["NHẪN", "TRÒN"]):
                        results.append({"brand": "SJC", "type": "Nhẫn Tròn SJC", "buy": _clean(cols[1]), "sell": _clean(cols[2])})
    except Exception:
        pass

    # ── 2. BTMC ─────────────────────────────────────────────────────────────
    try:
        resp = requests.get("https://btmc.vn/", headers=HEADERS, timeout=12)
        soup = BeautifulSoup(resp.content, "html.parser")
        for row in soup.find_all("tr"):
            txt = row.get_text(" ", strip=True).upper()
            if "NHẪN TRÒN TRƠN" in txt:
                tds = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(tds) >= 5:
                    results.append({"brand": "BTMC", "type": "Nhẫn Tròn 999.9", "buy": _clean(tds[3]), "sell": _clean(tds[4])})
                    break
    except Exception:
        pass

    # ── 3. DOJI ─────────────────────────────────────────────────────────────
    try:
        resp = requests.get("https://doji.vn/gia-vang/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for row in soup.find_all("tr"):
            txt = row.get_text(" ", strip=True).lower()
            if "nhẫn" in txt and "doji" not in str([r["brand"] for r in results]):
                tds = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(tds) >= 3:
                    results.append({"brand": "DOJI", "type": "Nhẫn Tròn DOJI 24K", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                    break
    except Exception:
        pass

    # ── 4. giavang.org (aggregator — PNJ & missing sources) ──────────────────
    try:
        resp = requests.get("https://giavang.org/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        brands_found = [r["brand"] for r in results]
        for row in soup.find_all("tr"):
            txt = row.get_text(" ", strip=True).lower()
            tds = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(tds) < 3:
                continue
            if "pnj" in txt and "nhẫn" in txt and "PNJ" not in brands_found:
                results.append({"brand": "PNJ", "type": "Nhẫn PNJ 24K", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                brands_found.append("PNJ")
            elif "doji" in txt and "nhẫn" in txt and "DOJI" not in brands_found:
                results.append({"brand": "DOJI", "type": "Nhẫn Tròn DOJI 24K", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                brands_found.append("DOJI")
    except Exception:
        pass

    # ── Fallback nếu tất cả thất bại ────────────────────────────────────────
    if not results:
        results = [
            {"brand": "SJC",  "type": "Vàng Miếng SJC",   "buy": "Đang cập nhật", "sell": "Đang cập nhật"},
            {"brand": "BTMC", "type": "Nhẫn Tròn 999.9",  "buy": "Đang cập nhật", "sell": "Đang cập nhật"},
            {"brand": "DOJI", "type": "Nhẫn Tròn 24K",    "buy": "Đang cập nhật", "sell": "Đang cập nhật"},
            {"brand": "PNJ",  "type": "Nhẫn PNJ 24K",     "buy": "Đang cập nhật", "sell": "Đang cập nhật"},
        ]

    return results


# ─── MARKET NEWS ──────────────────────────────────────────────────────────────

def _scrape_cafef(url: str, limit: int = 8) -> list[str]:
    headlines = []
    try:
        soup = BeautifulSoup(requests.get(url, headers=HEADERS, timeout=10).content, "html.parser")
        for tag in soup.find_all(["h2", "h3"]):
            title = tag.get_text(strip=True)
            if len(title) > 25:
                headlines.append(title)
            if len(headlines) >= limit * 2:
                break
    except Exception:
        pass
    return list(dict.fromkeys(headlines))[:limit]


def get_market_news() -> dict:
    """
    Return {"world": [...], "domestic": [...]} with latest macro news from CafeF.
    """
    return {
        "world":    _scrape_cafef("https://cafef.vn/tai-chinh-quoc-te.chn"),
        "domestic": _scrape_cafef("https://cafef.vn/vi-mo-dau-tu.chn"),
    }
