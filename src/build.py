"""Build the Elite Trip site from template.html + offers.json.

python3 -I build.py                 -> writes ../index.html (uses assets/ paths)
python3 -I build.py PREVIEW.html    -> also writes a single self-contained preview (data URIs) for the Artifact
"""
import base64, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
A = os.path.join(SITE, "assets")
tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
data = json.load(open(os.path.join(HERE, "offers.json"), encoding="utf-8"))
credits = {}
cp = os.path.join(A, "photos", "credits.json")
if os.path.exists(cp):
    credits = json.load(open(cp, encoding="utf-8"))

def uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

keys = {g["img"] for g in data["groups"]} | {e["img"] for e in data["events"]}
flags = {v["f"] for v in data["visas"]}

def build(inline):
    s = tpl
    ref = (lambda p, m: uri(os.path.join(A, p), m)) if inline else (lambda p, m: "assets/" + p)
    for k, p, m in [("EMBLEM_W", "emblem-white.png", "image/png"), ("EMBLEM", "emblem.png", "image/png"),
                    ("LOGO", "logo.png", "image/png"), ("NAKHOB_HEAD", "nakhob-head.png", "image/png"),
                    ("NAKHOB", "nakhob.webp", "image/webp")]:
        s = s.replace("{{%s}}" % k, ref(p, m))
    imgs = {k: ref(f"photos/{k}.webp", "image/webp") for k in keys if os.path.exists(os.path.join(A, "photos", f"{k}.webp"))}
    fl = {f: ref(f"flags/{f}.svg", "image/svg+xml") for f in flags if os.path.exists(os.path.join(A, "flags", f"{f}.svg"))}
    s = s.replace("{{DATA}}", json.dumps(data, ensure_ascii=False))
    s = s.replace("{{IMGMAP}}", json.dumps(imgs)).replace("{{FLAGMAP}}", json.dumps(fl))
    used = [credits[k] for k in sorted(keys) if k in credits and k in imgs]
    if used:
        line = "صور المعالم من ويكيميديا كومنز: " + "، ".join(
            f'<a href="{c["page"]}" target="_blank" rel="noopener">{c["title"]}</a> ({c["artist"] or "مجهول"}، {c["license"]})' for c in used)
        s = s.replace("</footer>", f'<div class="wrap credits">{line}</div>\n</footer>', 1)
    assert "{{" not in s, re.findall(r"\{\{\w+\}\}", s)
    return s

def standalone(s):
    title = re.search(r"<title>.*?</title>", s).group(0)
    s = s.replace(title, "", 1)
    head, rest = s.split("</style>", 1)
    body = rest.replace('<div dir="rtl" lang="ar">', "", 1)
    k = body.rindex("</div>\n\n<script>")
    body = body[:k] + "\n<script>" + body[k + len("</div>\n\n<script>"):]
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="رحلة النخبة للسفر والسياحة (Elite Trip)، بغداد: كروبات سياحية، حفلات، وفيزا.">
<link rel="icon" href="assets/emblem.png">
{title}
{head}
img{{max-width:100%}} [hidden]{{display:none!important}} body{{margin:0}}
</style>
</head>
<body>{body}
</body>
</html>
'''

open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(standalone(build(False)))
print("wrote index.html")
if len(sys.argv) > 1:
    open(sys.argv[1], "w", encoding="utf-8").write(build(True))
    print("wrote", sys.argv[1])
