"""
demo/demo_transformations.py

Minh hoạ trực quan 4 phép biến đổi consistency của FinTrust (Negation, Symmetric,
Additive, Transitive) trên test set gốc của tác giả (Data/earnings_call_3days.npy).

- KHÔNG ghi file .npy mới (các file đầu ra gốc nặng ~98MB/file, không nên commit thêm).
- Các hàm neg_doc / sym_doc bên dưới viết lại đúng logic từng dòng của
  Code/generate_neg_consis.py và Code/generate_sym_consis.py, rồi được KIỂM CHỨNG
  bằng cách so với file tác giả công bố (xem phần SELF-CHECK ở cuối).

Cách chạy (từ thư mục gốc của repo):
    pip install numpy pandas openpyxl
    python demo/demo_transformations.py --doc 0      # Lockheed Martin (Industrials)
    python demo/demo_transformations.py --doc 2      # McDonald's (Consumer Discretionary)

Cột của file .npy:  [0] ngày  [1] nhãn dạng CHUỖI '0.0' (giảm) / '1.0' (tăng)
                    [2] tên công ty (không phải ticker)  [3] toàn văn transcript
"""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CODE, DATA = ROOT / "Code", ROOT / "Data"
MAX_SHOW = 150  # cắt ngắn dòng khi in ra cho dễ đọc


def load_module(name, path):
    """Import một file .py của tác giả theo đường dẫn (các file đều có guard __main__)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


neg_mod = load_module("fintrust_neg", CODE / "generate_neg_consis.py")
sym_mod = load_module("fintrust_sym", CODE / "generate_sym_consis.py")


def short(s, n=MAX_SHOW):
    s = s.replace("\n", "⏎")
    return s if len(s) <= n else s[: n - 1] + "…"


# --------------------------------------------------------------------------- #
# NEGATION  (viết lại make_neg() của tác giả cho MỘT văn bản)
# --------------------------------------------------------------------------- #
def neg_lines(text):
    """Tách văn bản thành các 'dòng' đúng như tác giả: thêm '.' trước mỗi '\\n' rồi split."""
    return text.replace("\n", ".\n").split("\n")


def neg_doc(text):
    out = ""
    for line in neg_lines(text):
        out += neg_mod.replace_words(line) + " "
    return out.replace(". ", "\n")


def flip_label(label):
    return "0.0" if label == "1.0" else "1.0"  # đúng như tác giả: mọi giá trị khác '1.0' -> '1.0'


# --------------------------------------------------------------------------- #
# SYMMETRIC  (viết lại make_sym() của tác giả cho MỘT văn bản)
# --------------------------------------------------------------------------- #
def sym_line(line):
    parts = sym_mod.split_into_sub_sentences(line.lower())  # tách sau ", " hoặc ". "
    parts[-1] = parts[-1][:-1] + ","                         # dấu '.' cuối -> ','
    parts[-1] += " "
    out = ""
    for k in range(len(parts)):
        if k == len(parts) - 1:          # phần ĐẦU TIÊN của câu gốc, nay đứng cuối
            out += parts[-k - 1][:-2]    # bỏ ", " thừa
            out += ". "
        else:
            out += parts[-k - 1]
    return out


def sym_doc(text):
    lines = text.replace("\n", ".\n").split("\n")
    return "".join(sym_line(l) for l in lines).replace(". ", "\n")


# --------------------------------------------------------------------------- #
# TRANSITIVE  (mô phỏng generate_tra_consis.py, GIỮ NGUYÊN hành vi của script gốc)
# --------------------------------------------------------------------------- #
def tra_assignments(orig, header_bug=True):
    """
    Trả về, cho từng văn bản, (top_c, top_c_, bị_kế_thừa?).
    header_bug=True  : đọc top_company.xlsx như script gốc (dòng đầu bị coi là tiêu đề).
    header_bug=False : đọc với header=None (đủ cả 11 ngành).
    Biến top_c/top_c_ KHÔNG được reset giữa các văn bản trong script gốc, nên nếu ngành của
    văn bản hiện tại không có trong `top`, nó dùng lại giá trị của văn bản trước.
    """
    cons = pd.read_excel(CODE / "constituents-financials.xlsx").values
    top = pd.read_excel(CODE / "top_company.xlsx", header=None if not header_bug else 0).values
    top_c = top_c_ = None
    result = []
    for i in orig:
        sector = None
        for j in cons:
            if j[1] == i[2]:
                sector = j[2]
                break
        updated = False
        for j in top:
            if j[0] == sector:
                top_c, top_c_ = j[1], j[2]
                if j[1] == i[2]:               # công ty này CHÍNH LÀ top của ngành -> dùng hạng 2, 3
                    top_c, top_c_ = j[2], j[3]
                updated = True
        result.append((top_c, top_c_, not updated))
    return result, cons


def tra_line(line, top_c, top_c_):
    return (line.replace(top_c, top_c_).lower()
                .replace(" we ", " " + top_c + " ")
                .replace(" our ", " " + top_c + "'s ").lower())


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", type=int, default=0, help="chỉ số văn bản trong test set (0..112)")
    ap.add_argument("--selfcheck", type=int, default=5, help="số văn bản đầu dùng để đối chiếu file tác giả")
    args = ap.parse_args()

    orig = np.load(DATA / "earnings_call_3days.npy")  # (113, 4), dtype chuỗi -> không cần pickle
    d = args.doc
    date, label, company, text = orig[d]
    lines = text.split("\n")
    print("=" * 100)
    print(f"VĂN BẢN #{d}: {company} | ngày {date} | nhãn gốc {label} "
          f"({'giá GIẢM' if label == '0.0' else 'giá TĂNG'}) | {len(lines)} dòng | {len(text):,} ký tự")
    print("=" * 100)

    # ---- 1. NEGATION -------------------------------------------------------
    print("\n[1] NEGATION — thay từ bằng từ trái nghĩa, LẬT nhãn")
    print(f"    Nhãn: {label} -> {flip_label(label)}   (script lật nhãn cho MỌI văn bản)")
    shown = 0
    changed = 0
    ls = neg_lines(text)
    for l in ls:
        new = neg_mod.replace_words(l)
        if new != l.lower():
            changed += 1
            if shown < 5:
                print(f"    - TRƯỚC: {short(l)}\n      SAU  : {short(new)}")
                shown += 1
    print(f"    => {changed}/{len(ls)} dòng của văn bản này bị thay từ ({changed/len(ls):.0%})")

    # ---- 2. SYMMETRIC ------------------------------------------------------
    print("\n[2] SYMMETRIC — đảo thứ tự các mệnh đề trong mỗi dòng, GIỮ nhãn")
    shown = 0
    for l in text.replace("\n", ".\n").split("\n"):
        if "," in l and shown < 4:
            print(f"    - TRƯỚC: {short(l)}\n      SAU  : {short(sym_line(l))}")
            shown += 1

    # ---- 3. ADDITIVE -------------------------------------------------------
    print("\n[3] ADDITIVE — ghép với văn bản KẾ TIẾP có CÙNG nhãn, GIỮ nhãn")
    same = [k for k in range(len(orig)) if (orig[k][1] == "0.0") == (label == "0.0")]
    pos = same.index(d)
    nxt = same[(pos + 1) % len(same)]
    n1, n2 = len(text.split("\n")), len(orig[nxt][3].split("\n"))
    ok = n1 + n2 < 512
    print(f"    Nhóm cùng nhãn {label}: {len(same)} văn bản; đối tác của #{d} là #{nxt}: "
          f"{orig[nxt][2]} ({orig[nxt][0]})")
    print(f"    Số dòng: {n1} + {n2} = {n1+n2}  -> {'< 512: GHÉP' if ok else '>= 512: KHÔNG ghép, giữ nguyên văn bản gốc'}")
    if ok:
        merged_len = len((text + "\n" + orig[nxt][3]))
        print(f"    Độ dài sau ghép: {merged_len:,} ký tự (gốc {len(text):,})")

    # ---- 4. TRANSITIVE -----------------------------------------------------
    print("\n[4] TRANSITIVE — thay 'we'/'our' bằng công ty đứng đầu cùng ngành, GIỮ nhãn")
    asg, cons = tra_assignments(orig, header_bug=True)
    asg_fix, _ = tra_assignments(orig, header_bug=False)
    sector = next((r[2] for r in cons if r[1] == company), "??")
    top_c, top_c_, stale = asg[d]
    print(f"    Ngành của {company}: {sector}")
    print(f"    Script gốc dùng: 'we' -> '{top_c}'" + ("   <-- KẾ THỪA TỪ VĂN BẢN TRƯỚC (lỗi header)" if stale else ""))
    if stale:
        print(f"    Nếu đọc top_company.xlsx đúng (header=None) thì sẽ là: '{asg_fix[d][0]}'")
    example = next((l for l in lines if " we " in l.lower() or " our " in l.lower()), None)
    if example:
        print(f"    - TRƯỚC: {short(example)}\n      SAU  : {short(tra_line(example, top_c, top_c_))}")
    n_stale = sum(1 for a in asg if a[2])
    n_stale_fix = sum(1 for a in asg_fix if a[2])
    print(f"    Toàn test set: {n_stale}/{len(orig)} văn bản ({n_stale/len(orig):.0%}) dùng công ty kế thừa SAI "
          f"theo script gốc; sau khi sửa header: {n_stale_fix}/{len(orig)}")

    # ---- SELF-CHECK --------------------------------------------------------
    print("\n[SELF-CHECK] Đối chiếu bản viết lại với file tác giả công bố")
    neg_ref = np.load(DATA / "neg_earnings_call_3days.npy", mmap_mode="r")
    sym_ref = np.load(DATA / "sym_earnings_call_3days.npy", mmap_mode="r")
    for k in range(min(args.selfcheck, len(orig))):
        assert neg_doc(orig[k][3]) == neg_ref[k][3], f"neg_doc khác file tác giả ở văn bản {k}"
        assert flip_label(orig[k][1]) == neg_ref[k][1], f"nhãn neg khác ở văn bản {k}"
        assert sym_doc(orig[k][3]) == sym_ref[k][3], f"sym_doc khác file tác giả ở văn bản {k}"
    print(f"    OK: neg_doc, flip_label, sym_doc khớp từng ký tự với file tác giả ở {args.selfcheck} văn bản đầu.")


if __name__ == "__main__":
    main()
