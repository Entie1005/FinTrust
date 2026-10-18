# Tóm tắt bài báo FinTrust

> *Measuring Consistency in Text-based Financial Forecasting Models* — Yang, Ma, Zhang, ACL 2023.
> Số liệu bên dưới lấy trực tiếp từ các Bảng 1–4 của bài báo (bản PDF có trong repo).

## 1. Một câu

Các mô hình dự đoán giá cổ phiếu từ văn bản chỉ được chấm bằng độ chính xác và lợi nhuận, chưa ai kiểm tra
chúng có **suy luận nhất quán** hay không; bài báo đề xuất **FinTrust**, một công cụ đánh giá tính nhất quán,
và cho thấy các mô hình hiện có nhất quán rất kém.

## 2. Tính nhất quán (consistency) là gì

Một mô hình **nhất quán** khi dự đoán của nó **không đổi** (hoặc **đổi đúng như kỳ vọng**) trước các thay đổi đầu vào
mà con người xem là *giữ nguyên hoặc đảo ngược ý nghĩa một cách đoán trước được*.
Khác với *accuracy* (đúng bao nhiêu % so với nhãn thật) và khác với tấn công đối kháng (adversarial attack,
cố tình đánh lừa mô hình): ở đây phép biến đổi được thiết kế để **bảo toàn quan hệ logic**.
Tinh thần gần với CheckList (Ribeiro et al., 2020), công trình mà bài báo có trích dẫn.

## 3. Bốn phép biến đổi

| Phép biến đổi | Thao tác trên văn bản | Mô hình nhất quán phải… | Điểm (Consis) tính khi | Code |
|---|---|---|---|---|
| **Negation** | Thay từ bằng từ trái nghĩa theo bộ luật cố định | **đổi** dự đoán: f(x)=tăng ⇔ f(¬x)=giảm | f(x) **≠** f(x′) | `generate_neg_consis.py` |
| **Symmetric** | Đảo thứ tự các phần của câu | **giữ** dự đoán: f(Sp1,Sp2)=f(Sp2,Sp1) | f(x) = f(x′) | `generate_sym_consis.py` |
| **Additive** | Ghép hai văn bản **cùng nhãn** | **giữ** dự đoán cho x, y và x+y | f(x) = f(x′) | `generate_add_consis.py` |
| **Transitive** | Thay "we/our" bằng tên công ty đứng đầu cùng ngành | **giữ** dự đoán: f(x)=f(x′) | f(x) = f(x′) | `generate_tra_consis.py` |

Điểm tổng: **Consis = (ConsisN + ConsisS + ConsisA + ConsisT) / 4** (Eq. 6), mỗi thành phần là tỉ lệ mẫu trong
test set mà mô hình cư xử đúng kỳ vọng (Eq. 7).

## 4. Hai cách đánh giá (Setup)

- **Setup 1 — Representation:** đo "thiên kiến ngầm" của mô hình ngôn ngữ tiền huấn luyện (BERT, RoBERTa, DistilBERT, FinBERT)
  bằng bài cloze: che một từ, so xác suất mô hình gán cho "increased" và "decreased". (Bảng 1)
- **Setup 2 — Behavior:** đo các mô hình dự đoán đã huấn luyện (HTML, MRDM, Event, XGBoost) trên 4 bộ dữ liệu biến đổi
  qua Accuracy/F1/MCC (Bảng 2), mô phỏng giao dịch (Bảng 3) và điểm Consis (Bảng 4).

Tách hai setup để biết lỗi nằm ở **biểu diễn ngôn ngữ** hay ở **tầng dự đoán** phía trên.

## 5. Bài toán và dữ liệu

- **Bài toán:** phân loại nhị phân, giá đóng cửa **tăng hay giảm** sau n ngày (n = 3, 7, 15, 30) dựa trên transcript earnings call.
- **Dữ liệu:** 576 transcript earnings call của các công ty S&P 500 (Qin & Yang, 2019; nguồn Seeking Alpha) cùng giá đóng cửa
  từ Yahoo Finance (01/01/2017 – 31/01/2018) để gán nhãn.
- **Chia tập:** train/val/test = 7:1:2 **theo thứ tự thời gian** (tránh dùng thông tin tương lai để dự đoán quá khứ).
- **Test set mở rộng:** mỗi mẫu test gốc sinh thêm 4 mẫu biến đổi, nên bộ đánh giá lớn gấp 4 lần test set gốc.
  Trong repo, test set gốc có **113 văn bản**.

## 6. Kết quả chính

- **PLM (Bảng 1):** consistency chỉ 70.13%–82.7% ở cài đặt +/+; PLM kém hơn khi gặp token tiêu cực
  (trung bình 63.91% so với 86.09% ở token tích cực). Mô hình lớn hơn nhất quán hơn (BERT-base 71.33% → BERT-large 75.67%);
  RoBERTa-large cao nhất (82.70% / 76.67% / 88.72% ở ba cài đặt).
- **Dự đoán (Bảng 2):** sau FinTrust, Accuracy trung bình giảm ở cả 4 mô hình
  (HTML 0.546→0.521, MRDM 0.555→0.504, Event 0.542→0.512, XGBoost 0.515→0.507); một số kết quả
  thấp hơn đoán ngẫu nhiên, nhất là kỳ hạn 3 ngày.
- **Giao dịch (Bảng 3):** Buy-all đạt Profit Ratio 3.681. HTML (3.752) và Event (3.720) vượt Buy-all, nhưng sau FinTrust tụt còn
  3.359 và 3.535, tức **thấp hơn Buy-all**. MRDM giảm mạnh nhất (−32% lợi nhuận, −43% Sharpe).
  Lợi nhuận XGBoost *tăng* (−0.515 → 0.296) nhưng vẫn kém xa Buy-all; tác giả cho rằng không có giá trị tham khảo.
- **Consis (Bảng 4):** Event cao nhất ở 3/4 kỳ hạn. **Negation consistency của mọi mô hình rất thấp** (0.009–0.354):
  mô hình thường giữ nguyên dự đoán dù ý nghĩa văn bản đã bị lật.
- **Accuracy ≠ Consistency:** hệ số Pearson giữa Consis và Accuracy chỉ **0.314**, nên Consis là chỉ số bổ sung, không thừa.

## 7. Kiểm định của tác giả

- 2 người gán nhãn (tác giả) kiểm tra 40 mẫu và 160 mẫu biến đổi: Inter-Annotator Agreement **0.98**,
  điểm consistency trung bình của con người **0.975** → phép biến đổi giữ được ý nghĩa trong đa số trường hợp.
- Kiểm định t-test trên 10 lần chạy, p < 0.05 cho mức giảm hiệu năng.

## 8. Hạn chế

**Do tác giả nêu:** chỉ dùng earnings call (chưa có tin tức, mạng xã hội); mô phỏng giao dịch chưa tính phí giao dịch;
cách đánh giá consistency cho mô hình ngôn ngữ lớn (LLM) vẫn là câu hỏi mở.

**Câu hỏi mình sẽ kiểm tra bằng cách chạy lại code (sẽ ghi vào `docs/` ở các bước sau):** các luật biến đổi
có thật sự giữ/đảo đúng ý nghĩa như bài báo nói không (human eval báo cáo 0.975)?

## 9. Ánh xạ bài báo ↔ repo

| Khái niệm trong bài báo | Nằm ở đâu trong repo |
|---|---|
| Test set gốc (7:1:2, phần 20% cuối) | `Data/earnings_call.npy` (113×3: ngày, công ty, văn bản) |
| Nhãn tăng/giảm sau 3, 7, 15, 30 ngày | `Data/stock_movement_{3,7,15,30}days.npy` |
| Test set có nhãn (ngày 3 ngày) | `Data/earnings_call_3days.npy` (113×4: ngày, **nhãn**, công ty, văn bản) |
| Bốn bộ dữ liệu biến đổi | `Data/{neg,sym,add,tra}_earnings_call_3days.npy` |
| Sinh dữ liệu biến đổi | `Code/generate_{neg,sym,add,tra}_consis.py` |
| Danh sách ngành S&P 500 và công ty đầu ngành | `Code/constituents-financials.xlsx`, `Code/top_company.xlsx` |
| Huấn luyện/đánh giá mô hình (HTML, MRDM, Event, XGBoost) | **không có trong repo** (repo chỉ cung cấp dữ liệu và công cụ sinh dữ liệu) |

## 10. Thuật ngữ nhanh

- **PLM (pre-trained language model):** mô hình ngôn ngữ tiền huấn luyện như BERT.
- **Cloze / masked token prediction:** che một từ trong câu và để mô hình đoán từ đó.
- **MCC (Matthews correlation coefficient):** thước đo phân loại nhị phân bền hơn Accuracy khi hai lớp lệch nhau.
- **Profit Ratio / Sharpe Ratio:** lợi nhuận trên vốn đầu tư / lợi nhuận điều chỉnh theo rủi ro.
- **Buy-all:** chiến lược mua tất cả cổ phiếu, dùng làm mốc so sánh đơn giản.
