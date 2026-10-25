import pickle, re, pathlib
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier

BASE = pathlib.Path(r"C:\Users\Dell\FinTrust")
PKL = pathlib.Path(r"C:\Users\Dell\ACL2019\dataset_n3.pkl")
N_DAYS, SEEDS = 3, range(10)

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

def trade_return(comp, d):
    t = name2t.get(comp) or name2t_n.get(norm(comp))
    if not t or t not in close.columns:
        return None
    s = close[t].dropna()
    if s.empty:
        return None
    pos = s.index.searchsorted(d)
    tp = s.index.searchsorted(d + pd.Timedelta(days=N_DAYS))
    if pos >= len(s) or tp >= len(s) or pos == 0:
        return None
    return s.iloc[tp] / s.iloc[pos] - 1.0

D = pickle.load(open(PKL, "rb"))
train, val, test = D["train"], D["val"], D["test"]
keys = list(test["orig"].keys())
print("vi du khoa test:", keys[:2])

# ---- ghep gia cho test ----
ret = [trade_return(k[1], parse_date(k[0])) for k in keys]
use = np.array([r is not None for r in ret])
r_all = np.array([r if r is not None else np.nan for r in ret])
y = np.array([test["orig"][k][0] for k in keys])
print(f"Van ban test co gia: {use.sum()}/{len(keys)}")
agree = ((r_all[use] > 0).astype(int) == y[use]).sum()
print(f"Kiem tra: huong gia khop nhan tac gia {agree}/{use.sum()} (mong doi 85/85)")

# ---- huan luyen giong run_xgb_full.py ----
Xtr_t, ytr = [x[2] for x in train], np.array([x[3] for x in train])
Xva_t, yva = [x[2] for x in val], np.array([x[3] for x in val])
vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
Xtr = vec.fit_transform(Xtr_t); Xva = vec.transform(Xva_t)

def make(depth, trees, seed):
    return XGBClassifier(n_estimators=trees, max_depth=depth, learning_rate=0.05,
                         subsample=0.8, colsample_bytree=0.5, random_state=seed,
                         eval_metric="logloss")

best = None
for depth in (2, 3, 4):
    for trees in (100, 300):
        a = np.mean([(make(depth, trees, s).fit(Xtr, ytr).predict(Xva) == yva).mean()
                     for s in range(3)])
        if best is None or a > best[0]:
            best = (a, depth, trees)
print(f"Sieu tham so chon theo val: depth={best[1]}, trees={best[2]} (val ACC={best[0]:.3f})")

sets = ["orig", "add", "neg", "sym", "tra"]
X = {n: vec.transform([test[n][k][1] for k in keys]) for n in sets}
Y = {n: np.array([test[n][k][0] for k in keys]) for n in sets}

def profit_sharpe(pred, rets):
    side = np.where(pred == 1, 1.0, -1.0)          # 1 = mua, 0 = ban khong
    r = side * rets
    return r.mean() * 100, r.mean() / r.std(ddof=1)  # Profit Ratio (%), Sharpe (Rf=0)

# ---- chay 10 seed ----
res = {n: {"acc": [], "pr": [], "sh": []} for n in sets}
correct = np.zeros(len(keys))
for s in SEEDS:
    clf = make(best[1], best[2], s).fit(Xtr, ytr)
    for n in sets:
        p = clf.predict(X[n])
        res[n]["acc"].append((p == Y[n]).mean())
        pr, sh = profit_sharpe(p[use], r_all[use])
        res[n]["pr"].append(pr); res[n]["sh"].append(sh)
        if n == "orig":
            correct += (p == y)
correct /= len(list(SEEDS))

# ---- baseline ----
ru = r_all[use]
def base(pred_fn):
    return profit_sharpe(pred_fn(), ru)
buy = base(lambda: np.ones(len(ru), int))
short = base(lambda: np.zeros(len(ru), int))
rng = np.random.default_rng(0)
rnd = np.mean([profit_sharpe(rng.integers(0, 2, len(ru)), ru) for _ in range(2000)], axis=0)

print(f"\n=== Mo phong giao dich (n={N_DAYS} ngay, {use.sum()} van ban, dau tu deu moi co phieu) ===")
print(f"{'Chien luoc':<28}{'Profit Ratio %':>16}{'Sharpe':>10}")
print(f"{'Buy-all':<28}{buy[0]:>16.3f}{buy[1]:>10.3f}")
print(f"{'Short-sell-all':<28}{short[0]:>16.3f}{short[1]:>10.3f}")
print(f"{'Random (TB 2000 lan)':<28}{rnd[0]:>16.3f}{rnd[1]:>10.3f}")
for n in sets:
    pr, sh = np.array(res[n]["pr"]), np.array(res[n]["sh"])
    print(f"{'XGB-TFIDF tren ' + n:<28}{pr.mean():>10.3f}±{pr.std():.2f}{sh.mean():>8.3f}±{sh.std():.2f}")
print("(Bai bao Bang 3, n=3: Buy-all 3.681 / Short-sell-all -3.681 / Random -0.271)")

# ---- ACC + khoang tin cay bootstrap ----
print("\n=== ACC trung binh 10 seed, khoang tin cay 95% (bootstrap tren van ban) ===")
b = np.random.default_rng(1)
idx = b.integers(0, len(keys), (5000, len(keys)))
ci = np.percentile(correct[idx].mean(1), [2.5, 97.5])
down = (y == 0).astype(float)
ci_d = np.percentile(down[idx].mean(1), [2.5, 97.5])
print(f"ACC orig            : {correct.mean():.3f}  CI [{ci[0]:.3f}, {ci[1]:.3f}]")
print(f"Doan toan 'giam'    : {down.mean():.3f}  CI [{ci_d[0]:.3f}, {ci_d[1]:.3f}]")
diff = (correct - down)[idx].mean(1)
print(f"Hieu orig - 'giam'  : {correct.mean()-down.mean():+.3f}  CI [{np.percentile(diff,2.5):+.3f}, {np.percentile(diff,97.5):+.3f}]")
print("Neu CI cua hieu chua 0 -> khong ket luan duoc mo hinh tot hon doan toan 'giam'.")