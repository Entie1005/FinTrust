# FinTrust — bản học tập (Predictive Data Analytics, báo cáo giữa kỳ)

Repo này là bản sao học tập của [yingpengma/FinTrust](https://github.com/yingpengma/FinTrust),
kèm ghi chú phân tích code và thực nghiệm mở rộng của **Lưu Đạt Tuấn Nghĩa**.

**Bài báo:** Linyi Yang, Yingpeng Ma, Yue Zhang. *Measuring Consistency in Text-based Financial
Forecasting Models.* ACL 2023. DOI: [10.18653/v1/2023.acl-long.769](https://aclanthology.org/2023.acl-long.769/)

## FinTrust là gì (và không phải là gì)

FinTrust **không phải một mô hình NLP mới**. Đó là một **bộ kiểm thử (evaluation tool)** cho các mô hình
dự đoán biến động giá cổ phiếu từ văn bản earnings call. Ý tưởng giống một bộ unit test:
biến đổi đầu vào theo quy tắc **không làm đổi ý nghĩa tài chính** (hoặc đổi ý nghĩa theo cách đoán trước được),
rồi kiểm tra xem dự đoán của mô hình có đổi/giữ đúng như một người hợp lý kỳ vọng hay không.
Bốn phép biến đổi: **Negation, Symmetric, Additive, Transitive**.
Chi tiết trong [`docs/paper_summary.md`](docs/paper_summary.md).

## Cấu trúc repo

| Đường dẫn | Nguồn | Nội dung |
|---|---|---|
| `Code/` | tác giả | 4 script `generate_*_consis.py` sinh dữ liệu kiểm thử; 2 file Excel dùng cho phép Transitive |
| `Data/` | tác giả | test set 113 văn bản và 4 bộ biến đổi (file `.npy`, ~98 MB/file) |
| `Measuring Consistency ... .pdf` | tác giả | bản PDF bài báo |
| `README_upstream.md` | tác giả | README gốc của repo (giữ nguyên, có BibTeX) |
| `docs/` | mình | ghi chú học tập (hiện có: `paper_summary.md`; các ghi chú khác bổ sung theo tiến độ bên dưới) |

## Nguồn và giấy phép

- Code, dữ liệu và bài báo thuộc về nhóm tác giả. Repo gốc **không có file `LICENSE`**; phần *Ethics Statement*
  của bài báo nêu code và dữ liệu được công bố theo giấy phép **CC-BY-NC-SA**.
- Repo này chỉ dùng cho **mục đích học tập, phi thương mại**. Khi dùng lại, hãy trích dẫn bài báo
  (BibTeX trong `README_upstream.md`).
- Dữ liệu gốc của earnings call do [Qin & Yang (ACL 2019)](https://github.com/GeminiLn/EarningsCall_Dataset) công bố.

## Tiến độ

- [x] Tạo repo, giữ liên kết `upstream` tới repo tác giả
- [x] README và tóm tắt bài báo
- [ ] Phân tích từng script: `generate_neg_consis`, `generate_sym_consis`, `generate_add_consis`, `generate_tra_consis`
- [ ] Demo minh hoạ 4 phép biến đổi trên dữ liệu thật
- [ ] Mở rộng: áp luật Negation lên transcript NASDAQ
- [ ] Chuẩn bị slide giữa kỳ (≤ 15 slide, 10 phút trình bày + 5 phút hỏi đáp)
