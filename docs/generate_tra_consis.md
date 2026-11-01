# `generate_tra_consis.py` — phép biến đổi Transitive

> Tóm tắt một câu: với mỗi transcript, tìm **công ty đứng đầu cùng ngành** (sector) với công ty đó, rồi thay các từ "we/our"
> trong văn bản bằng tên công ty ấy. Nhãn **giữ nguyên**; mô hình nhất quán phải **giữ dự đoán**.
> *Script này có một lỗi đọc file Excel đã kiểm chứng, ảnh hưởng 25/113 văn bản (mục 5).*

## 1. Vì sao có phép này (đối chiếu bài báo, mục 3.1 và Phụ lục A)

Bài báo định nghĩa *transitive consistency*: nhận định về một công ty cũng phản ánh trong công ty đầu ngành cùng sector.
Ví dụ ở Phụ lục A: Nektar Therapeutics tạo niềm tin sau earnings call (cổ phiếu tăng 79,43% trong tháng sau) và Johnson & Johnson, công ty
đầu ngành Health Care, cũng tăng 1,91% cùng kỳ.
Vì vậy nếu thay "we/our" bằng tên công ty đầu ngành mà ý nghĩa tài chính coi như không đổi, mô hình phải dự đoán như cũ.

Ví dụ của bài báo (sector Information Technology, công ty đầu ngành Apple Inc.):
*"we believe that our products can bring convenience…"* → *"Apple Inc. believe that Apple Inc.'s products can bring convenience…"*.

## 2. Đầu vào và đầu ra

| | Tệp | Nội dung |
|---|---|---|
| Vào | `Data/earnings_call_3days.npy` | 113 × 4: ngày, nhãn, tên công ty, văn bản |
| Vào | `Code/constituents-financials.xlsx` | 512 công ty S&P 500, 14 cột: `Symbol, Name, Sector, Price, …`; script chỉ dùng `Name` (cột [1]) và `Sector` (cột [2]) |
| Vào | `Code/top_company.xlsx` | 11 ngành; mỗi dòng: Sector, công ty hạng 1, hạng 2, hạng 3 |
| Ra | `scratch/tra_earnings_call_3days.npy` | cùng cấu trúc; nhãn giữ nguyên, văn bản đã thay "we/our" và viết thường |

## 3. Đọc code từng phần

Với mỗi văn bản `i = [ngày, nhãn, công ty, văn bản]`:

1. **Tìm ngành**: duyệt `constituents-financials.xlsx`, hàng nào có `Name == tên công ty` thì lấy `Sector`, rồi `break`.
2. **Tìm công ty đại diện**: duyệt `top_company.xlsx`, hàng nào có `Sector` trùng thì đặt
   `top_c` = hạng 1 và `top_c_` = hạng 2.
   **Ngoại lệ**: nếu công ty đang xét *chính là* hạng 1 thì chuyển sang `top_c` = hạng 2, `top_c_` = hạng 3
   (tránh thay "we" của Exxon bằng chính "Exxon").
3. **Viết lại văn bản** (một dòng code):
   ```python
   i[3].replace(top_c, top_c_).lower().replace(' we ', ' '+top_c+' ').replace(' our ', ' '+top_c+"'s ").lower()
   ```
   * `.replace(top_c, top_c_)`: nếu văn bản đã nhắc sẵn tên `top_c` thì đổi sang `top_c_`, để sau bước sau, tên `top_c`
     chỉ xuất hiện ở những chỗ "we/our" đã được thay (đây là cách mình hiểu mục đích, code không giải thích).
   * `.lower()`: viết thường toàn bộ.
   * `' we '` → `' <top_c> '` và `' our '` → `' <top_c>'s '`: **dấu cách hai bên bắt buộc**.
   * `.lower()` lần cuối để tên công ty chèn vào cũng thành chữ thường.
4. Nhãn `i[1]` không bị đụng tới.

## 4. Ví dụ thật (văn bản #0, Lockheed Martin, ngành Industrials, công ty đầu ngành Boeing Company)

| Trước | Sau |
|---|---|
| …remarks based on the web charts that **we** included with **our** earnings release today | …remarks based on the web charts that **boeing company** included with **boeing company's** earnings release today |

Phép thay không chia động từ ("we believe" → "apple inc. believe"), giống ví dụ của bài báo.

## 5. Lỗi đã kiểm chứng: dòng đầu của `top_company.xlsx` bị nuốt

`pd.read_excel('top_company.xlsx')` mặc định coi dòng đầu là **tiêu đề cột**, nhưng file này **không có tiêu đề**:
dòng đầu là dữ liệu thật *Consumer Discretionary — Amazon.com Inc — Home Depot — Comcast Corp.* Kết quả là bảng `top` chỉ còn
**10 trong 11 ngành**, và ngành **Consumer Discretionary biến mất**.

Hậu quả (đã chạy lại và đếm):

* Với văn bản thuộc Consumer Discretionary, không hàng nào trong `top` khớp, nên `top_c` và `top_c_` **không được gán lại** và
  **giữ giá trị của văn bản trước đó**. Đây là cả **25/113 văn bản** (22%), đúng toàn bộ ngành Consumer Discretionary trong test set.
* Ví dụ: McDonald's (#2) nằm ngay sau Masco (Industrials), nên "we/our" của McDonald's bị thay bằng **Boeing Company**;
  Mattel (#27) bị thay bằng **JPMorgan Chase**; Garmin (#52) bằng **Apple**; Booking Holdings (#75) bằng **NextEra Energy**;
  Dish Network (#86) bằng **Wal-Mart Stores**.
  Công ty đúng theo thiết kế (đầu ngành Consumer Discretionary) lẽ ra là Amazon.com Inc.
* Như vậy 22% mẫu Transitive **không còn thoả tiền đề "cùng ngành"** của phép thử.
* Đọc đúng bằng `header=None` thì cả 11 ngành đều có mặt và số văn bản dùng nhầm là **0/113**. Hai bản
  khác nhau ở đúng 25 văn bản đó.

Script của mình cung cấp `--fix-header`; **mặc định giữ nguyên hành vi gốc** để tái hiện dữ liệu tác giả công bố.
Mỗi lần chạy script in số văn bản dùng nhầm công ty (25/113 ở chế độ mặc định).

```bash
python Code/generate_tra_consis.py                 # tái hiện bản tác giả (25/113 dùng nhầm)
python Code/generate_tra_consis.py --fix-header    # bản đã sửa -> scratch/tra_earnings_call_3days_fixed.npy
```

Lỗi này cũng *có thể* xảy ra khi một công ty không có trong `constituents-financials.xlsx` (khi đó `sector` giữ giá trị cũ hoặc báo lỗi);
với test set này, cả 113 công ty đều tìm thấy.

## 6. Các giới hạn khác đã kiểm chứng

1. **Thay thế không hoàn toàn.** Trong 17 393 dòng gốc có 6 936 lần " we " và 6 263 lần " our ". Sau biến đổi, " we " bị thay hết,
   nhưng **1 579 dòng vẫn bắt đầu bằng "we "**, **530 dòng bắt đầu bằng "our "** và **2 294 dòng chứa we're/we've/we'll/we'd**,
   vì luật yêu cầu dấu cách hai bên. Văn bản biến đổi vì vậy vẫn còn nhiều đại từ "we".
2. **Cắt cụt**: văn bản Exxon Mobil (hạng 1 ngành Energy, nên dùng Chevron/Schlumberger) dài ra 56 894 ký tự sau khi thay, vượt quá 54 209
   của kiểu `<U54209`, nên mất **2 685 ký tự cuối** (~5%, tương đương 25 dòng: 448 → 423 dòng; vì thế file Transitive có 17 368 dòng thay vì 17 393).
   Script mình in cảnh báo. (Các con số về "we/our" ở mục 6.1 tính trên file Transitive tác giả công bố, nên không gồm 25 dòng này.)
3. **Viết thường toàn bộ**, kể cả tên công ty.
4. **Độ tin cậy "công ty đầu ngành"**: danh sách trong `top_company.xlsx` do tác giả chọn (ví dụ Consumer Staples → Wal-Mart Stores;
   bài báo nói "top-valued company in the S&P 500"); mình chưa đối chiếu với vốn hoá thực tế thời điểm 2017.
5. Theo Bảng 4, Transitive consistency cao (0,673–0,991): có thể một phần do mô hình ít dựa vào các đại từ "we/our",
   và một phần do thay thế không hoàn toàn (mục 6.1). Đây là suy luận của mình, bài báo không tách bạch hai yếu tố này.

## 7. Chạy lại và kiểm chứng

```bash
python Code/generate_tra_consis.py
python Code/verify_outputs.py        # phải in [KHỚP] tra_earnings_call_3days.npy
```

## 8. Câu hỏi có thể gặp

* **Vì sao nhãn không đổi?** Vì giả định: đổi từ chỉ ngôi ("we") sang tên công ty đầu ngành không đổi ý nghĩa tài chính.
* **Vì sao công ty đầu ngành?** Giả thuyết trong bài báo: công ty đầu ngành dẫn dắt tâm lý của cả ngành (Phụ lục A).
* **Em có thấy điểm yếu nào trong repo không?** Có: lỗi `header` ở `top_company.xlsx` khiến 25/113 mẫu dùng sai công ty, đã tái hiện bằng cách chạy
  hai cách đọc file; bản sửa nằm ở `--fix-header`.
