# `generate_neg_consis.py` — phép biến đổi Negation

> Tóm tắt một câu: lấy từng transcript, thay các từ như *more, increase, good, growth…* bằng từ trái nghĩa, **lật nhãn**
> tăng ↔ giảm, rồi lưu thành bộ dữ liệu kiểm thử. Một mô hình nhất quán phải **đổi dự đoán** khi ý nghĩa văn bản bị đảo.

## 1. Vì sao có phép này (đối chiếu bài báo, mục 3.1)

Bài báo định nghĩa *negation consistency*: f(x) = positive ⇔ f(¬x) = negative, trong đó "positive" nghĩa là giá sẽ tăng.
¬x là văn bản đã bị "lật" bằng **luật định sẵn dựa trên các bigram từ thường gặp và từ trái nghĩa của chúng**.

Ví dụ của bài báo: *"the cost of raw materials has been greatly **decreased**…"* → *"…greatly **increased**…"*.
Chi phí nguyên liệu giảm là tin tốt (kỳ vọng giá tăng); đảo thành tăng chi phí là tin xấu (kỳ vọng giá giảm).
Vì vậy **nhãn kỳ vọng cũng bị lật**. Mô hình chỉ được xem là nhất quán trên một mẫu khi dự đoán cho x và cho ¬x **khác nhau**
(đây là phép duy nhất trong bốn phép đòi hỏi "khác nhau"; ba phép còn lại đòi hỏi "giống nhau").

## 2. Đầu vào và đầu ra

| | Tệp | Nội dung |
|---|---|---|
| Vào | `Data/earnings_call_3days.npy` | 113 × 4: ngày, nhãn (`'0.0'`/`'1.0'`), tên công ty, văn bản |
| Ra | `scratch/neg_earnings_call_3days.npy` | cùng cấu trúc; **nhãn bị lật**, văn bản đã thay từ và viết thường |

## 3. Đọc code từng phần

### 3.1 `replace_words(sent)` — "bộ luật"

```python
def replace_words(sent):
  sent = sent.lower()
  if " more " in sent:
    return sent.replace(" more ", " less ")
  elif " less " in sent:
    return sent.replace(" less ", " more ")
  elif " positive " in sent: ...
```

* **Chuỗi `if/elif` dài 97 luật.** Mỗi luật là một cặp *"nếu câu chứa từ A thì thay A bằng B"*. Phần lớn đi theo cặp hai chiều
  (more↔less, positive↔negative, increase↔decrease, good↔bad…).
* **Mỗi câu chỉ bị thay đúng một loại từ.** Do dùng `elif` và `return` ngay khi khớp, luật **đứng trước thắng**.
  Ví dụ câu có cả "more" và "increase" thì chỉ "more" → "less" được thực hiện (mọi lần xuất hiện của *cùng* từ "more"
  thì đều đổi, vì `str.replace` thay tất cả lần xuất hiện).
* **Từ phải đứng giữa hai dấu cách.** Luật viết là `" more "` (có dấu cách hai bên), nên *"more,"*, *"more."* hoặc từ ở đầu/cuối dòng **không** khớp.
* **Luôn trả về chữ thường**: dòng đầu tiên `sent = sent.lower()`, nên kể cả dòng không bị thay vẫn bị viết thường.

### 3.2 `make_neg()` — vòng lặp trên từng văn bản

Với mỗi văn bản `i = [ngày, nhãn, công ty, văn bản]`:

1. **Lật nhãn**: nếu `i[1] == '1.0'` thì thành `'0.0'`, ngược lại (mọi giá trị khác) thành `'1.0'`. Lật cho **mọi** văn bản,
   không phụ thuộc việc văn bản có từ nào bị thay hay không.
2. `text = i[3].replace('\n', '.\n')`: thêm dấu chấm cuối mỗi dòng (dòng gốc không có dấu chấm cuối).
3. `text.split('\n')`: tách thành danh sách các dòng.
4. Với mỗi dòng: `replace_words(dòng)`, cộng vào `neg_text` kèm một dấu cách.
5. `neg_text.replace('. ', '\n')`: đổi mọi `". "` thành xuống dòng, khôi phục cấu trúc "mỗi dòng một câu".
   (Hệ quả phụ: dấu `". "` có sẵn *giữa* một dòng cũng biến thành xuống dòng; trong dữ liệu có 664 chỗ như vậy.)
6. `np.save(...)` lưu cả mảng (đã được sửa tại chỗ) ra file mới.

## 4. Ví dụ thật (văn bản #0, Lockheed Martin, nhãn gốc `0.0` → `1.0`)

| Trước | Sau | Nhận xét |
|---|---|---|
| …web charts that we included with our **earnings** release today | …with our **cost** release today | luật *earnings→cost* làm mất nghĩa ("cost release") |
| Let's begin **with** chart 3 and an overview of our results | let's begin **without** chart 3 … | luật *with→without* (luật cuối cùng của chuỗi) |
| We're pleased **with** our performance in the quarter | we're pleased **without** our performance … | cũng *with→without* |

Hai dòng cuối đều do luật *with→without* (luật cuối cùng của chuỗi, và là luật thứ hai được dùng nhiều nhất);
kết quả không phải một "tin xấu" về tài chính mà chỉ là câu bị hỏng.

## 5. Số liệu đã kiểm chứng trên test set

* **10 766 / 17 393 dòng (61,9%) bị thay từ**; 113/113 văn bản có ít nhất một dòng bị thay.
* Các luật dùng nhiều nhất: *more→less* (1 067 dòng), *with→without* (728), *sales→buy* (554), *growth→decay* (534),
  *up→down* (505), *continue→stop* (449), *good→bad* (442).
* **14/97 luật không khớp dòng nào** trong test set (ví dụ dislike, disbelieve, abandon, approve, refuse, ignore, empty…).
* **11/97 luật không có chiều ngược lại** (nếu áp luật hai lần, kết quả không quay về câu gốc):
  sales→buy, a lot of→few, growth→decay, margin→loss, benefits→loss, income→loss, add→decrease, change→unchange,
  opportunities→changes, opportunity→change, within→without.

## 6. Điểm cần lưu ý khi thuyết trình (trung thực về giới hạn)

1. **Không phải mọi thay thế đều đảo "ý nghĩa tài chính".** Các luật như *with→without*, *earnings→cost*, *sales→buy*,
   *revenue→expense* đổi từ ngữ nhưng có thể làm câu vô nghĩa thay vì "tin xấu". Bài báo báo cáo đánh giá con người
   (2 người gán nhãn **lấy từ chính nhóm tác giả**, 40 mẫu gốc và 160 mẫu biến đổi; độ đồng thuận 0,98; consistency
   trung bình của con người 0,975, tức "phép biến đổi giữ được nghĩa gốc trong đa số trường hợp").
   Mẫu kiểm tra khá nhỏ so với 17 393 dòng và người gán nhãn không độc lập với tác giả, nên câu hỏi
   "tỷ lệ thực sự trên toàn test set là bao nhiêu?" là hợp lý.
2. **38% dòng không đổi**, và mỗi dòng chỉ đổi một loại từ, nên văn bản "bị lật" vẫn còn nhiều câu gốc. Điều này
   nghĩa là việc *lật nhãn* mạnh hơn mức *lật nội dung* thực tế.
3. **Lật nhãn vô điều kiện**: kể cả văn bản mà luật thay được rất ít dòng.
4. Kết hợp với kết quả bài báo (Bảng 4: điểm Negation consistency của mọi mô hình chỉ 0,009–0,354):
   mô hình thường **giữ nguyên dự đoán** dù văn bản bị đổi, tức là nhiều khả năng chúng dựa vào đặc điểm khác (tên công ty,
   cấu trúc văn bản…) hơn là nghĩa của từng câu. Đây là cách diễn giải hợp lý chứ không phải kết luận đã được bài báo chứng minh.

## 7. Chạy lại và kiểm chứng

```bash
python Code/generate_neg_consis.py
python Code/verify_outputs.py        # phải in [KHỚP] neg_earnings_call_3days.npy
```

## 8. Câu hỏi có thể gặp

* **Vì sao lật nhãn mà không giữ nguyên?** Vì phép biến đổi được thiết kế để đảo ý nghĩa; nhãn kỳ vọng đảo theo.
* **Negation có phải adversarial attack không?** Không. Tấn công đối kháng cố làm mô hình sai; ở đây phép biến đổi có
  *kết quả kỳ vọng xác định trước* theo logic của con người.
* **Vì sao điểm Negation thấp hơn ba phép còn lại?** Trong Bảng 4, Negation chỉ 0,009–0,354, còn Symmetric
  0,655–1,000, Transitive 0,673–0,991, Additive 0,301–0,947. Mô hình ít nhạy với đảo nghĩa hơn là với đảo thứ tự hay đổi tên.
  Khi đọc con số này nhớ mục 6: một phần "đảo nghĩa" của dữ liệu là câu bị hỏng chứ chưa chắc là tin xấu rõ ràng.
