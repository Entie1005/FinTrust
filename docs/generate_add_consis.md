# `generate_add_consis.py` — phép biến đổi Additive

> Tóm tắt một câu: ghép mỗi transcript với một transcript **khác có cùng nhãn**; nhãn **giữ nguyên**.
> Một mô hình nhất quán phải **giữ dự đoán** cho văn bản ghép.

## 1. Vì sao có phép này (đối chiếu bài báo, mục 3.1)

Ví dụ của bài báo: nếu mô hình dự đoán "tăng" cho câu *"the cost of raw materials has been greatly decreased…"* và cũng dự
đoán "tăng" cho câu *"we believe that our products can bring convenience to everyone's life"*, thì khi nối hai câu lại nó
cũng phải dự đoán "tăng". Tương tự với "giảm". Vì thế phải ghép **hai văn bản cùng nhãn**: ghép hai nhãn khác nhau thì không có
đáp án kỳ vọng rõ ràng. Mẫu chỉ được tính là nhất quán khi dự đoán cho văn bản ghép **bằng** dự đoán cho các văn bản thành phần.

## 2. Đầu vào và đầu ra

| | Tệp | Nội dung |
|---|---|---|
| Vào | `Data/earnings_call_3days.npy` | 113 × 4: ngày, nhãn, tên công ty, văn bản |
| Ra | `scratch/add_earnings_call_3days.npy` | cùng cấu trúc; nhãn giữ nguyên; văn bản của 110/113 hàng là bản ghép |

**Chú ý thứ tự dòng:** script xuất toàn bộ nhóm `0.0` trước, rồi nhóm `1.0`. File tác giả công bố thì đã được sắp lại đúng
thứ tự gốc của test set (script không làm việc đó), nên `verify_outputs.py` so sánh theo cặp (ngày, công ty).

## 3. Đọc code từng phần

1. **Chia nhóm** (`make_add`): lần lượt đưa mỗi văn bản vào `decrease_list` (nhãn `'0.0'`, 67 văn bản) hoặc
   `increase_list` (mọi nhãn khác, tức `'1.0'`, 46 văn bản).
2. **Ghép trong từng nhóm** (`merge_group`, mình tách ra từ hai đoạn lặp lại của bản gốc, logic y hệt):
   * `new = copy.deepcopy(group)`: bản sao để sửa mà không đụng văn bản gốc.
   * Với văn bản thứ `i`, đối tác là văn bản **kế tiếp** `i+1` trong nhóm; văn bản cuối ghép với văn bản đầu
     (`if nxt == len(group): nxt = 0`), nên mỗi văn bản được dùng đúng một lần làm "phần đầu" và một lần làm "đối tác".
   * Đếm số dòng của hai văn bản. **Nếu tổng < 512 dòng** (hằng `MAX_LINES`) thì
     `new[i][3] = (văn bản i + '\n' + văn bản đối tác).lower()` — nối bằng xuống dòng và viết thường **toàn bộ**.
   * **Nếu tổng ≥ 512** thì **không ghép**, hàng này giữ nguyên văn bản gốc (kể cả chữ hoa).
   * Cột ngày và tên công ty luôn là của văn bản **thứ nhất**; chỉ cột văn bản chứa thêm nội dung của đối tác.
3. Gộp kết quả của hai nhóm rồi `np.save`.

Ngưỡng 512 do tác giả chọn; bài báo và code không giải thích lý do (có thể liên quan giới hạn độ dài đầu vào của mô hình, nhưng đó
là suy đoán của mình).

## 4. Ví dụ thật

Văn bản #0, Lockheed Martin (nhãn `0.0`, 228 dòng, 30 641 ký tự) được ghép với **Masco** (nhãn `0.0`, 109 dòng, 15 234 ký tự):
228 + 109 = 337 < 512, nên hàng này có văn bản **337 dòng, 45 876 ký tự**, bắt đầu bằng toàn bộ bài của Lockheed rồi đến
bài của Masco, tất cả viết thường. Ngày vẫn là 2017-10-24 và công ty vẫn ghi là "Lockheed Martin Corp.".

## 5. Số liệu đã kiểm chứng

* **110/113 văn bản được ghép.** 3 văn bản không ghép được vì tổng ≥ 512 dòng:

| Văn bản | Đối tác | Tổng dòng |
|---|---|---|
| Aon plc (110 dòng, nhãn 0.0) | Exxon Mobil (448) | 558 |
| Exxon Mobil (448, nhãn 0.0) | Merck & Co. (75) | 523 |
| CBS Corp. (243, nhãn 1.0) | Martin Marietta Materials (425) | 668 |

  Văn bản dài nhất test set là 448 dòng (Exxon Mobil); trung vị 151 dòng.
* **7/113 văn bản ghép bị CẮT CỤT** (đã kiểm chứng; không có trong bài báo). Nguyên nhân: file `.npy` lưu chuỗi kiểu cố định
  `<U54209`, mỗi ô tối đa 54 209 ký tự. numpy **cắt im lặng** phần thừa khi gán chuỗi dài hơn. Phần mất là **phần cuối của văn bản đối tác**
  (thường là phần hỏi đáp cuối cuộc họp):

| Văn bản + đối tác | Độ dài ghép | Ký tự mất | % bài đối tác bị mất |
|---|---|---|---|
| AES Corp + Automatic Data Processing | 57 685 | 3 476 | 10% |
| Automatic Data Processing + Ball Corp | 59 857 | 5 648 | 22% |
| Gartner Inc + Parker-Hannifin | 54 301 | 92 | 0,4% |
| Intel Corp. + Mattel Inc. | 62 470 | 8 261 | 20% |
| Mattel Inc. + ResMed | 64 590 | 10 381 | 46% |
| Martin Marietta Materials + Motorola Solutions | 55 881 | 1 672 | 24% |
| General Mills + Conagra Brands | 55 535 | 1 326 | 4% |

  Script đã sửa của mình **in cảnh báo** cho từng trường hợp này khi chạy. Dữ liệu tác giả công bố mang cùng lỗi (khớp từng ký tự).

## 6. Điểm cần lưu ý khi thuyết trình

1. **Văn bản ghép thường là hai công ty khác nhau, chỉ chung nhãn.** Phép thử vì vậy hỏi: "ghép hai bài cùng nhãn có làm mô hình đổi ý không?",
   chứ không phải "bài ghép có ý nghĩa mạch lạc không". Nhãn hàng vẫn gắn với công ty đầu.
2. **Không đồng nhất giữa các hàng**: 110 hàng bị viết thường hoàn toàn, 3 hàng giữ nguyên chữ hoa; mô hình phân biệt hoa/thường
   có thể phản ứng với điều này thay vì với việc ghép.
3. **Đối tác được chọn theo thứ tự trong file** (văn bản kế tiếp trong nhóm cùng nhãn), không dùng ngẫu nhiên có hạt giống và không chọn theo ngành.
4. **Cắt cụt (mục 5)**: 7 văn bản mất phần cuối của đối tác; ảnh hưởng nhỏ nếu mô hình chỉ đọc phần đầu, nhưng đây là điều nên khai báo.
5. Theo Bảng 4, Additive consistency dao động nhiều giữa mô hình và kỳ hạn (0,301–0,947), thấp nhất là XGBoost ở mức ~0,5.

## 7. Chạy lại và kiểm chứng

```bash
python Code/generate_add_consis.py     # sẽ in 67, 113 và các cảnh báo cắt cụt
python Code/verify_outputs.py          # phải in [KHỚP] add_earnings_call_3days.npy
```

## 8. Câu hỏi có thể gặp

* **Vì sao chỉ ghép cùng nhãn?** Vì chỉ khi đó mới có đáp án kỳ vọng (cùng nhãn).
* **Vì sao 512?** Tác giả không nêu lý do trong bài hay code.
* **Văn bản ghép có hợp lý không?** Là hai bài độc lập nối nhau; mục đích là kiểm tra tính cộng gộp chứ không phải tạo văn bản tự nhiên.
