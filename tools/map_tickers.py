import re, pathlib, difflib
import pandas as pd

ROOT = pathlib.Path(r"C:\Users\Dell\ACL2019\text")
XLSX = r"C:\Users\Dell\FinTrust\Code\constituents-financials.xlsx"
OUT = r"C:\Users\Dell\FinTrust\tools\name_map.csv"

def norm(s):
    s = str(s).lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(inc|corp|corporation|co|company|ltd|plc|the|group|holdings|holding)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

df = pd.read_excel(XLSX)
print("cot:", df.columns.tolist())
table = {norm(n): s for n, s in zip(df["Name"], df["Symbol"])}

names = sorted({re.match(r"(.*)_\d{8}$", f.parent.name).group(1)
                for f in ROOT.rglob("TextSequence.txt")
                if re.match(r"(.*)_\d{8}$", f.parent.name)})
rows, exact, fuzzy, miss = [], 0, [], []
for n in names:
    k = norm(n)
    if k in table:
        exact += 1
        rows.append((n, table[k], "exact"))
        continue
    c = difflib.get_close_matches(k, table.keys(), n=1, cutoff=0.85)
    if c:
        fuzzy.append((n, c[0], table[c[0]]))
        rows.append((n, table[c[0]], "fuzzy"))
    else:
        miss.append(n)
        rows.append((n, "", "none"))

pd.DataFrame(rows, columns=["name", "ticker", "how"]).to_csv(OUT, index=False)
print("tong so cong ty:", len(names), "| khop chinh xac:", exact,
      "| khop gan dung:", len(fuzzy), "| khong khop:", len(miss))
print("gan dung (kiem tra bang mat):")
for a in fuzzy[:25]:
    print("  ", a)
print("khong khop:", miss[:40])