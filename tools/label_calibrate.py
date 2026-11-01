import re, pathlib
import numpy as np, pandas as pd

BASE = pathlib.Path(r"C:\Users\Dell\FinTrust")
TOOLS = BASE / "tools"
MAP, PRICES = TOOLS / "name_map.csv", TOOLS / "prices_close.csv"
XLSX = BASE / "Code" / "constituents-financials.xlsx"

OVERRIDE = {"ABIOMED Inc": "ABMD", "Broadridge Financial Solutions": "BR",
            "Cboe Global Markets": "CBOE", "FleetCor Technologies Inc": "CPAY",
            "IPG Photonics Corp.": "IPGP", "MSCI Inc": "MSCI",
            "SVB Financial": "SVB", "Twitter, Inc.": "TWTR"}
# ma doi ten (tu tri nho, chua kiem chung; canh bao: MYL, BK kem chac)
RENAME = {"FB": "META", "ANTM": "ELV", "ABC": "COR", "CBG": "CBRE", "KORS": "CPRI",
          "HCN": "WELL", "HRS": "LHX", "FBHS": "FBIN", "PKI": "RVTY", "BLL": "BALL",
          "SYMC": "GEN", "CTL": "LUMN", "GPS": "GAP", "ADS": "BFH", "UTX": "RTX",
          "MYL": "VTRS", "BK": "BNY"}
# ma Yahoo da tra ve 'khong co du lieu' o lan chay truoc
SKIP = {"ABMD", "AET", "AGN", "ALXN", "ATVI", "CA", "CBS", "CELG", "CMA", "CTXS",
        "DISH", "EA", "FL", "FLIR", "GGP", "HBI", "HES", "HOLX", "IPG", "JNPR",
        "JWN", "K", "KSU", "MMC", "NBL", "NLSN", "RHT", "RTN", "SCG", "SEE",
        "SRCL", "STI", "SVB", "TIF", "TWTR", "VAR", "VIAB", "WBA", "XEC", "XLNX"}

def norm(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|the|group|holdings|holding)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def fix(t):
    return str(t).replace(".", "-")

m = pd.read_csv(MAP, keep_default_na=False)
t0 = [OVERRIDE.get(n, t) for n, t in zip(m["name"], m["ticker"])]
m["ticker"] = [RENAME.get(t, t) for t in t0]
m.to_csv(MAP, index=False)
tickers = sorted({fix(t) for t in m["ticker"] if t})
need = [t for t in tickers if t not in SKIP]

if not PRICES.exists():
    import yfinance as yf
    print("dang tai gia", len(need), "ma, lan luot, mat khoang 3-6 phut...")
    raw = yf.download(need, start="2016-12-15", end="2018-03-15",
                      auto_adjust=False, progress=False, threads=False)
    raw["Close"].to_csv(PRICES)
close = pd.read_csv(PRICES, index_col=0, parse_dates=True)
ok = [t for t in need if t in close.columns and close[t].notna().any()]
print("ma co gia:", len(ok), "/", len(need), "(da bo", len(SKIP), "ma bien mat tu truoc)")
print("ma van chua co gia:", [t for t in need if t not in ok])

# ---- nhan that cua tac gia tren 113 van ban test ----
test = np.load(BASE / "Data" / "earnings_call_3days.npy", allow_pickle=True)
dates = pd.to_datetime([str(r[0]) for r in test])
comps = [str(r[2]) for r in test]
xl = pd.read_excel(XLSX)
tab = {norm(n): s for n, s in zip(xl["Name"], xl["Symbol"])}
fold = {norm(n): t for n, t in zip(m["name"], m["ticker"]) if t}

def tk(c):
    t = fold.get(norm(c)) or tab.get(norm(c)) or ""
    return fix(RENAME.get(t, t))

tick = [tk(c) for c in comps]
print("van ban test khong tim ra ma:", sum(t == "" for t in tick))
print("van ban test co gia:", sum(t in ok for t in tick), "/ 113")

truth = {3: np.array([int(float(r[1])) for r in test])}
for n in (7, 15, 30):
    a = np.load(BASE / "Data" / f"stock_movement_{n}days.npy", allow_pickle=True)
    print(f"stock_movement_{n}days shape:", a.shape)
    if a.size == len(test):
        truth[n] = np.array([int(float(x)) for x in a.flatten()])
a3 = np.load(BASE / "Data" / "stock_movement_3days.npy", allow_pickle=True)
print("kiem tra thu tu: nhan 3 ngay khop earnings_call_3days:",
      (np.array([int(float(x)) for x in a3.flatten()]) == truth[3]).mean())

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
for n in sorted(truth):
    for base in ("d", "d-1"):
        for mode in ("trading", "calendar"):
            pairs = [(label(t, d, n, base, mode), y)
                     for t, d, y in zip(tick, dates, truth[n])]
            pairs = [(a, y) for a, y in pairs if a is not None]
            agree = sum(a == y for a, y in pairs)
            print(f"{n:2d} | {len(pairs):3d}/113 | goc={base:3s} ngay={mode:8s} | "
                  f"{agree}/{len(pairs)} = {agree / max(len(pairs), 1):.3f}")