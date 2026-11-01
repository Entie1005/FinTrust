import pickle, re, pathlib, warnings
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, matthews_corrcoef
from xgboost import XGBClassifier
warnings.filterwarnings("ignore")

BASE = pathlib.Path(r"C:\Users\Dell\FinTrust")
PKL = pathlib.Path(r"C:\Users\Dell\ACL2019\dataset_n3.pkl")
HORIZONS = (3, 7, 15, 30)
SEEDS = list(range(10))
SETS = ["orig", "add", "neg", "sym", "tra"]

close = pd.read_csv(BASE / "tools" / "prices_close.csv", index_col=0, parse_dates=True)
m = pd.read_csv(BASE / "tools" / "name_map.csv", keep_default_na=False)
name2t = {n: str(t).replace(".", "-") for n, t in zip(m["name"], m["ticker"]) if t}
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
name2t_n = {norm(n): t for n, t in name2t.items()}
print("Gia den ngay:", close.index.max().date())


def parse_date(x):
    try:
        return pd.to_datetime(str(x), format="%Y%m%d")
    except Exception:
        return pd.to_datetime(str(x))


def price_pair(comp, d, n):
    t = name2t.get(comp) or name2t_n.get(norm(comp))
    if not t or t not in close.columns:
        return None
    s = close[t].dropna()
    if s.empty:
        return None
    pos = s.index.searchsorted(d)
    tp = s.index.searchsorted(d + pd.Timedelta(days=n))
    if pos == 0 or pos >= len(s) or tp >= len(s):
        return None
    return s.iloc[pos], s.iloc[tp]


def profit_sharpe(pred, rets):
    r = np.where(pred == 1, 1.0, -1.0) * rets
    sd = r.std(ddof=1)
    return r.mean() * 100, (r.mean() / sd if sd > 0 else 0.0)


def make(depth, trees, seed):
    return XGBClassifier(n_estimators=trees, max_depth=depth, learning_rate=0.05,
                         subsample=0.8, colsample_bytree=0.5, random_state=seed,
                         eval_metric="logloss")


D = pickle.load(open(PKL, "rb"))
train_all, val_all, test = D["train"], D["val"], D["test"]
keys = list(test["orig"].keys())
dates = [parse_date(k[0]) for k in keys]


def lab(rows, n):
    out = []
    for ds, comp, txt, _ in rows:
        pp = price_pair(comp, parse_date(ds), n)
        if pp is not None:
            out.append((txt, int(pp[1] > pp[0])))
    return out


for n in HORIZONS:
    print("\n" + "=" * 70)
    print(f"KY HAN {n} NGAY")
    tr, va = lab(train_all, n), lab(val_all, n)
    pps = [price_pair(k[1], d, n) for k, d in zip(keys, dates)]
    mask = np.array([p is not None for p in pps])
    ret = np.array([(p[1] / p[0] - 1.0) if p else np.nan for p in pps])
    yn = np.array([int(p[1] > p[0]) if p else -1 for p in pps])
    print(f"train {len(tr)}/{len(train_all)} | val {len(va)}/{len(val_all)} | "
          f"test co nhan {mask.sum()}/{len(keys)}")
    ytr = np.array([y for _, y in tr]); yva = np.array([y for _, y in va])
    print(f"ti le nhan 'tang': train {ytr.mean():.3f} | val {yva.mean():.3f} | test {yn[mask].mean():.3f}")
    if len(set(ytr)) < 2:
        print("Chi co 1 lop trong train -> bo qua ky han nay"); continue

    vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
    Xtr = vec.fit_transform([t for t, _ in tr]); Xva = vec.transform([t for t, _ in va])
    best = None
    for depth in (2, 3, 4):
        for trees in (100, 300):
            a = np.mean([(make(depth, trees, s).fit(Xtr, ytr).predict(Xva) == yva).mean()
                         for s in range(3)])
            if best is None or a > best[0]:
                best = (a, depth, trees)
    print(f"sieu tham so: depth={best[1]}, trees={best[2]} (val ACC={best[0]:.3f})")

    X = {s: vec.transform([test[s][k][1] for k in keys]) for s in SETS}
    Y = {s: (1 - yn if s == "neg" else yn) for s in SETS}
    R = {s: {"acc": [], "f1": [], "mcc": [], "cons": [], "pr": [], "sh": []} for s in SETS}
    correct = np.zeros(mask.sum())
    for sd in SEEDS:
        clf = make(best[1], best[2], sd).fit(Xtr, ytr)
        P = {s: clf.predict(X[s]) for s in SETS}
        for s in SETS:
            p, yy = P[s][mask], Y[s][mask]
            R[s]["acc"].append((p == yy).mean())
            R[s]["f1"].append(f1_score(yy, p, zero_division=0))
            R[s]["mcc"].append(matthews_corrcoef(yy, p))
            R[s]["cons"].append(((P[s] != P["orig"]) if s == "neg" else (P[s] == P["orig"])).mean()
                                if s != "orig" else 1.0)
            pr, sh = profit_sharpe(p, ret[mask])
            R[s]["pr"].append(pr); R[s]["sh"].append(sh)
        correct += (P["orig"][mask] == yn[mask])
    correct /= len(SEEDS)

    f = lambda v: f"{np.mean(v):.3f}+-{np.std(v):.3f}"
    print(f"\n{'bo':<6}{'ACC':>14}{'F1':>14}{'MCC':>14}{'Consis*':>14}")
    for s in SETS:
        print(f"{s:<6}{f(R[s]['acc']):>14}{f(R[s]['f1']):>14}{f(R[s]['mcc']):>14}"
              f"{(f(R[s]['cons']) if s != 'orig' else '-'):>14}")
    cons_avg = np.mean([np.mean(R[s]["cons"]) for s in ("add", "neg", "sym", "tra")])
    print(f"Consis trung binh 4 phep: {cons_avg:.3f}   (*tinh tren tat ca {len(keys)} van ban)")

    ru = ret[mask]
    rng = np.random.default_rng(0)
    buy = profit_sharpe(np.ones(len(ru), int), ru)
    sho = profit_sharpe(np.zeros(len(ru), int), ru)
    rnd = np.mean([profit_sharpe(rng.integers(0, 2, len(ru)), ru) for _ in range(2000)], axis=0)
    print(f"\nGiao dich ({mask.sum()} lenh)   Profit%   Sharpe")
    print(f"{'Buy-all':<22}{buy[0]:>9.3f}{buy[1]:>9.3f}")
    print(f"{'Short-sell-all':<22}{sho[0]:>9.3f}{sho[1]:>9.3f}")
    print(f"{'Random':<22}{rnd[0]:>9.3f}{rnd[1]:>9.3f}")
    for s in SETS:
        print(f"{'XGB-TFIDF ' + s:<22}{np.mean(R[s]['pr']):>9.3f}{np.mean(R[s]['sh']):>9.3f}")

    b = np.random.default_rng(1)
    idx = b.integers(0, mask.sum(), (5000, mask.sum()))
    ci = np.percentile(correct[idx].mean(1), [2.5, 97.5])
    maj = max(yn[mask].mean(), 1 - yn[mask].mean())
    const = (yn[mask] == (1 if yn[mask].mean() >= 0.5 else 0)).astype(float)
    dci = np.percentile((correct - const)[idx].mean(1), [2.5, 97.5])
    print(f"\nACC orig {correct.mean():.3f} CI95 [{ci[0]:.3f},{ci[1]:.3f}] | "
          f"doan lop da so {maj:.3f}")
    print(f"Hieu ACC - lop da so: {correct.mean() - maj:+.3f} CI95 [{dci[0]:+.3f},{dci[1]:+.3f}]"
          f"  (CI chua 0 => khong ket luan duoc)")