"""
Code/generate_sym_consis.py  --  phép biến đổi SYMMETRIC của FinTrust.

Ý tưởng (bài báo, mục 3.1): đảo thứ tự các mệnh đề trong một câu; con người cho rằng ý nghĩa
không đổi, nên một mô hình nhất quán phải GIỮ nguyên dự đoán  f(Sp1, Sp2) = f(Sp2, Sp1).
=> Script này KHÔNG đổi nhãn, chỉ đổi văn bản.

Đầu vào : <data-dir>/earnings_call_3days.npy   (113 dòng x 4 cột: ngày, nhãn, tên công ty, văn bản)
Đầu ra  : <out-dir>/sym_earnings_call_3days.npy (cùng cấu trúc)

Cách chạy (từ BẤT KỲ thư mục nào, đường dẫn tự suy ra từ vị trí file này):
    python Code/generate_sym_consis.py
    python Code/generate_sym_consis.py --data-dir D:/du_lieu --out-dir D:/ket_qua

Mặc định ghi vào <gốc repo>/scratch/ (đã nằm trong .gitignore) để KHÔNG ghi đè file ~98 MB trong Data/.

Ghi chú về bản chỉnh sửa so với bản gốc của tác giả: CHỈ thêm phần xử lý đường dẫn/tham số dòng lệnh
và chú thích. Logic của split_into_sub_sentences() và make_sym() giữ nguyên từng dòng
(đã kiểm chứng: đầu ra khớp từng ký tự với Data/sym_earnings_call_3days.npy của tác giả).
"""
import argparse
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]   # gốc repo = thư mục cha của Code/
DEFAULT_DATA = ROOT / "Data"
DEFAULT_OUT = ROOT / "scratch"


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Sinh dữ liệu kiểm thử Symmetric consistency (FinTrust).")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA, help="thư mục chứa earnings_call_3days.npy")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="thư mục ghi file kết quả")
    ap.add_argument("--force", action="store_true", help="cho phép ghi đè vào chính thư mục dữ liệu")
    args = ap.parse_args(argv)
    if args.out_dir.resolve() == args.data_dir.resolve() and not args.force:
        ap.error("out-dir trùng data-dir: sẽ ghi đè file gốc. Dùng --out-dir khác, hoặc thêm --force nếu chủ ý.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    return args


def split_into_sub_sentences(input_text):
    # Cắt chuỗi thành các "mệnh đề" ngay SAU mỗi ", " hoặc ". " (lookbehind (?<=[,.] ) giữ lại dấu và dấu cách
    # ở cuối mỗi mảnh). Ví dụ "a, b. c" -> ["a, ", "b. ", "c"].
    sentences = re.split(r'(?<=[,.] )', input_text)
    return sentences


def make_sym(data_dir=DEFAULT_DATA, out_dir=DEFAULT_OUT):
    test_list = np.load(Path(data_dir) / "earnings_call_3days.npy")
    for i in test_list:                      # i = [ngày, nhãn, tên công ty, văn bản]; i là view nên gán i[3] sửa trực tiếp test_list
        text = i[3].replace('\n', '.\n')     # thêm '.' cuối mỗi dòng để mỗi dòng kết thúc bằng dấu chấm
        text = text.split('\n')              # tách văn bản thành các dòng (mỗi dòng ~ một câu)
        sym_text = ''
        for j in text:
            text = split_into_sub_sentences(j.lower())   # (tái dùng tên `text`, vòng for vẫn chạy trên danh sách dòng cũ)
            text[-1] = text[-1][:-1] + ','   # mảnh cuối: bỏ ký tự cuối (dấu '.') thay bằng ','
            text[-1] += ' '
            for k in range(len(text)):
                if k == len(text) - 1:       # k cuối = mảnh ĐẦU TIÊN của câu gốc, nay đứng cuối
                    sym_text += text[-k - 1][:-2]   # bỏ ", " ở cuối mảnh
                    sym_text += '. '
                else:
                    sym_text += text[-k - 1]        # duyệt mảnh từ cuối về đầu => đảo thứ tự
        i[3] = sym_text.replace('. ', '\n')  # mọi ". " (kể cả ". " nằm giữa câu) biến thành xuống dòng
    out = Path(out_dir) / "sym_earnings_call_3days.npy"
    np.save(out, test_list)
    print(f"Đã ghi {out}  ({len(test_list)} văn bản)")


if __name__ == "__main__":
    a = parse_args()
    make_sym(a.data_dir, a.out_dir)
