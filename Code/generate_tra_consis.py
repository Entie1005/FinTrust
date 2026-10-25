"""
Code/generate_tra_consis.py  --  phép biến đổi TRANSITIVE của FinTrust.

Ý tưởng (bài báo, mục 3.1 và Phụ lục A): cảm nhận về một công ty cũng phản ánh trong công ty đầu ngành cùng sector.
Thay "we"/"our" trong transcript bằng tên công ty đứng đầu cùng ngành ("company_name", "company_name's");
mô hình nhất quán phải GIỮ nguyên dự đoán  f(x) = f(x').  => KHÔNG đổi nhãn, chỉ đổi văn bản.

Dữ liệu phụ (nằm cạnh file này, trong Code/):
  constituents-financials.xlsx : danh sách S&P 500; cột [1]=tên công ty, cột [2]=sector
  top_company.xlsx             : mỗi dòng = [sector, công ty hạng 1, hạng 2, hạng 3]

Với mỗi văn bản: tra sector của công ty -> lấy hạng 1 của sector (top_c) và hạng 2 (top_c_).
Nếu công ty ĐANG xét chính là hạng 1 thì dùng hạng 2 (top_c) và hạng 3 (top_c_) (tránh thay nó bằng chính nó).
Rồi: (1) thay tên top_c trong văn bản bằng top_c_ ; (2) ' we ' -> ' top_c ' ; (3) ' our ' -> " top_c's ".

Đầu vào : <data-dir>/earnings_call_3days.npy
Đầu ra  : <out-dir>/tra_earnings_call_3days.npy
          (hoặc tra_earnings_call_3days_fixed.npy nếu dùng --fix-header)

Cách chạy:
    python Code/generate_tra_consis.py                 # tái hiện ĐÚNG hành vi script gốc của tác giả
    python Code/generate_tra_consis.py --fix-header    # đọc top_company.xlsx đúng (xem bên dưới)

!!! LỖI ĐÃ KIỂM CHỨNG TRONG SCRIPT GỐC (giữ nguyên làm mặc định để khớp file tác giả công bố) !!!
top_company.xlsx KHÔNG có dòng tiêu đề, nhưng pd.read_excel(...) mặc định coi dòng đầu là tiêu đề, nên dòng
"Consumer Discretionary / Amazon / Home Depot / Comcast" bị nuốt mất. Hậu quả: văn bản thuộc ngành này không khớp
sector nào, biến top_c/top_c_ không được gán lại và DÙNG LẠI giá trị của văn bản trước (25/113 văn bản).
--fix-header sửa bằng header=None. Kết quả mặc định (không cờ) vẫn khớp từng ký tự file của tác giả.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CODE_DIR = Path(__file__).resolve().parent        # thư mục Code/: nơi đặt 2 file Excel
ROOT = CODE_DIR.parent
DEFAULT_DATA = ROOT / "Data"
DEFAULT_OUT = ROOT / "scratch"


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Sinh dữ liệu kiểm thử Transitive consistency (FinTrust).")
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA, help="thư mục chứa earnings_call_3days.npy")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT, help="thư mục ghi file kết quả")
    ap.add_argument("--fix-header", action="store_true",
                    help="đọc top_company.xlsx với header=None (sửa lỗi nuốt dòng đầu); đầu ra sẽ KHÁC file tác giả")
    ap.add_argument("--force", action="store_true", help="cho phép ghi đè vào chính thư mục dữ liệu")
    args = ap.parse_args(argv)
    if args.out_dir.resolve() == args.data_dir.resolve() and not args.force:
        ap.error("out-dir trùng data-dir: sẽ ghi đè file gốc. Dùng --out-dir khác, hoặc thêm --force nếu chủ ý.")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    return args


def make_tra(data_dir=DEFAULT_DATA, out_dir=DEFAULT_OUT, fix_header=False):
    df = pd.read_excel(CODE_DIR / 'constituents-financials.xlsx')
    data = df.values                                   # cột [1]=tên công ty, [2]=sector
    df = pd.read_excel(CODE_DIR / 'top_company.xlsx', header=None if fix_header else 0)
    top = df.values                                    # [sector, hạng 1, hạng 2, hạng 3]
    print(top)
    test_list = np.load(Path(data_dir) / "earnings_call_3days.npy")
    width = test_list.dtype.itemsize // 4              # độ rộng tối đa (ký tự) của mỗi ô chuỗi trong file .npy
    n_stale = 0                                        # chỉ để báo cáo: số văn bản dùng lại công ty của văn bản trước
    for i in test_list:                                # i = [ngày, nhãn, tên công ty, văn bản]
        for j in data:
            if j[1] == i[2]:                           # tìm công ty trong danh sách S&P 500
                sector = j[2]
                break
        matched = False
        for j in top:
            if j[0] == sector:                         # sector có trong top_company.xlsx
                top_c = j[1]                           # công ty hạng 1
                top_c_ = j[2]                          # công ty hạng 2
                if j[1] == i[2]:                       # công ty đang xét chính là hạng 1
                    top_c = j[2]                       # -> dùng hạng 2 làm "công ty đại diện"
                    top_c_ = j[3]                      # -> và hạng 3 làm công ty thay thế tên
                matched = True
        if not matched:
            n_stale += 1                               # top_c / top_c_ giữ giá trị của văn bản trước (lỗi)
        text = i[3].replace(top_c, top_c_).lower().replace(' we ', ' ' + top_c + ' ').replace(' our ', ' ' + top_c + "'s ").lower()
        if len(text) > width:                          # numpy CẮT CỤT im lặng chuỗi dài hơn độ rộng kiểu '<U54209'
            print(f"  CẢNH BÁO: {i[2]} dài {len(text)} > {width} ký tự sau khi thay tên, mất {len(text) - width} ký tự cuối")
        i[3] = text                                    # nhãn i[1] không đổi
    print(len(test_list))
    print(f"Số văn bản dùng lại công ty của văn bản trước (không khớp sector): {n_stale}/{len(test_list)}")
    name = "tra_earnings_call_3days_fixed.npy" if fix_header else "tra_earnings_call_3days.npy"
    out = Path(out_dir) / name
    np.save(out, test_list)
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    a = parse_args()
    make_tra(a.data_dir, a.out_dir, a.fix_header)
