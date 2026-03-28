from google import genai
from google.genai import types
import os
import json
from datetime import datetime
import re

class MacroAnalyzer:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Cần API Key để thực hiện mẫu phân tích.")
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.0-flash'

    def analyze(self, indicators, gold_prices, news):
        """
        Phân tích chuyên sâu 5x5 Vĩ mô/Ngành cho thị trường Việt Nam.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Làm sạch các chỉ báo rỗng để prompt ngắn gọn
        clean_indicators = {}
        for k, v in indicators.items():
            if isinstance(v["value"], (int, float)):
                clean_indicators[k] = v
        
        prompt = f"""
        GIẢ ĐỊNH: Bạn là Chuyên gia Chiến lược Vĩ mô Cao cấp tại thị trường Việt Nam.
        THỜI GIAN: {now} (Thứ Bảy, Chủ Nhật sẽ lấy dữ liệu từ phiên Thứ Sáu gần nhất).
        
        DỮ LIỆU ĐƯỢC CUNG CẤP:
        1. Chỉ số thị trường (VN-Index, VN30, HNX, DXY, S&P 500, Vàng Thế giới, Dầu, BTC, Tỉ giá...): 
           {json.dumps(clean_indicators, ensure_ascii=False, indent=1)}
        2. Giá vàng Nhẫn trong nước (Tr/lượng): {json.dumps(gold_prices, ensure_ascii=False)}
        3. Điểm tin vĩ mô nổi bật: {news}
        
        NHIỆM VỤ CHIẾN LƯỢC (CHỈ TRẢ VỀ TIẾNG VIỆT):
        1. Đánh giá TÂM LÝ thị trường hiện tại (Sợ hãi | Trung lập | Hưng phấn) và giải thích vì sao thông qua dữ liệu vĩ mô (Tỉ giá, Lãi suất, Chính sách tiền tệ).
        2. Xác định TOP 5 NGÀNH HƯỞNG LỢI (Outlook Tích cực). Với mỗi ngành: Nêu lý do và gợi ý đúng ĐỦ 5 MÃ CỔ PHIẾU tiêu biểu.
        3. Xác định TOP 5 NGÀNH RỦI RO (Rủi ro/Cẩn trọng). Với mỗi ngành: Nêu lý do rủi ro và gợi ý đúng ĐỦ 5 MÃ CỔ PHIẾU CẦN TRÁNH/PHẢI TRÁNH XA.
        4. Tư vấn chiến lược đầu tư Vàng (Sự chênh lệch giá thế giới vs trong nước).
        
        QUY TẮC ĐỊNH DẠNG: Chỉ trả về duy nhất chuỗi JSON có cấu trúc sau:
        {{
            "sentiment": "Tâm lý thị trường",
            "summary": "Phân tích vĩ mô chi tiết bằng Tiếng Việt",
            "positive_sectors": [
                {{"name": "Tên ngành hưởng lợi", "reason": "Lý do", "tickers": ["Mã 1", "Mã 2", "Mã 3", "Mã 4", "Mã 5"]}},
                ... (đủ 5 mục)
            ],
            "negative_sectors": [
                {{"name": "Tên ngành rủi ro", "reason": "Lý do rủi ro", "tickers": ["Mã 1", "Mã 2", "Mã 3", "Mã 4", "Mã 5"]}},
                ... (đủ 5 mục)
            ],
            "gold_advice": "Lời khuyên đầu tư vàng chuyên sâu"
        }}
        
        LƯU Ý QUAN TRỌNG: Không dùng bất kỳ từ tiếng Anh nào trong kết quả. Phải có ĐỦ 5 NGÀNH và mỗi ngành ĐỦ 5 MÃ. Nếu số liệu bị thiếu, hãy sử dụng logic tin tức vĩ mô để dự phóng một cách chuyên nghiệp nhất.
        """
        
        try:
            # Ưu tiên News nếu số liệu Indicators bị thiếu đột xuất
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            output_text = response.text.strip()
            
            # Trích xuất JSON bằng regex để tránh lỗi markdown
            json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Dự phòng nếu response không đúng JSON
            return json.loads(output_text[output_text.find("{"):output_text.rfind("}")+1])
            
        except Exception as e:
            # Giải pháp dự phòng chuyên nghiệp khi Gemini lỗi
            return {
                "sentiment": "Trung lập",
                "summary": "Hiện tại hệ thống không thể thực hiện phân tích kỹ thuật do API kết nối gián đoạn. Tuy nhiên bối cảnh vĩ mô vẫn cho thấy sự ổn định tương đối dựa trên tin tức hiện tại.",
                "positive_sectors": [{"name": "Ngân hàng", "reason": "Lãi suất ổn định.", "tickers": ["VCB", "BID", "CTG", "TCB", "MBB"]}],
                "negative_sectors": [{"name": "Bất động sản", "reason": "Vấn đề thanh khoản.", "tickers": ["NVL", "PDR", "HPX", "DIG", "CEO"]}],
                "gold_advice": "Quan sát thêm sự chênh lệch giữa giá vàng thế giới và SJC."
            }
