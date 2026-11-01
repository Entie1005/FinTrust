"""Ve cac hinh cua bao cao TU DONG tu tools/horizons_out.txt (log cua run_horizons.py).
Chay:  python tools\\plot_figures.py        -> ghi 4 file PNG vao docs\\fig\\
Khong gõ tay so nao: moi so duoc doc tu log."""
import re, pathlib, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = pathlib.Path(__file__).resolve().parent.parent
LOG = BASE / "tools" / "horizons_out.txt"
OUT = BASE / "docs" / "fig"; OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
C = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#7F7F7F"]

# ---------- doc log ----------
txt = LOG.read_bytes().decode("utf-8", errors="ignore")
blocks = re.split(r"KY HAN (\d+) NGAY", txt)
H = {}
for i in range(1, len(blocks), 2):
    n, b = int(blocks[i]), blocks[i + 1]
    num = r"(-?\d+\.\d+)"
    d = {}
    for s in ("add", "neg", "sym", "tra"):
        m = re.search(rf"^{s}\s+\S+\s+\S+\s+\S+\s+{num}\+-", b, re.M)
        d[s] = float(m.group(1))
    d["buy"] = float(re.search(rf"^Buy-all\s+{num}", b, re.M).group(1))
    d["rnd"] = float(re.search(rf"^Random\s+{num}", b, re.M).group(1))
    d["mod"] = float(re.search(rf"^XGB-TFIDF orig\s+{num}", b, re.M).group(1))
    m = re.search(rf"ACC orig {num} CI95 \[{num},{num}\] \| doan lop da so {num}", b)
    d["acc"], d["lo"], d["hi"], d["maj"] = map(float, m.groups())
    H[n] = d
hz = sorted(H)
assert hz == [3, 7, 15, 30], f"log thieu ky han: {hz}"
print("Da doc log:", {n: H[n]["acc"] for n in hz})

# ---------- Hinh 3.1 so do quy trinh (ve lai theo mo ta bai bao) ----------
fig,ax=plt.subplots(figsize=(8.2,3.6)); ax.axis("off"); ax.set_xlim(0,100); ax.set_ylim(0,44)
def box(x,y,w,h,t,fc="#FFFFFF",ec="#333333",fs=9):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.4,rounding_size=1.2",fc=fc,ec=ec,lw=1.2))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs)
def arrow(x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=12,lw=1.2,color="#333333"))
box(1,17,18,10,"Transcript\ngốc x (113\nvăn bản test)","#E8F1F8",fs=8.5)
names=[("Negation: nhãn ĐỔI",C[3]),("Symmetric: nhãn GIỮ",C[0]),("Additive: nhãn GIỮ",C[2]),("Transitive: nhãn GIỮ",C[1])]
ys=[34,24,14,4]
for (n,c),y in zip(names,ys):
    box(26,y,22,7,n,"#FFFFFF",c)
    arrow(19.5,22,25.5,y+3.5)
    arrow(48.5,y+3.5,56.5,22)
box(57,17,17,10,"Mô hình f\nđã huấn luyện","#F3F3F3")
arrow(74.5,22,78.5,22)
box(79,14,20,16,"So sánh f(x)\nvà f(x′) theo\nkỳ vọng →\nConsis (TB\n4 điểm)","#FFF4DC",fs=8.5)
plt.savefig(OUT / "pipeline.png",dpi=200,bbox_inches="tight"); plt.close()

# ---------- Hinh 4.1 Consis ----------
labels = ["Additive", "Negation", "Symmetric", "Transitive"]
fig, ax = plt.subplots(figsize=(7.2, 3.6)); w = 0.2; x = np.arange(4)
for i, n in enumerate(hz):
    ax.bar(x + (i - 1.5) * w, [H[n][s] for s in ("add", "neg", "sym", "tra")], w, label=f"{n} ngày", color=C[i])
ax.set_xticks(x); ax.set_xticklabels(labels); ax.set_ylim(0, 1.1); ax.set_ylabel("Điểm Consis")
ax.axhline(1, color="#999999", lw=0.6, ls=":")
ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.15))
ax.yaxis.grid(True, lw=0.4, color="#DDDDDD"); ax.set_axisbelow(True)
plt.savefig(OUT / "consis.png", dpi=200, bbox_inches="tight"); plt.close()

# ---------- Hinh 4.2 ACC ----------
acc = [H[n]["acc"] for n in hz]; lo = [H[n]["lo"] for n in hz]; hi = [H[n]["hi"] for n in hz]; maj = [H[n]["maj"] for n in hz]
fig, ax = plt.subplots(figsize=(7.2, 3.6)); x = np.arange(4)
ax.errorbar(x, acc, yerr=[np.array(acc) - lo, np.array(hi) - acc], fmt="o", color=C[0], capsize=4, lw=1.5, ms=6, label="ACC mô hình (CI 95%)")
ax.plot(x, maj, "D", color=C[3], ms=7, label="Đoán lớp đa số")
ax.axhline(0.5, color="#999999", lw=0.8, ls="--")
ax.set_xticks(x); ax.set_xticklabels([f"{n} ngày" for n in hz]); ax.set_ylim(0.35, 0.7); ax.set_ylabel("Accuracy (85 văn bản)")
ax.legend(frameon=False, loc="upper left"); ax.yaxis.grid(True, lw=0.4, color="#DDDDDD"); ax.set_axisbelow(True)
plt.savefig(OUT / "acc.png", dpi=200, bbox_inches="tight"); plt.close()

# ---------- Hinh 4.3 Loi nhuan ----------
fig, ax = plt.subplots(figsize=(7.2, 3.6)); w = 0.26; x = np.arange(4)
ax.bar(x - w, [H[n]["buy"] for n in hz], w, label="Buy-all", color=C[0])
ax.bar(x, [H[n]["mod"] for n in hz], w, label="Mô hình (bộ gốc)", color=C[1])
ax.bar(x + w, [H[n]["rnd"] for n in hz], w, label="Random", color=C[4])
ax.axhline(0, color="#333333", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels([f"{n} ngày" for n in hz]); ax.set_ylabel("Lợi suất TB mỗi lệnh (%)")
ax.legend(frameon=False, loc="upper left"); ax.yaxis.grid(True, lw=0.4, color="#DDDDDD"); ax.set_axisbelow(True)
plt.savefig(OUT / "profit.png", dpi=200, bbox_inches="tight"); plt.close()
print("Xong:", OUT)
