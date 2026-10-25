"""
Code/generate_add_consis.py  --  phép biến đổi ADDITIVE của FinTrust.

Ý tưởng (bài báo, mục 3.1): nếu mô hình dự đoán "tăng" cho văn bản x và cũng "tăng" cho văn bản y thì
phải dự đoán "tăng" cho văn bản ghép x+y (tương tự với "giảm").  => GHÉP HAI VĂN BẢN CÙNG NHÃN, GIỮ nhãn.

Cách làm: chia test set thành nhóm nhãn '0.0' (giảm) và nhóm '1.0' (tăng). Trong mỗi nhóm, văn bản thứ i được
ghép với văn bản KẾ TIẾP (i+1, vòng tròn: văn bản cuối ghép với văn bản đầu) nếu tổng số dòng < MAX_LINES.
Nếu tổng >= MAX_LINES thì KHÔNG ghép, giữ nguyên văn bản gốc (kể cả chữ hoa).

Đầu vào : <data-dir>/earnings_call_3days.npy
Đầu ra  : <out-dir>/add_earnings_call_3days.npy  (thứ tự dòng: toàn bộ nhóm '0.0' trước, rồi nhóm '1.0';
          KHÁC thứ tự của test set gốc. File tác giả công bố thì đã được sắp lại đúng thứ tự gốc (script không làm việc
          đó), nên khi so sánh hãy ghép theo (ngày, công ty), đừng theo vị trí dòng)

Cách chạy (từ bất kỳ thư mục nào):
    python Code/generate_add_consis.py
    python Code/generate_add_consis.py --data-dir D:/du_lieu --out-dir D:/ket_qua

Bản chỉnh sửa so với bản gốc: thêm xử lý đường dẫn + chú thích; đổi tên biến `list`->`result`, `next`->`nxt`
(trùng tên hàm dựng sẵn của Python, đổi tên không làm thay đổi kết quả); đưa số 512 thành hằng MAX_LINES.
"""
import argparse
import copy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "Data"
DEFAULT_OUT = ROOT / "scratch"
MAX_LINES = 512   # ngưỡng do tác giả chọn; bài báo không giải thích lý do (có thể liên quan giới hạn độ dài đầu vào của mô hình)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Sinh dữ liệu kiểm thử Additive consistency (FinTrust).")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA, help="thư mục chứa earnings_call_3days.npy")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="thư mục ghi file kết quả")
    ap.add_argument("--force", action="store_true", help="cho phép ghi đè vào chính thư mục dữ liệu")
    args = ap.parse_args(argv)
    if args.out_dir.resolve() == args.data_dir.resolve() and not args.force:
        ap.error("out-dir trùng data-dir: sẽ ghi đè file gốc. Dùng --out-dir khác, hoặc thêm --force nếu chủ ý.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    return args


def merge_group(group, result):
    """Ghép từng văn bản trong `group` với văn bản kế tiếp (vòng tròn) nếu tổng số dòng < MAX_LINES."""
    new = copy.deepcopy(group)                       # bản sao để sửa, không đụng bản gốc
    width = group[0].dtype.itemsize // 4             # file .npy lưu chuỗi KIỂU CỐ ĐỊNH '<U54209' (4 byte/ký tự)
    for i in range(len(group)):
        length = len(group[i][3].split('\n'))        # số dòng của văn bản i
        nxt = i + 1
        if nxt == len(group):                        # văn bản cuối ghép với văn bản đầu
            nxt = 0
        next_length = len(group[nxt][3].split('\n'))
        if length + next_length < MAX_LINES:
            merged = (group[i][3] + '\n' + group[nxt][3]).lower()   # ghép, rồi đưa về chữ thường
            if len(merged) > width:                  # numpy CẮT CỤT im lặng chuỗi dài hơn độ rộng kiểu dữ liệu
                print(f"  CẢNH BÁO: {group[i][2]} + {group[nxt][2]} dài {len(merged)} > {width} ký tự, "
                      f"mất {len(merged) - width} ký tự cuối (phần cuối văn bản ghép thêm)")
            new[i][3] = merged
        result.append(new[i])                        # không ghép được thì giữ nguyên bản gốc (chưa lower)


def make_add(data_dir=DEFAULT_DATA, out_dir=DEFAULT_OUT):
    test_list = np.load(Path(data_dir) / "earnings_call_3days.npy")
    increase_list = []   # nhãn '1.0' (giá tăng)
    decrease_list = []   # nhãn '0.0' (giá giảm)
    result = []
    for i in test_list:
        if i[1] == '0.0':
            decrease_list.append(i)
        else:
            increase_list.append(i)
    merge_group(decrease_list, result)
    print(len(result))                               # số văn bản nhóm giảm (67 với test set của tác giả)
    merge_group(increase_list, result)
    print(len(result))                               # tổng sau cả hai nhóm (113)
    out = Path(out_dir) / "add_earnings_call_3days.npy"
    np.save(out, result)
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    a = parse_args()
    make_add(a.data_dir, a.out_dir)
