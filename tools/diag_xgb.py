import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier

D = pickle.load(open(r"C:\Users\Dell\ACL2019\dataset_n3.pkl", "rb"))
train, test = D["train"], D["test"]
ytr = np.array([x[3] for x in train])
keys = list(test["orig"].keys())
sets = ["orig", "add", "neg", "sym", "tra"]

for sw in ("english", None):
    vec = TfidfVectorizer(max_features=5000, min_df=2, sublinear_tf=True, stop_words=sw)
    Xtr = vec.fit_transform([x[2] for x in train])
    X = {n: vec.transform([test[n][k][1] for k in keys]) for n in sets}
    up = {n: [] for n in sets}
    c = {k: [] for k in ("add", "neg", "sym", "tra")}
    for seed in range(10):
        clf = XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.5, random_state=seed,
                            eval_metric="logloss").fit(Xtr, ytr)
        P = {n: clf.predict(X[n]) for n in sets}
        for n in sets:
            up[n].append(P[n].mean())
        for n in ("add", "sym", "tra"):
            c[n].append((P[n] == P["orig"]).mean())
        c["neg"].append((P["neg"] != P["orig"]).mean())
    print(f"\n=== stop_words = {sw} ===")
    print("ti le du doan 'tang':", {n: round(float(np.mean(v)), 3) for n, v in up.items()})
    print("Consis:", {n: round(float(np.mean(v)), 3) for n, v in c.items()})