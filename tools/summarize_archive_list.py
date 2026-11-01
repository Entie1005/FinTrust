import sys, collections, pathlib, os

raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8-sig", errors="ignore")
body = raw.replace("\r\n", "\n").split("----------", 1)[-1]

cnt, size = collections.Counter(), collections.Counter()
dirs, ex = set(), []
for block in body.split("\n\n"):
    d = dict(l.split(" = ", 1) for l in block.splitlines() if " = " in l)
    p = d.get("Path")
    if not p or d.get("Folder") == "+":
        continue
    e = pathlib.PurePath(p).suffix.lower() or "(khong co)"
    cnt[e] += 1
    size[e] += int(d.get("Size") or 0)
    if e == ".txt":
        dirs.add(os.path.dirname(p.replace("\\", "/")))
        if len(ex) < 3:
            ex.append(p)

print("so file theo duoi:", dict(cnt.most_common(6)))
print("dung luong (MB):", {k: round(v / 1e6) for k, v in size.most_common(6)})
print("so thu muc co file txt:", len(dirs))
print("vi du txt:", ex)