import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
from xgboost import XGBClassifier

DATA = Path(__file__).resolve().parent.parent / "Data"
N_SEEDS = 10
NAMES = ["add", "neg", "sym", "tra"]


def load(path):
    a = np.load(path, allow_pickle=True)
    # cot: 0 ngay | 1 nhan | 2 cong ty | 3 van ban
    return {(str(r[0]), str(r[2])): (int(float(r[1])), str(r[3])) for r in a}


orig = load(DATA / "earnings_call_3days.npy")
trans = {n: load(DATA / f"{n}_earnings_call_3days.npy") for n in NAMES}
keys = list(orig.keys())
y = np.array([orig[k][0] for k in keys])
txt = [orig[k][1] for k in keys]
print("so van ban goc:", len(keys), "| nhan 0:", int((y == 0).sum()), "| nhan 1:", int((y == 1).sum()))
for n in NAMES:
    print(f"bo {n}: {len(trans[n])} van ban, khop voi goc: {sum(k in trans[n] for k in keys)}")
print("Baseline doan toan 'giam' (lop da so): ACC =", round((y == 0).mean(), 3))


def metrics(yt, yp):
    return (accuracy_score(yt, yp), f1_score(yt, yp, zero_division=0), matthews_corrcoef(yt, yp))


rows = []
for seed in range(N_SEEDS):
    skf = StratifiedKFold(5, shuffle=True, random_state=seed)
    po = np.zeros(len(keys), int)
    pt = {n: np.full(len(keys), -1) for n in NAMES}
    for tr, te in skf.split(txt, y):
        vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
        Xtr = vec.fit_transform([txt[i] for i in tr])
        clf = XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.5,
                            random_state=seed, eval_metric="logloss")
        clf.fit(Xtr, y[tr])
        po[te] = clf.predict(vec.transform([txt[i] for i in te]))
        for n in NAMES:
            idx = [i for i in te if keys[i] in trans[n]]
            if idx:
                pt[n][idx] = clf.predict(vec.transform([trans[n][keys[i]][1] for i in idx]))
    r = {"orig": metrics(y, po)}
    accs = []
    for n in NAMES:
        m = np.where(pt[n] >= 0)[0]
        yt = np.array([trans[n][keys[i]][0] for i in m])  # nhan cua chinh bo bien doi (neg da lat)
        r[n] = metrics(yt, pt[n][m])
        accs.append(r[n][0])
        same = (pt[n][m] == po[m]).mean()
        r[n + "_consis"] = (1 - same) if n == "neg" else same
    r["avg_transformed_acc"] = np.mean(accs)
    rows.append(r)


def ms(f):
    v = np.array([f(r) for r in rows])
    return f"{v.mean():.3f} ± {v.std():.3f}"


print(f"\n=== XGBoost + TF-IDF, 5-fold CV, {N_SEEDS} seed, ky han 3 ngay ===")
print("Bo        ACC            F1             MCC")
for k in ["orig"] + NAMES:
    print(f"{k:6s}  {ms(lambda r: r[k][0])}  {ms(lambda r: r[k][1])}  {ms(lambda r: r[k][2])}")
print("ACC trung binh 4 bo bien doi:", ms(lambda r: r["avg_transformed_acc"]))
print("\nConsis tung phep (Neg: ti le doi du doan; con lai: ti le giu du doan)")
for n in NAMES:
    print(f"  {n}: {ms(lambda r: r[n + '_consis'])}")
print("  Consis tong:", ms(lambda r: np.mean([r[n + '_consis'] for n in NAMES])))