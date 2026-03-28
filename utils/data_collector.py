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
    Scrape Vietnamese domestic gold prices from multiple reliable sources.
    Priority: Rings (BTMC, BTMH) then Bars (SJC, DOJI, PNJ).
    """
    results = []

    # ── 1. BTMC (Bảo Tín Minh Châu) - Ring ──────────────────────────────────
    try:
        resp = requests.get("https://btmc.vn/", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for row in soup.find_all("tr"):
            txt = row.get_text(" ", strip=True).upper()
            if ("RỒNG THĂNG LONG" in txt or "NHẪN TRÒN" in txt) and "999.9" in txt:
                tds = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(tds) >= 4:
                    results.append({"brand": "Minh Châu", "type": "Nhẫn Tròn VRTL", "buy": _clean(tds[-2]), "sell": _clean(tds[-1])})
                    break
    except Exception: pass

    # ── 2. BTMH (Bảo Tín Mạnh Hải) - Ring ───────────────────────────────────
    try:
        resp = requests.get("https://baotinmanhhai.vn/gia-vang", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for row in soup.find_all("tr"):
            txt = row.get_text(" ", strip=True).upper()
            if "NHẪN" in txt and ("MẠNH HẢI" in txt or "GIA BẢO" in txt):
                tds = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(tds) >= 3:
                    results.append({"brand": "Mạnh Hải", "type": "Nhẫn Kim Gia Bảo", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                    break
    except Exception: pass

    # ── 3. DOJI, PNJ, SJC (Via tygia.vn - highly stable) ──────────────────────
    try:
        resp = requests.get("https://tygia.vn/gia-vang", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        for row in soup.find_all("tr"):
            tds = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(tds) < 3: continue
            name = tds[0].upper()
            if "SJC" in name and ("HỒ CHÍ MINH" in name or "SÀI GÒN" in name or "SJC" == name.strip()):
                results.append({"brand": "SJC", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
            elif "DOJI" in name and ("HÀ NỘI" in name or "SÀI GÒN" in name):
                results.append({"brand": "DOJI", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
            elif ("PNJ" in name or "PHÚ NHUẬN" in name) and "HÀ NỘI" in name:
                results.append({"brand": "PNJ", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
    except Exception: pass

    # ── 4. Fallback for large brands (Via giavang.org) ───────────────────────
    if len(results) < 4:
        try:
            resp = requests.get("https://giavang.org/", headers=HEADERS, timeout=10)
            soup = BeautifulSoup(resp.content, "html.parser")
            for row in soup.find_all("tr"):
                tds = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(tds) < 3: continue
                txt = " ".join(tds).upper()
                if "SJC" in txt and "HÀ NỘI" in txt:
                     results.append({"brand": "SJC", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                if "DOJI" in txt and "HÀ NỘI" in txt:
                    results.append({"brand": "DOJI", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
                if "PNJ" in txt and "HÀ NỘI" in txt:
                    results.append({"brand": "PNJ", "type": "Vàng Miếng SJC", "buy": _clean(tds[1]), "sell": _clean(tds[2])})
        except Exception: pass

    # Final cleanup & Deduplication
    final = []
    seen = set()
    # Priority order: BTMC, BTMH, SJC, DOJI, PNJ
    for brand_target in ["Minh Châu", "Mạnh Hải", "SJC", "DOJI", "PNJ"]:
        for r in results:
            if r['brand'] == brand_target:
                key = f"{r['brand']}-{r['type']}"
                if key not in seen:
                    final.append(r)
                    seen.add(key)
                    break 

    if not final:
        return [
            {"brand": "Minh Châu", "type": "Nhẫn Tròn VRTL", "buy": "---", "sell": "---"},
            {"brand": "Mạnh Hải", "type": "Nhẫn Kim Gia Bảo", "buy": "---", "sell": "---"},
            {"brand": "SJC",  "type": "Vàng Miếng SJC",   "buy": "---", "sell": "---"},
        ]
    return final[:6]


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
