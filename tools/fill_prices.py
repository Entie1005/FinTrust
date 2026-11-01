"""Bo sung gia cho 28 cong ty test con thieu -> du 113 van ban.
Chay:  python tools\\fill_prices.py
Buoc 1: thu Yahoo (yfinance).  Buoc 2: cong ty nao Yahoo khong co thi doc tools\\all_stocks_5yr.csv (Kaggle, neu co).
An toan: sao luu prices_close.csv -> prices_close_233.bak.csv, name_map.csv -> name_map.bak.csv truoc khi ghi."""
import os, sys, pathlib, shutil
import pandas as pd

BASE = pathlib.Path(os.environ.get("FT_BASE", r"C:\Users\Dell\FinTrust"))
TOOLS = BASE / "tools"
START, END = "2017-01-01", "2018-03-20"

# ten trong test  ->  ma (cac ma khac nhau theo nguon: Yahoo / Kaggle thang 2/2018)
NEW_NAMES = {   # 7 cong ty chua co trong name_map.csv
    "XL Group": "XL", "Amgen Inc.": "AMGN", "WestRock": "WRK", "Booking Holdings Inc": "BKNG",
    "Nektar Therapeutics": "NKTR", "Walmart": "WMT", "Ulta Beauty": "ULTA"}
TICKERS = ["XL", "AMGN", "WRK", "BKNG", "NKTR", "WMT", "ULTA",
           "FLIR", "HES", "NLSN", "VAR", "WBA", "ALXN", "CELG", "MMC", "RTN", "EA", "K", "HBI",
           "CBS", "HOLX", "SEE", "SRCL", "DISH", "JWN", "VIAB", "FL", "RHT"]
ALIAS = {"BKNG": ["BKNG", "PCLN"]}   # Booking cu ten Priceline (PCLN) truoc 2/2018


def from_yahoo(t):
    import yfinance as yf
    h = yf.Ticker(t).history(start=START, end=END, auto_adjust=False)
    if h is None or h.empty:
        return None
    s = h["Close"].copy()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s


def from_kaggle(t, kg):
    for a in ALIAS.get(t, [t]):
        x = kg[kg["Name"] == a]
        if len(x):
            return pd.Series(x["close"].values, index=pd.to_datetime(x["date"].values), name=t)
    return None


def main(fetch_yahoo=from_yahoo):
    pc = TOOLS / "prices_close.csv"; nm = TOOLS / "name_map.csv"
    for src_f, bak in ((pc, TOOLS / "prices_close_233.bak.csv"), (nm, TOOLS / "name_map.bak.csv")):
        if not bak.exists():          # chi sao luu ban goc mot lan
            shutil.copy(src_f, bak)
    close = pd.read_csv(pc, index_col=0, parse_dates=True)
    close.index = pd.to_datetime(close.index).normalize()
    kg_path = TOOLS / "all_stocks_5yr.csv"
    kg = pd.read_csv(kg_path) if kg_path.exists() else None
    got, failed = {}, []
    for t in TICKERS:
        if t in close.columns and close[t].notna().sum() > 100:
            continue
        s = None
        try:
            s = fetch_yahoo(t)
        except Exception as e:
            print(f"  {t}: Yahoo loi ({type(e).__name__})")
        src = "Yahoo"
        if s is None and kg is not None:
            s = from_kaggle(t, kg); src = "Kaggle"
        if s is None or s.dropna().empty:
            failed.append(t); print(f"  {t}: KHONG CO"); continue
        got[t] = s; print(f"  {t}: {src}  {s.index.min().date()} -> {s.index.max().date()}  ({len(s)} phien)")
    if got:
        add = pd.DataFrame(got)
        close = close.drop(columns=[c for c in add.columns if c in close.columns]).join(add, how="outer").sort_index()
        close.to_csv(pc)
    m = pd.read_csv(nm, keep_default_na=False)
    extra_col = m.columns[2] if len(m.columns) > 2 else None   # vd. cot 'exact' (kieu khop)
    n_set = 0
    for name, t in NEW_NAMES.items():
        hit = m.index[m["name"] == name]
        if len(hit):                         # ten da co nhung ticker dang TRONG -> dien vao
            for i in hit:
                if str(m.at[i, "ticker"]).strip() == "":
                    m.at[i, "ticker"] = t
                    if extra_col: m.at[i, extra_col] = "manual"
                    n_set += 1
        else:                                # ten chua co -> them dong moi
            row = {c: "" for c in m.columns}; row["name"] = name; row["ticker"] = t
            if extra_col: row[extra_col] = "manual"
            m = pd.concat([m, pd.DataFrame([row])], ignore_index=True); n_set += 1
    m.to_csv(nm, index=False)
    rows = range(n_set)
    print(f"\nDa them gia cho {len(got)} ma; dien/them {n_set} ten trong name_map.csv.")
    if failed:
        print("CHUA CO GIA:", failed)
        print("-> Tai Kaggle 'S&P 500 stock data' (camnugent/sandp500, file all_stocks_5yr.csv), dat vao tools\\, roi chay lai script nay.")
    else:
        print("Du gia. Chay lai: python tools\\run_why.py  (muc A phai bao 0/113 thieu)")


if __name__ == "__main__":
    main()
