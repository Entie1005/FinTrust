import numpy as np, glob

for f in sorted(glob.glob("Data/*.npy")):
    a = np.load(f, allow_pickle=True)
    print("\n===", f)
    print("shape:", a.shape, "| dtype:", a.dtype)
    if a.size == 0:
        continue
    x = a.flat[0]
    print("kieu phan tu dau:", type(x).__name__)
    if isinstance(x, str):
        print("do dai:", len(x), "| dau:", x[:120].replace("\n", " "))
    elif isinstance(x, dict):
        print("cac khoa:", list(x.keys())[:10])
    if a.dtype != object and a.ndim <= 1:
        print("gia tri va so luong:", np.unique(a, return_counts=True))
    elif a.dtype != object:
        print("3 dong dau:", a[:3])