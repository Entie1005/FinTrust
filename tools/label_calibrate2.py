import re, pathlib
import numpy as np, pandas as pd

BASE = pathlib.Path(r"C:\Users\Dell\FinTrust")
T = BASE / "tools"
close = pd.read_csv(T / "prices_close.csv", index_col=0, parse_dates=True)
m = pd.read_csv(T / "name_map.csv", keep_default_na=False)
xl = pd.read_excel(BASE / "Code" / "constituents-financials.xlsx")
RENAME = {"FB": "META", "ANTM": "ELV", "ABC": "COR", "CBG": "CBRE", "KORS": "CPRI",
          "HCN": "WELL", "HRS": "LHX", "FBHS": "FBIN", "PKI": "RVTY", "BLL": "BALL",
          "SYMC": "GEN", "CTL": "LUMN", "GPS": "GAP", "ADS": "BFH", "UTX": "RTX",
          "MYL": "VTRS", "BK": "BNY"}

def norm(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|the|group|holdings|holding)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

tab = {norm(n): s for n, s in zip(xl["Name"], xl["Symbol"])}
fold = {norm(n): t for n, t in zip(m["name"], m["ticker"]) if t}
def tk(c):
    t = fold.get(norm(c)) or tab.get(norm(c)) or ""
    return str(RENAME.get(t, t)).replace(".", "-")

ec = np.load(BASE / "Data" / "earnings_call.npy", allow_pickle=True)
print("earnings_call.npy shape:", ec.shape, "| dong dau:", ec[0][0], "|", ec[0][1])
dates = pd.to_datetime([str(r[0]) for r in ec])
comps = [str(r[1]) for r in ec]
tick = [tk(c) for c in comps]
mv = {n: np.array([int(float(x)) for x in
      np.load(BASE / "Data" / f"stock_movement_{n}days.npy", allow_pickle=True).flatten()])
      for n in (3, 7, 15, 30)}

e3 = np.load(BASE / "Data" / "earnings_call_3days.npy", allow_pickle=True)
lab3 = {(str(r[0]), str(r[2])): int(float(r[1])) for r in e3}
keys = [(str(r[0]), str(r[1])) for r in ec]
print("kiem tra thu tu moi (phai gan 1.0):",
      round(float(np.mean([lab3.get(k) == y for k, y in zip(keys, mv[3])])), 3))

def label(t, d, n, base, mode):
    if t not in close.columns:
        return None
    s = close[t].dropna()
    if s.empty:
        return None
    idx = s.index
    pos = idx.searchsorted(d)
    if pos >= len(idx) or pos == 0:
        return None
    b = s.iloc[pos] if base == "d" else s.iloc[pos - 1]
    tp = pos + n if mode == "trading" else idx.searchsorted(d + pd.Timedelta(days=n))
    if tp >= len(idx):
        return None
    return int(s.iloc[tp] > b)

print("\nn | co so sanh | cach dinh nghia              | khop")
for n in (3, 7, 15, 30):
    for base in ("d", "d-1"):
        for mode in ("trading", "calendar"):
            pr = [(label(t, d, n, base, mode), y) for t, d, y in zip(tick, dates, mv[n])]
            pr = [(a, y) for a, y in pr if a is not None]
            ag = sum(a == y for a, y in pr)
            print(f"{n:2d} | {len(pr):3d}/113 | goc={base:3s} ngay={mode:8s} | "
                  f"{ag}/{len(pr)} = {ag / max(len(pr), 1):.3f}")