---
name: vn-stock-oversell-fair-price-screen
description: Multi-factor screen for Vietnamese stocks in oversell (RSI<35, MFI<40) or fair price (RSI 45-55) zones with P/E valuation, 52w position, NN flow confirmation, and trade setup. Now expanded to handle missing NN data and distinguish oversell from fair price zones.
---
# vn-stock-oversell-fair-price-screen

## MỤC ĐÍCH
Screen các cổ phiếu Việt Nam đang ở vùng giá hợp lý (fair price) hoặc quá bán (super oversell) với xác nhận từ yếu tố kỹ thuật, cơ bản và dòng tiền nước ngoài.

## BƯỚC 1: SCREEN VỚI TIÊU CHUẨN KỸ THUẬT

### Super Oversell (Mua mạnh)
- RSI(14) < 35
- MFI(14) < 40
- Giá cách đáy 52 tuần < 5%

### Fair Price (Vùng giá hợp lý)
- RSI(14) từ 45-55
- MFI(14) từ 40-60
- Giá cách đáy 52 tuần < 15%

### Lọc bổ sung
- P/E < 15x (ưu tiên P/E thấp nhất)
- P/B < 3x
- ROE > 10%

## BƯỚC 2: XÁC NHẬN YẾU TỐ CƠ BẢN

- So sánh P/E ngành: chỉ giữ lại cổ phiếu có P/E thấp hơn trung bình ngành ≥ 20%
- Đánh giá xu hướng lợi nhuận: EPS tăng trưởng dương 4 quý gần nhất
- Kiểm tra dividend yield: > 3% là điểm cộng thêm

## BƯỚC 3: XÁC NHẬN DÒNG TIỀN NN (QUAN TRỌNG)

- **Có đủ dữ liệu NN:** Chỉ khuyến nghị MUa khi có xác nhận dòng tiền nước ngoài vào (mua ròng ≥ 3 phiên gần nhất)
- **Không đủ dữ liệu NN:** Chuyển thành WATCH ONLY — không khuyến nghị mua do thiếu xác nhận flow
- **NN đang bán:** Tránh — cho dù technical oversell

## BƯỚC 4: PHÂN BIỆT OVERSELL vs FAIR PRICE

| Zone | RSI | MFI | Ý nghĩa |
|------|-----|-----|---------|
| Super Oversell | < 35 | < 40 | Đáy cục bộ, chuẩn bị rebound mạnh |
| Fair Price | 45-55 | 40-60 | Vùng giá trị, an toàn cho dài hạn |
| Oversell nhưng KHÔNG fair price | 35-45 | < 40 | Chỉ oversell về chart, không có giá trị cơ bản |

**Quy tắc:** DSC có RSI 47 + MFI 20 = vẫn là oversell, không phải fair price do MFI quá thấp.

## BƯỚC 5: TÍNH TOAN R/R RATIO

```
Entry = vùng giá hiện tại
SL = đáy 52 tuần hoặc -5% từ entry (chọn mức nào lớn hơn)
TP1 = +7% (1:1)
TP2 = +12% (1:2)
```

- **R/R ≥ 2:1:** Đạt ngưỡng — khuyến nghị Mua
- **R/R < 2:1:** Không đạt — chuyển Watch hoặc chờ pullback sâu hơn

## BƯỚC 6: ĐÁNH GIÁ CATALYST

- **Catalyst rõ ràng:** Sự kiện sắp tới (AGM, tăng vốn, M&A, chính sách ngành) trong 1-3 tháng
- **Không có catalyst:** Trừ khi oversell cực mạnh (RSI < 25), không ưu tiên

## OUTPUT: ACTION TABLE

| Stock | Zone | RSI | MFI | P/E | NN Flow | R/R | Catalyst | Action | Entry | SL | TP |
|-------|------|-----|-----|-----|--------|-----|----------|--------|-------|-----|-----|
| DGC | Super Oversell | 33 | 19 | 6.5 | ⛔ Thiếu | 3.3:1 | AGM 09/04 | **WATCH** | 44,500-45,000 | 43,500 | 48,000/50,000 |

**Quy tắc quan trọng:** Khi thiếu dữ liệu NN flow → chuyển thành WATCH ONLY, không khuyến nghị mua cho dù mọi tiêu chuẩn khác đạt.

---

## LƯU Ý SỬ DỤNG

- Chạy screen hàng tuần hoặc khi thị trường giảm mạnh
- Ưu tiên cổ phiếu có đủ cả 3 yếu tố: technical oversell + cơ bản tốt + NN flow xác nhận
- Khi thiếu 1 yếu tố → giảm mức ưu tiên hoặc chuyển watch