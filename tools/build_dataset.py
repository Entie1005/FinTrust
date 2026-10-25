import re, pathlib, pickle
import numpy as np, pandas as pd

BASE = pathlib.Path(r"C:\Users\Dell\FinTrust")
TEXT = pathlib.Path(r"C:\Users\Dell\ACL2019\text")
OUT = pathlib.Path(r"C:\Users\Dell\ACL2019\dataset_n3.pkl")   # de ngoai repo

# 1. stock_movement_* thuc ra chua gi?
for n in (3, 7, 15, 30):
    a = np.load(BASE / "Data" / f"stock_movement_{n}days.npy", allow_pickle=True)
    vals, cnt = np.unique(a.astype(str), return_counts=True)
    print(f"stock_movement_{n}: dtype={a.dtype} shape={a.shape} "
          f"so gia tri khac nhau={len(vals)} -> {dict(zip(vals[:6], cnt[:6]))}")

# 2. nhan Yahoo cho cac van ban truoc ngay bat dau test
close = pd.read_csv(BASE / "tools" / "prices_close.csv", index_col=0, parse_dates=True)
m = pd.read_csv(BASE / "tools" / "name_map.csv", keep_default_na=False)
name2t = {n: str(t).replace(".", "-") for n, t in zip(m["name"], m["ticker"]) if t}

def label3(t, d):
    if t not in close.columns:
        return None
    s = close[t].dropna()
    if s.empty:
        return None
    idx = s.index
    pos = idx.searchsorted(d)
    tp = idx.searchsorted(d + pd.Timedelta(days=3))
    if pos == 0 or pos >= len(idx) or tp >= len(idx):
        return None
    return int(s.iloc[tp] > s.iloc[pos])

docs = []
for f in TEXT.rglob("TextSequence.txt"):
    mm = re.match(r"(.*)_(\d{8})$", f.parent.name)
    if not mm:
        continue
    comp, ds = mm.groups()
    lines = [l.strip() for l in f.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
    docs.append((ds, comp, "\n".join(lines), len(lines)))
docs.sort()

START = "20171024"
pre = [d for d in docs if d[0] < START]
lab, nolabel = [], []
for ds, comp, txt, nl in pre:
    y = label3(name2t.get(comp, ""), pd.Timestamp(ds))
    (lab if y is not None else nolabel).append((ds, comp, txt, y))
print("\nvan ban truoc", START, ":", len(pre))
print("  co nhan Yahoo:", len(lab), "| khong co gia (cong ty bien mat/loi ma):", len(nolabel))
print("  nhan 0 / 1:", sum(x[3] == 0 for x in lab), "/", sum(x[3] == 1 for x in lab))
print("  so van ban ngan (<10 dong) trong tap co nhan:",
      sum(len(x[2].split("\n")) < 10 for x in lab))
k = int(len(lab) * 7 / 8)
train, val = lab[:k], lab[k:]
print("  train:", len(train), "(", train[0][0], "->", train[-1][0], ")",
      "| val:", len(val), "(", val[0][0], "->", val[-1][0], ")")

# 3. test: giu nguyen cua tac gia (nhan that, 113 van ban) + 4 bo bien doi
test = {}
for name in ("earnings_call", "add_earnings_call", "neg_earnings_call",
             "sym_earnings_call", "tra_earnings_call"):
    fn = "earnings_call_3days.npy" if name == "earnings_call" else f"{name}_3days.npy"
    a = np.load(BASE / "Data" / fn, allow_pickle=True)
    key = "orig" if name == "earnings_call" else name.split("_")[0]
    test[key] = {(str(r[0]), str(r[2])): (int(float(r[1])), str(r[3])) for r in a}
    print("test", key, ":", len(test[key]), "van ban,",
          "nhan 1:", sum(v[0] for v in test[key].values()))

pickle.dump({"train": train, "val": val, "nolabel": nolabel, "test": test}, open(OUT, "wb"))
print("\nda luu:", OUT)