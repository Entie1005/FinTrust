"""
Code/verify_outputs.py  --  kiểm tra: dữ liệu mình tự sinh ra (scratch/) có GIỐNG file tác giả công bố (Data/) không.

Chạy sau khi đã chạy 4 script generate_*_consis.py:
    python Code/verify_outputs.py

Quy tắc so sánh:
  * neg, sym, tra : so từng ô (ngày, nhãn, tên công ty, văn bản) => phải giống hệt.
  * add           : script xuất các dòng theo thứ tự "nhóm nhãn 0.0 trước, nhóm 1.0 sau", khác thứ tự file gốc,
                    nên ghép theo cặp (ngày, tên công ty) rồi so nội dung.
"""
import argparse
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=ROOT / "Data", help="file tác giả công bố")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "scratch", help="file mình vừa sinh")
    a = ap.parse_args()

    ok_all = True
    for name in ("neg", "sym", "tra", "add"):
        fname = f"{name}_earnings_call_3days.npy"
        if not (a.out_dir / fname).exists():
            print(f"[BỎ QUA] {fname}: chưa có trong {a.out_dir} (hãy chạy generate_{name}_consis.py trước)")
            continue
        mine = np.load(a.out_dir / fname)
        ref = np.load(a.data_dir / fname)
        if name == "add":
            key = lambda r: (str(r[0]), str(r[2]))
            dm, dr = {key(r): r for r in mine}, {key(r): r for r in ref}
            ok = dm.keys() == dr.keys() and all((dm[k] == dr[k]).all() for k in dm)
            how = "so theo (ngày, công ty)"
        else:
            ok = mine.shape == ref.shape and bool((mine == ref).all())
            how = "so từng ô"
        ok_all &= ok
        print(f"[{'KHỚP' if ok else 'KHÁC'}] {fname}  ({how}; {mine.shape[0]} văn bản)")
    print("\nKết luận:", "tái hiện đúng dữ liệu của tác giả." if ok_all else "có file KHÁC, hãy kiểm tra lại.")


if __name__ == "__main__":
    main()
