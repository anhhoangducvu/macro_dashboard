try:
    from google import genai
except ImportError:
    genai = None
import json

import re
from datetime import datetime


class MacroAnalyzer:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Cần API Key để thực hiện phân tích.")
        if genai is None:
            raise ImportError("Thư viện 'google-genai' chưa được cài đặt. Vui lòng kiểm tra requirements.txt.")
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

NHIỆM VỤ: Phân tích sâu sắc bối cảnh vĩ mô và trả về JSON thuần (không giải thích ngoài JSON):
{{
  "sentiment": "Sợ hãi | Tiêu cực | Trung lập | Tích cực | Hưng phấn",
  "summary": "Phân tích vĩ mô cô đọng 3-5 câu bằng tiếng Việt, giải thích mối liên hệ logic giữa các chỉ số quốc tế (DXY, Brent, Yield) với VN-Index.",
  "positive_sectors": [
    {{"name": "Tên ngành", "reason": "Giải thích chi tiết 2-3 câu về lý do tại sao các biến số vĩ mô trên hỗ trợ trực tiếp cho lợi nhuận của doanh nghiệp trong ngành.", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "negative_sectors": [
    {{"name": "Tên ngành", "reason": "Giải thích chi tiết 2-3 câu về các áp lực chi phí đầu vào, tỷ giá hay cầu yếu đang trực tiếp đe dọa biên lợi nhuận của ngành.", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "gold_advice": "Lời khuyên chiến thuật cho nhà đầu tư (Mua/Bán/Giữ) dựa trên chênh lệch giá với thế giới và xu hướng tỷ giá VND."
}}

QUY TẮC:
- Phải có ĐỦ 5 ngành positive và 5 ngành negative.
- Lý do (reason) phải CHUYÊN SÂU, không ghi chung chung 'được hỗ trợ'.
- Toàn bộ bằng tiếng Việt. Mã cổ phiếu HOSE/HNX chính xác."""


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
