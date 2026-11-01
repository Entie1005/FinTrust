import numpy as np, pathlib

D = pathlib.Path(r"C:\Users\Dell\FinTrust\Data")
e3 = np.load(D / "earnings_call_3days.npy", allow_pickle=True)
ec = np.load(D / "earnings_call.npy", allow_pickle=True)

def ld(n):
    a = np.load(D / f"stock_movement_{n}days.npy", allow_pickle=True)
    return np.array([int(float(x)) for x in a.flatten()])

mv = {n: ld(n) for n in (3, 7, 15, 30)}
y3 = np.array([int(float(r[1])) for r in e3])
dates = [str(r[0]) for r in ec]
comps = [str(r[1]) for r in ec]
N = len(ec)

print("so nhan 1: earnings_call_3days =", int(y3.sum()),
      "| stock_movement_3 =", int(mv[3].sum()), "| (tong", N, ")")
print("earnings_call va earnings_call_3days cung thu tu:",
      all(str(a[0]) == str(b[0]) and str(a[1]) == str(b[2]) for a, b in zip(ec, e3)))
print("khop truc tiep (theo vi tri):", int((y3 == mv[3]).sum()), "/", N)

print("\n10 dong dau: i | ngay | cong ty | nhan(3days.npy) | stock_movement_3")
for i in range(10):
    print(i, "|", dates[i], "|", comps[i][:22], "|", y3[i], "|", mv[3][i])

orders = {
    "dao nguoc": list(range(N - 1, -1, -1)),
    "ten cong ty A-Z": sorted(range(N), key=lambda i: comps[i].lower()),
    "ten cong ty Z-A": sorted(range(N), key=lambda i: comps[i].lower(), reverse=True),
    "ngay giam dan": sorted(range(N), key=lambda i: dates[i], reverse=True),
    "ngay tang roi ten": sorted(range(N), key=lambda i: (dates[i], comps[i].lower())),
}
print("\nthu hoan vi: gia su stock_movement_3[k] ung voi dong p[k] cua earnings_call")
best = (0, None)
for name, p in orders.items():
    ag = float(np.mean([mv[3][k] == y3[p[k]] for k in range(N)]))
    print(f"  {name:20s} khop = {ag:.3f}")
    if ag > best[0]:
        best = (ag, name)
print("tot nhat:", best)