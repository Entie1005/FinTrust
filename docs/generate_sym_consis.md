# `generate_sym_consis.py` — phép biến đổi Symmetric

> Tóm tắt một câu: trong mỗi câu, cắt thành các mệnh đề ở chỗ có dấu phẩy rồi **xếp chúng theo thứ tự ngược lại**.
> Nhãn **giữ nguyên**, vì con người coi thứ tự các mệnh đề không đổi ý nghĩa tài chính.
> Một mô hình nhất quán phải **giữ dự đoán**.

## 1. Vì sao có phép này (đối chiếu bài báo, mục 3.1)

Bài báo định nghĩa *symmetric consistency*: f(Sp1, Sp2) = f(Sp2, Sp1), với Spi là phần thứ i của câu S.
Ví dụ của bài báo: *"the cost of raw materials has been greatly decreased, with a change of 30% compared with last year"*
→ *"with a change of 30% compared with last year, the cost of raw materials has been greatly decreased"*.
Hai câu cùng nghĩa; nếu mô hình đổi dự đoán chỉ vì đảo thứ tự thì nó đang dựa vào **vị trí từ** chứ không phải nội dung.
Nhãn không đổi vì ý nghĩa không đổi.

## 2. Đầu vào và đầu ra

| | Tệp | Nội dung |
|---|---|---|
| Vào | `Data/earnings_call_3days.npy` | 113 × 4: ngày, nhãn, tên công ty, văn bản |
| Ra | `scratch/sym_earnings_call_3days.npy` | cùng cấu trúc; **nhãn giữ nguyên**, văn bản đã đảo mệnh đề và viết thường |

## 3. Đọc code từng phần

### 3.1 `split_into_sub_sentences(input_text)`

```python
sentences = re.split(r'(?<=[,.] )', input_text)
```

Biểu thức chính quy `(?<=[,.] )` là một *lookbehind*: "vị trí nằm ngay **sau** một dấu `,` hoặc `.` kèm dấu cách".
Tách tại những vị trí đó, mỗi mảnh **giữ lại** dấu và dấu cách ở cuối. Ví dụ `"good morning, everyone."`
→ `["good morning, ", "everyone."]`.

### 3.2 `make_sym()` — xử lý một dòng

Văn bản được thêm `.` cuối mỗi dòng (như Negation) rồi tách thành dòng. Với mỗi dòng `j`:

1. `parts = split_into_sub_sentences(j.lower())` — viết thường rồi cắt thành các mảnh.
2. `parts[-1] = parts[-1][:-1] + ','` rồi thêm `' '` — mảnh **cuối** đang kết thúc bằng dấu `.`; đổi `.` thành `,` và thêm
   dấu cách để nó có hình dạng giống các mảnh khác (kết thúc bằng `", "`).
3. Duyệt `k = 0 … len-1`, lấy `parts[-k-1]` (**duyệt ngược từ cuối về đầu**) và nối vào kết quả.
   Riêng phần tử cuối của vòng lặp (chính là mảnh **đầu tiên** của câu gốc) thì cắt bỏ 2 ký tự cuối (`", "`)
   rồi thêm `". "`, để câu mới kết thúc bằng dấu chấm.
4. Sau khi xong cả văn bản: `sym_text.replace('. ', '\n')` — mọi `". "` thành xuống dòng.

Minh hoạ với `"Good morning, everyone"`:

| Bước | Giá trị |
|---|---|
| thêm `.` + viết thường | `good morning, everyone.` |
| tách | `["good morning, ", "everyone."]` |
| mảnh cuối đổi `.`→`,` | `["good morning, ", "everyone, "]` |
| duyệt ngược, nối | `"everyone, "` + `"good morning"` + `". "` |
| `". "` → xuống dòng | `everyone, good morning` ⏎ |

Câu không có dấu phẩy chỉ có một mảnh nên chỉ bị viết thường, nội dung giữ nguyên.

## 4. Ví dụ thật (văn bản #0, Lockheed Martin, nhãn `0.0` giữ nguyên)

| Trước | Sau |
|---|---|
| Good morning, everyone | everyone, good morning |
| Profit, on the other hand, is comparable under the two standards | is comparable under the two standards, on the other hand, profit |
| In addition, and as expected, we had a very strong quarter of capturing new business, achieving a record backlog level of $104 billion | achieving a record backlog level of $104 billion, we had a very strong quarter of capturing new business, and as expected, in addition |
| Sales of … expectations, **but** we expect … fourth quarter, as we will discuss later | as we will discuss later, **but** we expect … fourth quarter, sales of … expectations |

Dòng 3 và 4 cho thấy điều quan trọng: code đảo **tất cả** mệnh đề, không chỉ hai phần (Sp1, Sp2) như định nghĩa trong bài báo.
Từ nối như "but", "and", "in addition" bị đưa về vị trí khác, nên đôi khi câu nghe gượng.

## 5. Số liệu đã kiểm chứng

* **62% số dòng (10 805/17 393) chứa dấu phẩy**, tức bị đảo thật sự. Khoảng **37%** (6 476 dòng) không có dấu phẩy và chỉ bị viết thường.
* **Số dòng tăng**: 17 393 → 17 909 (+516). Nguyên nhân: dấu `". "` nằm giữa một dòng (664 chỗ trong dữ liệu gốc) bị đổi thành xuống dòng,
  nên một dòng gốc có thể tách thành nhiều dòng. Sau biến đổi, số `". "` còn lại trong văn bản là 0.
* Văn bản #0: 228 → 255 dòng.

## 6. Điểm cần lưu ý khi thuyết trình

1. **Đảo mọi mệnh đề** chứ không chỉ đổi chỗ hai phần như trong định nghĩa (xem mục 4). Với dòng có nhiều dấu phẩy,
   thứ tự đảo xa câu gốc hơn so với ví dụ minh hoạ của bài báo.
2. **Dấu phẩy không phải ranh giới mệnh đề hoàn hảo**: dấu phẩy trong liệt kê (*"earnings per share and cash from operations,
   operating profit, …"*) cũng bị coi là ranh giới và đảo ngược.
3. **Thay đổi cấu trúc dòng** (số dòng tăng) là tác dụng phụ ngoài ý muốn: một mô hình xử lý theo câu/dòng sẽ thấy
   một đầu vào có số "câu" khác.
4. Mọi chữ đều thành chữ thường, nên mô hình phân biệt chữ hoa/thường sẽ thấy khác biệt ngoài thứ tự mệnh đề.
5. Theo Bảng 4 của bài báo, Symmetric consistency khá cao (0,655–1,000): mô hình nhìn chung ít bị ảnh hưởng bởi đảo thứ tự.

## 7. Chạy lại và kiểm chứng

```bash
python Code/generate_sym_consis.py
python Code/verify_outputs.py        # phải in [KHỚP] sym_earnings_call_3days.npy
```

## 8. Câu hỏi có thể gặp

* **Vì sao nhãn không đổi?** Vì đảo thứ tự mệnh đề được giả định không đổi ý nghĩa tài chính.
* **Vì sao Symmetric dễ đạt điểm cao hơn Negation?** Nếu mô hình chủ yếu dựa vào *những từ xuất hiện* (như túi từ),
  thứ tự không quan trọng nên dự đoán gần như giữ nguyên; điều đó cho điểm cao ở Symmetric nhưng không chứng tỏ mô hình "hiểu" nghĩa
  (đây là cách giải thích hợp lý, bài báo không kiểm tra riêng điều này).
