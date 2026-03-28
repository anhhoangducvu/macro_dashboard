import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import re
import time

def get_vn_index_robust(symbol="VNINDEX"):
    """
    Yahoo Finance priority with multiple fallback sources for VN market.
    """
    # 1. Yahoo Finance (User preferred)
    try:
        yf_sym = "^VNINDEX" if symbol == "VNINDEX" else ("^VN30" if symbol == "VN30" else "^HNX")
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period="5d")
        if not hist.empty:
            current = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
            pct = ((current - prev) / prev * 100) if prev != 0 else 0
            return {"value": round(current, 2), "percent": round(pct, 2)}
    except:
        pass

    # 2. DNSE API (Robust Fallback)
    try:
        s_code = symbol.replace("^", "").upper()
        now_ts = int(time.time())
        start_ts = now_ts - (7 * 24 * 3600)
        url = f"https://api.dnse.com.vn/chart-api/v2/ohlcs/index?symbol={s_code}&resolution=1D&from={start_ts}&to={now_ts}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        api_data = resp.json()
        if 'c' in api_data and len(api_data['c']) > 0:
            current = float(api_data['c'][-1])
            prev = float(api_data['c'][-2]) if len(api_data['c']) > 1 else current
            pct = ((current - prev) / prev * 100) if prev != 0 else 0
            return {"value": round(current, 2), "percent": round(pct, 2)}
    except:
        pass

    # 3. VnExpress Widget Fallback
    try:
        url = f"https://vne-finance.vnecdn.net/v1/widget/stock?symbol={symbol}"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        vne_data = resp.json()
        if 'data' in vne_data and symbol in vne_data['data']:
            node = vne_data['data'][symbol]
            return {"value": float(node['price']), "percent": float(node['percent'])}
    except:
        pass

    return {"value": "N/A", "percent": 0.0}

def get_global_indicators():
    """
    Fetch global macro indicators with Yahoo Finance Priority.
    """
    symbols = {
        "VN-Index": "VNINDEX", 
        "VN30-Index": "VN30",
        "HNX-Index": "HNX",
        "DXY": "DX-Y.NYB",
        "S&P 500": "^GSPC",
        "Gold (World)": "GC=F",
        "Oil (WTI)": "CL=F",
        "Bitcoin": "BTC-USD",
        "USD/VND": "VND=X",
        "US 10Y Yield": "^TNX"
    }

    data = {}
    for name, symbol in symbols.items():
        if name in ["VN-Index", "VN30-Index", "HNX-Index"]:
            data[name] = get_vn_index_robust(symbol)
        else:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if not hist.empty:
                    current = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
                    pct = ((current - prev)/prev * 100) if prev != 0 else 0
                    data[name] = {"value": round(current, 2), "percent": round(pct, 2)}
                else:
                    data[name] = {"value": "N/A", "percent": 0}
            except:
                data[name] = {"value": "Err", "percent": 0}
    return data

def scrape_gold_prices():
    """
    Scrape domestic gold prices for specific brands requested by the user.
    """
    results = {
        "PNJ": {"buy": "N/A", "sell": "N/A"}, 
        "SJC": {"buy": "N/A", "sell": "N/A"},
        "Bảo Tín Minh Châu": {"buy": "N/A", "sell": "N/A"},
        "Mạnh Hải": {"buy": "N/A", "sell": "N/A"}
    }
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    # 1. PNJ & SJC (from giavang.org - aggregated)
    try:
        resp = requests.get("https://giavang.org/", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        rows = soup.find_all("tr")
        for row in rows:
            txt = row.get_text().lower()
            if "nhẫn" in txt:
                if "pnj" in txt:
                    tds = row.find_all("td")
                    if len(tds) >= 3: results["PNJ"] = {"buy": tds[1].text.strip(), "sell": tds[2].text.strip()}
                if "sjc" in txt:
                    tds = row.find_all("td")
                    if len(tds) >= 3: results["SJC"] = {"buy": tds[1].text.strip(), "sell": tds[2].text.strip()}
    except: pass

    # 2. Bảo Tín Minh Châu (Direct)
    try:
        resp = requests.get("https://btmc.vn/", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        # Direct search for the Nhẫn Tròn Trơn row
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                if "NHẪN TRÒN TRƠN" in row.get_text().upper():
                    tds = row.find_all("td")
                    if len(tds) >= 5:
                        # BTMC table usually has Buy at index 3 and Sell at index 4 (0-indexed)
                        results["Bảo Tín Minh Châu"] = {"buy": tds[3].text.strip(), "sell": tds[4].text.strip()}
                        break
    except: pass

    # 3. Bảo Tín Mạnh Hải (Direct)
    try:
        resp = requests.get("https://baotinmanhhai.vn/gia-vang-hom-nay", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        rows = soup.find_all("tr")
        for row in rows:
            if "Nhẫn Tròn ép vỉ" in row.get_text():
                tds = row.find_all("td")
                if len(tds) >= 3:
                    results["Mạnh Hải"] = {"buy": tds[1].text.strip(), "sell": tds[2].text.strip()}
                    break
    except: pass

    return results

def get_market_news():
    """
    Get latest headlines from CafeF macro section.
    """
    news = []
    try:
        resp = requests.get("https://cafef.vn/vi-mo-dau-tu.chn", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")
        items = soup.find_all("h3")
        for i in items[:15]:
            title = i.get_text().strip()
            if len(title) > 20: news.append(title)
    except: pass
    return list(set(news))[:20]
