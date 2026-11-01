from transformers import pipeline

ctxs = {
    "chi phi GIAM": "the cost of raw materials has been greatly decreased, so the expected return for the next quarter is {m} .",
    "chi phi TANG": "the cost of raw materials has been greatly increased, so the expected return for the next quarter is {m} .",
}
for name in ["bert-base-uncased", "roberta-base"]:
    fm = pipeline("fill-mask", model=name)
    sp = " " if "roberta" in name else ""
    targets = [sp + "higher", sp + "lower"]
    for label, c in ctxs.items():
        out = fm(c.format(m=fm.tokenizer.mask_token), targets=targets)
        p = {r["token_str"].strip(): r["score"] for r in out}
        print(f"{name:18s} | {label} | P(higher)={p['higher']:.4f}  P(lower)={p['lower']:.4f}")