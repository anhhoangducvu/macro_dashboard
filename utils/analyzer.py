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
        self.model = "gemini-1.5-flash"


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
    {{"name": "Tên ngành", "reason": "PHẢI GIẢI THÍCH CHI TIẾT 2-4 câu: Tại sao các yếu tố vĩ mô hiện tại (USD, Lãi suất, Giá hàng hóa...) lại giúp ngành này tăng trưởng lợi nhuận? Không được ghi chung chung.", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "negative_sectors": [
    {{"name": "Tên ngành", "reason": "PHẢI GIẢI THÍCH CHI TIẾT 2-4 câu: Những rủi ro cụ thể nào (chi phí vốn, tỷ giá, cầu yếu...) đang trực tiếp bào mòn biên lợi nhuận của ngành? Không được ghi ngắn.", "tickers": ["MÃ1","MÃ2","MÃ3","MÃ4","MÃ5"]}}
  ],
  "gold_advice": "Lời khuyên chiến thuật chi tiết cho nhà đầu tư (Mua/Bán/Giữ) dựa trên chênh lệch giá và xu hướng tỷ giá."
}}

QUY TẮC BẮT BUỘC:
- Phần 'reason' KHÔNG ĐƯỢC ngắn hơn 2 câu. Phải có tính giải thích chuyên môn.
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
            # Enhanced fallback with more detailed reasoning
            return {
                "sentiment": "Trung lập",
                "summary": f"Đang sử dụng dữ liệu mặc định do AI đạt giới hạn (429). Lỗi: {str(e)[:50]}",
                "positive_sectors": [
                    {"name": "Công nghệ (FPT)", "reason": "Xu hướng chuyển đổi số toàn cầu và nhu cầu AI tăng mạnh giúp duy trì tăng trưởng hai chữ số bất chấp vĩ mô.", "tickers": ["FPT", "CMG", "ELC", "CTR"]},
                    {"name": "Xuất khẩu & Khu CN", "reason": "Tỷ giá USD/VND neo cao hỗ trợ các doanh nghiệp có doanh thu bằng USD và thu hút dòng vốn FDI dịch chuyển.", "tickers": ["VHC", "ANV", "KBC", "IDC", "SZC"]},
                    {"name": "Điện & Năng lượng", "reason": "Nhu cầu tiêu thụ điện phục hồi cùng việc triển khai Quy hoạch điện VIII tạo nền móng cho các dự án lớn.", "tickers": ["POW", "PC1", "GEG", "REE", "ASM"]},
                    {"name": "Ngân hàng Thương mại", "reason": "Khả năng quản trị chi phí vốn tốt và dư địa tăng trưởng tín dụng cao trong giai đoạn phục hồi kinh tế.", "tickers": ["VCB", "ACB", "TCB", "MBB", "HDB"]},
                    {"name": "Hàng tiêu dùng thiết yếu", "reason": "Nhu cầu ổn định và khả năng chuyển chi phí sang người tiêu dùng tốt trong môi trường lạm phát vừa phải.", "tickers": ["MSN", "VNM", "SAB", "DBC", "PAN"]},
                ],
                "negative_sectors": [
                    {"name": "Bất động sản dân dụng", "reason": "Áp lực trái phiếu đến hạn và khó khăn trong phê duyệt pháp lý dự án kéo dài làm chậm dòng tiền.", "tickers": ["NVL", "PDR", "DIG", "DXG", "CEO"]},
                    {"name": "Vật liệu xây dựng", "reason": "Thị trường bất động sản chưa phục hồi cùng chi phí năng lượng (than, điện) đầu vào cao bào mòn biên lợi nhuận.", "tickers": ["HPG", "HSG", "NKG", "HT1", "BCC"]},
                    {"name": "Vận tải quốc tế", "reason": "Chi phí nhiên liệu biến động và nhu cầu vận chuyển toàn cầu suy yếu ảnh hưởng đến giá cước.", "tickers": ["GMD", "HAH", "VOS", "PVT", "VSC"]},
                    {"name": "Dệt may & Da giày", "reason": "Đơn hàng từ các thị trường xuất khẩu chính (Mỹ, EU) hồi phục chậm do thắt chặt chi tiêu.", "tickers": ["TNG", "MSH", "VGT", "GIL", "STK"]},
                    {"name": "Chứng khoán", "reason": "Thị trường đi ngang và thanh khoản sụt giảm ảnh hưởng trực tiếp đến mảng môi giới và tự doanh.", "tickers": ["SSI", "VND", "HCM", "VCI", "MBS"]},
                ],
                "gold_advice": "Hành động: Quan sát thêm chênh lệch với giá vàng thế giới. Ưu tiên vàng nhẫn khi tỷ giá USD/VND biến động mạnh.",
            }
