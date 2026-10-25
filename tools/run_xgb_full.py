import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
from xgboost import XGBClassifier

D = pickle.load(open(r"C:\Users\Dell\ACL2019\dataset_n3.pkl", "rb"))
train, val, test = D["train"], D["val"], D["test"]
Xtr_t, ytr = [x[2] for x in train], np.array([x[3] for x in train])
Xva_t, yva = [x[2] for x in val], np.array([x[3] for x in val])

vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words="english")
Xtr = vec.fit_transform(Xtr_t)
Xva = vec.transform(Xva_t)

def make(depth, trees, seed):
    return XGBClassifier(n_estimators=trees, max_depth=depth, learning_rate=0.05,
                         subsample=0.8, colsample_bytree=0.5, random_state=seed,
                         eval_metric="logloss")

# chon sieu tham so tren val (trung binh 3 seed)
best = None
print("chon sieu tham so tren val (49 mau, nhieu):")
for depth in (2, 3, 4):
    for trees in (100, 300):
        acc = np.mean([accuracy_score(yva, make(depth, trees, s).fit(Xtr, ytr).predict(Xva))
                       for s in range(3)])
        print(f"  depth={depth} trees={trees} val ACC={acc:.3f}")
        if best is None or acc > best[0]:
            best = (acc, depth, trees)
print("chon:", best)
_, depth, trees = best

keys = list(test["orig"].keys())
y = np.array([test["orig"][k][0] for k in keys])
print("\ntest: so van ban", len(keys), "| doan toan 'giam' ACC =", round((y == 0).mean(), 3))
sets = ["orig", "add", "neg", "sym", "tra"]
X = {n: vec.transform([test[n][k][1] for k in keys]) for n in sets}
Y = {n: np.array([test[n][k][0] for k in keys]) for n in sets}

rows = []
for seed in range(10):
    clf = make(depth, trees, seed).fit(Xtr, ytr)
    P = {n: clf.predict(X[n]) for n in sets}
    r = {}
    for n in sets:
        r[n] = (accuracy_score(Y[n], P[n]), f1_score(Y[n], P[n], zero_division=0),
                matthews_corrcoef(Y[n], P[n]))
    for n in ("add", "sym", "tra"):
        r[n + "_c"] = float((P[n] == P["orig"]).mean())
    r["neg_c"] = float((P["neg"] != P["orig"]).mean())
    rows.append(r)

def ms(f):
    v = np.array([f(r) for r in rows])
    return f"{v.mean():.3f} ± {v.std():.3f}"

print(f"\n=== XGBoost + TF-IDF | train {len(train)} | val {len(val)} | test 113 | n=3 | 10 seed ===")
print("Bo       ACC            F1             MCC")
for n in sets:
    print(f"{n:6s} {ms(lambda r: r[n][0])}  {ms(lambda r: r[n][1])}  {ms(lambda r: r[n][2])}")
for i, name in enumerate(("ACC", "F1", "MCC")):
    print(f"trung binh 4 bo bien doi - {name}:", ms(lambda r: np.mean([r[n][i] for n in sets[1:]])))
print("\nConsis tung phep (Neg: ti le doi du doan; con lai: ti le giu du doan)")
for n, k in (("add", "add_c"), ("neg", "neg_c"), ("sym", "sym_c"), ("tra", "tra_c")):
    print(f"  {n}: {ms(lambda r: r[k])}")
print("  Consis tong:", ms(lambda r: np.mean([r[k] for k in ("add_c", "neg_c", "sym_c", "tra_c")])))