# Code — sinh dữ liệu kiểm thử consistency của FinTrust

Thư mục này chứa 4 script của tác giả (Yang, Ma, Zhang, ACL 2023) tạo ra **bốn bộ dữ liệu kiểm thử** từ test set
gốc, cộng 2 file Excel hỗ trợ và 1 script kiểm chứng của mình. FinTrust không huấn luyện mô hình nào; các script này
chỉ **biến đổi văn bản** để sau đó kiểm tra mô hình dự đoán có cư xử nhất quán hay không.

| Script | Phép biến đổi | Văn bản | Nhãn | Mô hình nhất quán phải… | Giải thích chi tiết |
|---|---|---|---|---|---|
| `generate_neg_consis.py` | Negation | thay từ bằng từ trái nghĩa | **lật** | **đổi** dự đoán | [`docs/generate_neg_consis.md`](../docs/generate_neg_consis.md) |
| `generate_sym_consis.py` | Symmetric | đảo thứ tự các mệnh đề | giữ | **giữ** dự đoán | [`docs/generate_sym_consis.md`](../docs/generate_sym_consis.md) |
| `generate_add_consis.py` | Additive | ghép 2 văn bản cùng nhãn | giữ | **giữ** dự đoán | [`docs/generate_add_consis.md`](../docs/generate_add_consis.md) |
| `generate_tra_consis.py` | Transitive | "we/our" → tên công ty đầu ngành | giữ | **giữ** dự đoán | [`docs/generate_tra_consis.md`](../docs/generate_tra_consis.md) |
| `verify_outputs.py` | — | so file mình sinh với file tác giả | — | — | (mục "Kiểm chứng" bên dưới) |
| `constituents-financials.xlsx` | — | danh sách S&P 500: Symbol, Name, Sector, … | — | — | dùng bởi Transitive |
| `top_company.xlsx` | — | mỗi dòng: Sector, công ty hạng 1, 2, 3 | — | — | dùng bởi Transitive |

## Định dạng dữ liệu vào

`Data/earnings_call_3days.npy` là mảng numpy **113 dòng × 4 cột**, kiểu chuỗi cố định `<U54209`
(mỗi ô tối đa 54 209 ký tự; xem mục "Hạn chế" bên dưới):

| Cột | Nội dung | Ví dụ |
|---|---|---|
| 0 | ngày earnings call | `2017-10-24` (cả test set trải từ 2017-10-24 đến 2017-12-21) |
| 1 | nhãn, **kiểu chuỗi**: `'0.0'` = giá **giảm**, `'1.0'` = giá **tăng** sau 3 ngày | `'0.0'` |
| 2 | tên công ty (không phải mã chứng khoán) | `Lockheed Martin Corp.` |
| 3 | toàn văn transcript; mỗi dòng ≈ một câu, **không có dấu chấm cuối dòng** | `Good morning, everyone` |

Test set có 67 văn bản nhãn `0.0` và 46 văn bản nhãn `1.0`; tổng 17 393 dòng (trung vị 151 dòng/văn bản,
ngắn nhất 25, dài nhất 448).

## Cách chạy

```bash
pip install numpy pandas openpyxl        # openpyxl cần để pandas đọc file .xlsx
cd FinTrust                              # thư mục gốc repo (cha của Code/)
python Code/generate_neg_consis.py       # Windows: python Code\generate_neg_consis.py
python Code/generate_sym_consis.py
python Code/generate_add_consis.py
python Code/generate_tra_consis.py
python Code/verify_outputs.py
```

* Chạy từ **bất kỳ thư mục nào** cũng được: đường dẫn được suy ra từ vị trí của file `.py`
  (`Code/` → gốc repo → `Data/`), không còn phụ thuộc vào thư mục hiện hành.
* Mặc định **đọc từ `Data/`** và **ghi vào `scratch/`** (đã nằm trong `.gitignore`).
  Mỗi file đầu ra nặng ~98 MB; ghi đè vào `Data/` sẽ làm Git coi đó là thay đổi lớn. Script từ chối ghi vào chính
  thư mục dữ liệu trừ khi bạn thêm `--force`.
* Tuỳ chọn chung: `--data-dir <thư mục>`, `--out-dir <thư mục>`.
* Riêng Transitive: `--fix-header` (xem `docs/generate_tra_consis.md`), ghi ra `tra_earnings_call_3days_fixed.npy`.

## Kiểm chứng (đã chạy)

`python Code/verify_outputs.py` so bốn file mình sinh ra với bốn file tác giả công bố trong `Data/`:

* Negation, Symmetric, Transitive: **giống từng ký tự**.
* Additive: **cùng nội dung**; script xuất các dòng theo nhóm nhãn (`0.0` trước, rồi `1.0`), còn file tác giả công bố
  đã được sắp lại theo thứ tự test set gốc (script không làm việc đó), nên phép so ghép theo (ngày, công ty).

## Mình đã sửa gì so với bản của tác giả

Chỉ phần **đường dẫn / dòng lệnh / chú thích**; logic biến đổi giữ nguyên (đó là lý do kết quả vẫn khớp).

| Thay đổi | Lý do |
|---|---|
| Đọc `Data/`, ghi `scratch/`, suy đường dẫn từ vị trí file | bản gốc dùng đường dẫn tương đối (`np.load("earnings_call_3days.npy")`), chỉ chạy được khi đứng đúng trong thư mục chứa dữ liệu, và sẽ ghi đè ngay vào đó |
| `--data-dir`, `--out-dir`, `--force` | chạy trên máy/thư mục khác; tránh ghi đè nhầm |
| Hàm `make_*` nhận tham số; phần chạy nằm sau `if __name__ == "__main__"` | để các script demo/mở rộng import lại `replace_words`… mà không tự động chạy |
| Additive: đổi tên biến `list`→`result`, `next`→`nxt`; số `512` thành `MAX_LINES` | `list`, `next` trùng tên hàm dựng sẵn của Python |
| Additive, Transitive: in **cảnh báo** khi văn bản bị cắt cụt; Transitive: in số văn bản dùng nhầm công ty | làm lộ các điểm yếu (bên dưới) mà bản gốc im lặng bỏ qua; không đổi kết quả |
| Transitive: tuỳ chọn `--fix-header` | sửa lỗi đọc Excel; **mặc định tắt** để vẫn tái hiện đúng dữ liệu tác giả |

## Hạn chế đã kiểm chứng của dữ liệu tác giả công bố

Chi tiết và số liệu trong từng file `docs/generate_*_consis.md`. Tóm tắt:

1. **Negation**: 61,9% dòng bị thay từ; nhiều thay thế làm câu sai ngữ pháp hoặc lệch nghĩa; 11/97 luật không có chiều ngược lại.
2. **Symmetric**: đảo *tất cả* mệnh đề tách bởi dấu phẩy chứ không chỉ hai phần; số dòng tăng 17 393 → 17 909.
3. **Additive**: 3/113 văn bản không ghép được (quá 512 dòng); 7/113 văn bản ghép bị **cắt cụt** do kiểu `<U54209`.
4. **Transitive**: lỗi đọc Excel khiến 25/113 văn bản (toàn bộ ngành Consumer Discretionary) dùng nhầm công ty;
   1 văn bản (Exxon Mobil) bị cắt cụt; "we're/we've…" và "we" đầu dòng không được thay.
