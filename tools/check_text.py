import re, pathlib, collections
import numpy as np

ROOT = pathlib.Path(r"C:\Users\Dell\ACL2019\text")
TEST = r"C:\Users\Dell\FinTrust\Data\earnings_call_3days.npy"

recs = []
for f in ROOT.rglob("TextSequence.txt"):
    m = re.match(r"(.*)_(\d{8})$", f.parent.name)
    if m:
        recs.append((m.group(1), m.group(2), f))
    else:
        print("ten thu muc la:", f.parent.name)
print("so cuoc goi doc duoc:", len(recs))

dates = sorted(d for _, d, _ in recs)
print("ngay som nhat / muon nhat:", dates[0], dates[-1])

test = np.load(TEST, allow_pickle=True)
by_date = collections.defaultdict(list)
for r in test:
    first = str(r[3]).split("\n")[0].strip().lower()
    by_date[str(r[0]).replace("-", "")].append(first)
min_test = min(by_date)
print("ngay dau tien cua test set:", min_test, "| so van ban test:", len(test))
print("so cuoc goi tu ngay do tro di (trong Drive):", sum(d >= min_test for d in dates))

n_len = []
in_test = matched = 0
for comp, d, f in recs:
    lines = [l for l in f.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
    n_len.append(len(lines))
    if d in by_date:
        in_test += 1
        if lines and lines[0].strip().lower() in by_date[d]:
            matched += 1
print("so dong/van ban: min", min(n_len), "| trung vi", int(np.median(n_len)), "| max", max(n_len))
print("cuoc goi trung ngay voi test:", in_test, "| khop dong dau:", matched)