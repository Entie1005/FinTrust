"""Doi chieu nhan 3 ngay tinh tu gia voi nhan cua tac gia cho 113 van ban test.
Chay:  python tools\\check_labels.py"""
import os, pickle, re, pathlib
import numpy as np, pandas as pd

BASE = pathlib.Path(os.environ.get("FT_BASE", r"C:\Users\Dell\FinTrust"))
PKL = pathlib.Path(os.environ.get("FT_PKL", r"C:\Users\Dell\ACL2019\dataset_n3.pkl"))
close = pd.read_csv(BASE / "tools" / "prices_close.csv", index_col=0, parse_dates=True)
m = pd.read_csv(BASE / "tools" / "name_map.csv", keep_default_na=False)
name2t = {n: str(t).replace(".", "-") for n, t in zip(m["name"], m["ticker"]) if t}
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
name2t_n = {norm(n): t for n, t in name2t.items()}

def parse_date(x):
    try: return pd.to_datetime(str(x), format="%Y%m%d")
    except Exception: return pd.to_datetime(str(x))

def price_label(comp, d, n=3):
    t = name2t.get(comp) or name2t_n.get(norm(comp))
    if not t or t not in close.columns: return None
    s = close[t].dropna()
    pos = s.index.searchsorted(d); tp = s.index.searchsorted(d + pd.Timedelta(days=n))
    if pos == 0 or pos >= len(s) or tp >= len(s): return None
    return int(s.iloc[tp] > s.iloc[pos])

def as01(v):
    try:
        f = float(v)
        return int(f) if f in (0.0, 1.0) else None
    except Exception:
        return None

D = pickle.load(open(PKL, "rb")); test = D["test"]["orig"]
keys = list(test.keys())
sample = test[keys[0]]
print("Cau truc 1 phan tu test:", type(sample).__name__, "len", len(sample), [type(x).__name__ for x in sample])
# tim chi so chua nhan 0/1 cua tac gia
idx = next((i for i in range(len(sample)) if all(as01(test[k][i]) is not None for k in keys)), None)
if idx is None:
    print("Khong tim thay cot nhan 0/1 trong du lieu test -> gui dong tren cho Claude."); raise SystemExit
print(f"Cot nhan cua tac gia: chi so {idx}")
auth = np.array([as01(test[k][idx]) for k in keys])
mine = [price_label(k[1], parse_date(k[0])) for k in keys]
ok = [(a, b) for a, b in zip(auth, mine) if b is not None]
agree = sum(int(a == b) for a, b in ok)
print(f"Nhan tac gia: {int(auth.sum())} tang / {len(auth) - int(auth.sum())} giam tren {len(auth)} van ban")
print(f"Khop nhan tu gia: {agree}/{len(ok)} ({len(keys) - len(ok)} van ban khong co nhan gia)")
for k, a, b in zip(keys, auth, mine):
    if b is not None and a != b: print("  LECH:", k, "tac gia =", a, "| tu gia =", b)
