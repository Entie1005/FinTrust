"""Chan doan: vi sao so lieu cua thuc nghiem khac bai bao.
Chay:  python tools\\run_why.py > tools\\why_out.txt
Chi doc du lieu (khong ghi de gi). Dung lai dung cach gan nhan cua run_horizons.py."""
import os, pickle, re, pathlib, warnings
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier
warnings.filterwarnings("ignore")

BASE = pathlib.Path(os.environ.get("FT_BASE", r"C:\Users\Dell\FinTrust"))
PKL = pathlib.Path(os.environ.get("FT_PKL", r"C:\Users\Dell\ACL2019\dataset_n3.pkl"))
HORIZONS = (3, 7, 15, 30)
SEEDS = list(range(10))
SETS = ["orig", "add", "neg", "sym", "tra"]

close = pd.read_csv(BASE / "tools" / "prices_close.csv", index_col=0, parse_dates=True)
m = pd.read_csv(BASE / "tools" / "name_map.csv", keep_default_na=False)
name2t = {n: str(t).replace(".", "-") for n, t in zip(m["name"], m["ticker"]) if t}
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
name2t_n = {norm(n): t for n, t in name2t.items()}


def parse_date(x):
    try:
        return pd.to_datetime(str(x), format="%Y%m%d")
    except Exception:
        return pd.to_datetime(str(x))


def ticker_of(comp):
    return name2t.get(comp) or name2t_n.get(norm(comp))


def price_pair(comp, d, n):
    t = ticker_of(comp)
    if not t or t not in close.columns:
        return None
    s = close[t].dropna()
    if s.empty:
        return None
    pos = s.index.searchsorted(d); tp = s.index.searchsorted(d + pd.Timedelta(days=n))
    if pos == 0 or pos >= len(s) or tp >= len(s):
        return None
    return s.iloc[pos], s.iloc[tp]


def lab(rows, n):
    out = []
    for ds, comp, txt, _ in rows:
        pp = price_pair(comp, parse_date(ds), n)
        if pp is not None:
            out.append((txt, int(pp[1] > pp[0])))
    return out


D = pickle.load(open(PKL, "rb"))
train_all, val_all, test = D["train"], D["val"], D["test"]
keys = list(test["orig"].keys())
dates = [parse_date(k[0]) for k in keys]

# ---------------------------------------------------------------- A
print("=" * 70); print("A. VAN BAN TEST KHONG CO NHAN GIA (kep 113 -> 85)")
miss = []
for k, d in zip(keys, dates):
    why = None
    t = ticker_of(k[1])
    if not t: why = "khong co trong name_map.csv"
    elif t not in close.columns: why = f"ticker {t} khong co trong prices_close.csv"
    elif price_pair(k[1], d, 30) is None: why = f"{t}: thieu gia quanh ngay {d.date()} (+30)"
    if why: miss.append((k[0], k[1], why))
print(f"{len(miss)}/{len(keys)} van ban khong co nhan o ky han 30 ngay (hoac thieu ticker/gia):")
for r in miss: print("  ", r)
print("-> Neu bo sung ticker/gia cho cac cong ty nay, tap danh gia tang len gan 113 nhu bai bao.")

# ---------------------------------------------------------------- B
print("\n" + "=" * 70); print("B. TF-IDF CO 'THAY' DUOC SU BIEN DOI KHONG? (cosine voi van ban goc)")
tr3 = lab(train_all, 3)
vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
Xtr = vec.fit_transform([t for t, _ in tr3])
X = {s: vec.transform([test[s][k][1] for k in keys]) for s in SETS}
def rowcos(A, B):
    num = np.asarray(A.multiply(B).sum(1)).ravel()
    den = np.sqrt(np.asarray(A.multiply(A).sum(1)).ravel() * np.asarray(B.multiply(B).sum(1)).ravel())
    return num / np.maximum(den, 1e-12)
COS = {}
print(f"{'bo':<6}{'cos TB':>9}{'cos min':>9}{'vector y het goc':>20}")
for s in ("add", "neg", "sym", "tra"):
    c = rowcos(X["orig"], X[s]); COS[s] = c
    print(f"{s:<6}{c.mean():>9.4f}{c.min():>9.4f}{(c > 0.99999).mean():>19.1%}")
print("(sym phai ~1.000 vi TF-IDF la tui tu; tra/neg gan 1 nghia la bien doi chi dich vai dac trung)")

# ---------------------------------------------------------------- C, D
for n in HORIZONS:
    print("\n" + "=" * 70); print(f"KY HAN {n} NGAY")
    tr, va = lab(train_all, n), lab(val_all, n)
    pps = [price_pair(k[1], d, n) for k, d in zip(keys, dates)]
    mask = np.array([p is not None for p in pps])
    ret = np.array([(p[1] / p[0] - 1.0) if p else np.nan for p in pps])
    yn = np.array([int(p[1] > p[0]) if p else -1 for p in pps])
    ytr = np.array([y for _, y in tr]); yva = np.array([y for _, y in va])
    if len(set(ytr)) < 2: print("1 lop -> bo qua"); continue
    v = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
    Xt = v.fit_transform([t for t, _ in tr]); Xv = v.transform([t for t, _ in va])
    best = None
    for depth in (2, 3, 4):
        for trees in (100, 300):
            a = np.mean([(XGBClassifier(n_estimators=trees, max_depth=depth, learning_rate=0.05, subsample=0.8,
                          colsample_bytree=0.5, random_state=s, eval_metric="logloss").fit(Xt, ytr).predict(Xv) == yva).mean()
                         for s in range(3)])
            if best is None or a > best[0]: best = (a, depth, trees)
    XT = {s: v.transform([test[s][k][1] for k in keys]) for s in SETS}
    up = {s: [] for s in SETS}; flip = {s: [] for s in ("add", "neg", "sym", "tra")}
    fl_by_cos = {"tra_changed": [], "tra_same": []}
    for sd in SEEDS:
        clf = XGBClassifier(n_estimators=best[2], max_depth=best[1], learning_rate=0.05, subsample=0.8,
                            colsample_bytree=0.5, random_state=sd, eval_metric="logloss").fit(Xt, ytr)
        P = {s: clf.predict(XT[s]) for s in SETS}
        for s in SETS: up[s].append(P[s].mean())
        for s in flip: flip[s].append((P[s] != P["orig"]))
        ch = COS["tra"] < 0.99999
        fl_by_cos["tra_changed"].append((P["tra"] != P["orig"])[ch].mean() if ch.any() else np.nan)
        fl_by_cos["tra_same"].append((P["tra"] != P["orig"])[~ch].mean() if (~ch).any() else np.nan)
    print("C. Ti le du doan 'tang' (TB 10 seed):  " + "  ".join(f"{s}={np.mean(up[s]):.3f}" for s in SETS))
    print(f"   Ti le 'tang' that cua test: {yn[mask].mean():.3f}  | train: {ytr.mean():.3f}  | ACC neu luon doan 'tang': {yn[mask].mean():.3f}")
    print("   Ti le dao du doan so voi goc:  " + "  ".join(f"{s}={np.mean([f.mean() for f in flip[s]]):.3f}" for s in flip))
    print(f"   Transitive: dao du doan o van ban co vector DOI = {np.nanmean(fl_by_cos['tra_changed']):.3f}"
          f" | o van ban vector GIU NGUYEN = {np.nanmean(fl_by_cos['tra_same']):.3f}")
    ru = ret[mask]
    print(f"D. Buy-all: trung binh moi lenh = {ru.mean()*100:.3f}%  | TONG loi suat (R/I, I=1 co phieu) = {ru.sum():.3f}"
          f"  | N={mask.sum()}  (bai bao Bang 3: 3.681, khong ghi ky han, N co the = 113)")
print("\nDoc ket qua: xem muc 'Vi sao so lieu khac bai bao' trong bao cao.")
