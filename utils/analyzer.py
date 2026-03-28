from google import genai
import json
import re
from datetime import datetime


class MacroAnalyzer:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Cần API Key để thực hiện phân tích.")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def analyze(self, indicators: dict, gold_domestic: list, news: dict) -> dict:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        clean_ind = {k: v for k, v in indicators.items() if isinstance(v.get("value"), (int, float))}

        prompt = f"""Bạn là Chuyên gia Chiến lược Vĩ mô Cấp cao tại thị trường Việt Nam.
Thời gian phân tích: {now}.

DỮ LIỆU VĨ MÔ:
1. Chỉ số thị trường: {json.dumps(clean_ind, ensure_ascii=False)}
2. Giá vàng trong nước: {json.dumps(gold_domestic, ensure_ascii=False)}
3. Tin thế giới: {" | ".join(news.get("world", [])[:5])}
4. Tin trong nước: {" | ".join(news.get("domestic", [])[:5])}

NHIỆM VỤ: Chỉ trả về JSON thuần (không markdown, không giải thích):
{{
  "sentiment": "Sợ hãi | Trung lập | Hưng phấn",
  "summary": "Phân tích vĩ mô 3-4 câu bằng tiếng Việt",
  "positive_sectors": [
    {{"name": "Tên ngành", "reason": "Lý do tích cực", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "negative_sectors": [
    {{"name": "Tên ngành", "reason": "Lý do rủi ro", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "gold_advice": "Lời khuyên về vàng"
}}

Quy tắc: ĐÚNG ĐỦ 5 ngành hưởng lợi + 5 ngành rủi ro, mỗi ngành ĐÚNG ĐỦ 5 mã cổ phiếu. Toàn bộ tiếng Việt."""

        try:
            resp = self.client.models.generate_content(model=self.model, contents=prompt)
            text = resp.text.strip()
            # Strip any markdown code fences
            text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
            return json.loads(text)
        except Exception as e:
            return {
                "sentiment": "Trung lập",
                "summary": f"Không thể kết nối AI lúc này. Lỗi: {str(e)[:120]}",
                "positive_sectors": [
                    {"name": "Ngân hàng", "reason": "Lãi suất ổn định hỗ trợ biên lợi nhuận.", "tickers": ["VCB", "BID", "CTG", "TCB", "MBB"]},
                    {"name": "Dầu khí", "reason": "Giá dầu tăng hỗ trợ doanh thu.", "tickers": ["PVS", "PVD", "GAS", "BSR", "OIL"]},
                    {"name": "Hóa chất", "reason": "Chi phí đầu vào giảm.", "tickers": ["DPM", "DCM", "BFC", "LAS", "CSV"]},
                    {"name": "Thép", "reason": "Nhu cầu xây dựng phục hồi.", "tickers": ["HPG", "HSG", "NKG", "TLH", "POM"]},
                    {"name": "Chứng khoán", "reason": "Thanh khoản thị trường cải thiện.", "tickers": ["SSI", "VND", "HCM", "VCI", "MBS"]},
                ],
                "negative_sectors": [
                    {"name": "Bất động sản", "reason": "Thanh khoản thấp, tồn kho cao.", "tickers": ["NVL", "PDR", "DIG", "HPX", "CEO"]},
                    {"name": "Hàng không", "reason": "Chi phí nhiên liệu tăng.", "tickers": ["HVN", "VJC", "AST", "NCS", "SGN"]},
                    {"name": "Thủy sản", "reason": "Nhu cầu xuất khẩu suy yếu.", "tickers": ["VHC", "ANV", "FMC", "CMX", "IDI"]},
                    {"name": "Bán lẻ", "reason": "Tiêu dùng trong nước giảm.", "tickers": ["MWG", "PNJ", "FRT", "DGW", "PET"]},
                    {"name": "Công nghệ", "reason": "Chi phí vốn tăng ảnh hưởng định giá.", "tickers": ["FPT", "CMG", "ELC", "MFS", "CTR"]},
                ],
                "gold_advice": "Quan sát thêm sự chênh lệch giữa giá vàng thế giới và trong nước.",
            }
