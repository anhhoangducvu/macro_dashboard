# 📈 Macro Finance Dashboard

A personal project to track global macro indicators, market news, and **Vietnam domestic gold prices** (SJC, DOJI, PNJ, BTMC, BTMH). The app uses AI (Gemini) to analyze market trends and provide investment insights.

## ✨ Features
- **Global Indicators**: Real-time tracking of DXY, VN-Index, S&P 500, Gold, Oil, Bitcoin, USD/VND.
- **Domestic Gold Prices**: Automated scraping for ring gold (vàng nhẫn) from 5 major brands in Vietnam.
- **AI-Powered Market Analysis**: Connects to Gemini 1.5 Flash to summarize market sentiment and identify potential sectors/stocks.
- **Modern UI**: Dark-themed, responsive dashboard designed for clarity.

## 🚀 Getting Started

### 1. Local Development
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

### 2. Deployment to Streamlit Cloud
1. Push your code to a GitHub repository.
2. Connect the repository to [Streamlit Cloud](https://share.streamlit.io).
3. **Important**: Add your Gemini API Key in `Advanced settings` -> `Secrets`:
   ```toml
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```

## 🛠 Tech Stack
- **Framework**: Streamlit
- **Data Sources**: yfinance, BeautifulSoup4, requests
- **Analysis**: Google Generative AI (Gemini 1.5 Flash)

---
© 2026 Personal Market Intelligence Project | Built for educational purposes.
