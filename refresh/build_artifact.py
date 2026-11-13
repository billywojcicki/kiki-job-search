"""Build the in-chat snapshot of the site: index.html with today's data baked in.

usage: python3 refresh/build_artifact.py [OUT_PATH]
Writes OUT_PATH (default: refresh/out/kiki-job-search.html, which is git-ignored).
The page is a body fragment (the Artifact tool adds the document wrapper);
a full standalone document is also written next to it as *-full.html.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "kiki-job-search.html")

html = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()


def data(name, optional=False):
    p = os.path.join(SITE, "data", name)
    if optional and not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


blob = {
    "jobs": data("jobs.json"), "facilities": data("facilities.json"), "updates": data("updates.json"),
    "meta": data("meta.json"), "gaps": data("gaps.json", optional=True) or {},
}
blob_js = json.dumps(blob, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

# 1. Read the baked-in data instead of fetching data/*.json.
old_fetch = 'Promise.all([get("data/jobs.json"), get("data/facilities.json"), get("data/updates.json"), get("data/meta.json"), optional("data/gaps.json")])'
assert old_fetch in html, "index.html load() changed; update build_artifact.py"
html = html.replace(old_fetch, "(window.KIKI_DATA ? Promise.resolve([KIKI_DATA.jobs, KIKI_DATA.facilities, KIKI_DATA.updates, KIKI_DATA.meta, KIKI_DATA.gaps]) : " + old_fetch + ")")

# 2. Theme: honor an explicit data-theme on <html> as well as the OS setting.
old_dark = "@media (prefers-color-scheme: dark) {\n  :root {"
assert old_dark in html, "index.html dark-mode block changed; update build_artifact.py"
m = re.search(r"@media \(prefers-color-scheme: dark\) \{\n  :root \{(.*?)\n  \}\n\}", html, re.S)
dark_vars = m.group(1)
html = html.replace(old_dark, '@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {', 1)
html = html.replace(m.group(0).replace(":root {", ':root:not([data-theme="light"]) {', 1),
                    m.group(0).replace(":root {", ':root:not([data-theme="light"]) {', 1)
                    + '\n:root[data-theme="dark"] {' + dark_vars + "\n}", 1)

# 3. Bake the data in, just before the first script.
inject = "<script>window.KIKI_DATA = " + blob_js + ";</script>\n"
i = html.index("<script")
html = html[:i] + inject + html[i:]

# Full standalone document (viewport-fit=cover is fine: body pads with env(safe-area-inset-*)).
os.makedirs(os.path.dirname(OUT), exist_ok=True)
full = OUT[:-5] + "-full.html" if OUT.endswith(".html") else OUT + "-full.html"
open(full, "w", encoding="utf-8").write(html)

# Body fragment for the Artifact tool: drop the document wrapper and head-only meta/link tags.
head = html[html.index("<head>") + 6: html.index("</head>")]
head = re.sub(r"<meta[^>]*>\s*", "", head)
head = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", head)
body = html[html.index("<body>") + 6: html.index("</body>")]
open(OUT, "w", encoding="utf-8").write(head.strip() + "\n" + body.strip() + "\n")
print(OUT)
print(full)
