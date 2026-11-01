"""
extension/negation_on_transcript.py

Áp luật Negation của FinTrust (hàm replace_words trong Code/generate_neg_consis.py)
lên MỘT transcript của dataset Kaggle "Earnings Call Transcripts - NASDAQ 2016-2020",
để xem luật này hoạt động thế nào trên dữ liệu MỚI (khác định dạng test set của tác giả).

GIỚI HẠN (đọc kỹ trước khi trình bày):
  * Đây là thử nghiệm trên VĂN BẢN. Dataset NASDAQ chưa có nhãn tăng/giảm giá cổ phiếu
    (cần ghép giá lịch sử theo ticker + ngày), nên chưa thể đo consistency của MÔ HÌNH nào.
  * Nếu có nhãn, Negation sẽ lật nhãn (0 <-> 1) như generate_neg_consis.py.

Khác biệt định dạng so với test set của tác giả:
  * Tác giả: mỗi dòng ~ một câu, không có tiêu đề diễn giả.
  * NASDAQ: mỗi dòng là một ĐOẠN (nhiều câu), có tiêu đề diễn giả "Tên   [số]", dòng kẻ ===/---,
    và khối Definitions/Disclaimer ở cuối. Vì vậy script này (1) cắt bỏ phần không phải lời nói,
    (2) tách đoạn thành CÂU rồi mới áp replace_words, để mỗi câu được thay tối đa một loại từ
    (đúng cơ chế if/elif của tác giả).

Cách chạy (từ thư mục gốc của repo):
    python extension/negation_on_transcript.py "đường/dẫn/2016-Apr-21-GOOGL.txt"
"""
import argparse
import difflib
import importlib.util
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "Code"


def load_replace_words():
    spec = importlib.util.spec_from_file_location("fintrust_neg", CODE / "generate_neg_consis.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.replace_words


def extract_sentences(raw):
    """Lấy các câu trong phần Presentation + Q&A, bỏ tiêu đề diễn giả, dòng kẻ và khối pháp lý."""
    start = raw.find("Presentation")
    end = raw.find("Definitions", start if start != -1 else 0)
    body = raw[start if start != -1 else 0: end if end != -1 else len(raw)]
    sentences = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.fullmatch(r"[=\-]{5,}", s):                 # dòng kẻ ==== hoặc ----
            continue
        if re.search(r"\[\d+\]\s*$", s):                  # tiêu đề diễn giả: "Ruth Porat, Alphabet - CFO   [4]"
            continue
        if s in ("Presentation", "Questions and Answers"):  # tiêu đề mục
            continue
        sentences.extend(p for p in re.split(r"(?<=[.!?])\s+", s) if p)
    return sentences


def first_change(old, new):
    """Cặp (từ cũ -> từ mới) đầu tiên khác nhau giữa hai câu, để thống kê luật nào được dùng nhiều."""
    a, b = old.lower().split(), new.split()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag != "equal":
            return " ".join(a[i1:i2]) + " → " + " ".join(b[j1:j2])
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript", help="đường dẫn tới 1 file transcript .txt của dataset NASDAQ")
    ap.add_argument("--examples", type=int, default=8, help="số ví dụ trước/sau cần in")
    args = ap.parse_args()

    replace_words = load_replace_words()
    raw = Path(args.transcript).read_text(encoding="utf-8", errors="replace")
    sentences = extract_sentences(raw)

    changed, pairs, examples = 0, Counter(), []
    seen_pairs = set()
    for s in sentences:
        new = replace_words(s)
        if new == s.lower():
            continue
        changed += 1
        pair = first_change(s, new)
        pairs[pair] += 1
        if pair not in seen_pairs and len(examples) < args.examples:   # mỗi cặp từ lấy 1 ví dụ cho đa dạng
            seen_pairs.add(pair)
            examples.append((s, new, pair))

    print(f"File: {Path(args.transcript).name}")
    print(f"Số câu trong phần lời nói: {len(sentences)}")
    print(f"Số câu bị thay từ: {changed} ({changed / max(len(sentences), 1):.1%})")
    print("Nhãn: (chưa có — cần ghép giá cổ phiếu; nếu có, Negation sẽ lật nhãn)\n")

    print("10 cặp thay thế được dùng nhiều nhất:")
    for pair, n in pairs.most_common(10):
        print(f"  {n:4d}  {pair}")

    print("\nVí dụ trước/sau (mỗi cặp từ một ví dụ):")
    for s, new, pair in examples:
        print(f"  [{pair}]")
        print(f"    TRƯỚC: {s[:200]}")
        print(f"    SAU  : {new[:200]}")


if __name__ == "__main__":
    main()
