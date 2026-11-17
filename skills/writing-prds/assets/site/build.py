"""Build a PRD into a website: one page per section.

    python3 tools/site/build.py <repo> <out> [version]

The PRD has four parts, one page per section, in docs/<part>/<NN-section>.md (or .html).
The file names give the order. Every page gets the same top bar (home, where you are,
previous and next page). The home page gives the document's particulars (docs/about.md,
with {version}, {date} and {author} taken from the newest row of the revision table) and
its table of contents. The document's name is read from prd.json at the top of the repo.

A Markdown page may hold HTML for pictures, mock-ups and tables, and ```mermaid fences
for flowcharts. An HTML page at the top of the repo is page content with its own <title>
and <style>; these are listed under 附件.

Needs the `markdown` package (pip install markdown==3.7). Any static host can serve the
output; on Cloudflare Pages the build command is this script and the output folder `_site`.
"""

import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

NAME = "產品需求文件"  # replaced by "name" in the repo's prd.json
SHORT = "PRD"  # the short name a published copy keeps ("short" in prd.json)
# Flowcharts are drawn in the browser by mermaid: from tools/site/vendor/ when the file is
# there (no outside request), else from this address.
MERMAID_CDN = "https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"
PARTS = {
    "00-part-0": ("Part 0", "文件管理"),
    "01-part-1": ("Part 1", "背景需求：為什麼要做"),
    "02-part-2": ("Part 2", "需求詳述：要怎麼做"),
    "03-part-3": ("Part 3", "其他"),
}
APPENDIX = ("附件", "說明與附錄")
FONTS = "https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=JetBrains+Mono:wght@500;700&display=swap"

SHELL = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
{head}
</head>
<body>
{body}
</body>
</html>
"""

# What the Artifact tool's own shell gives a page; a page with its own <style> gets only this.
RESET = """
:root{color-scheme:light}
body{margin:0;font:14px system-ui,sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
.prd-nav{max-width:940px;margin:0 auto 28px;display:flex;flex-wrap:wrap;gap:4px 10px;
  font:500 14px/1.5 "Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif}
.prd-nav a{color:inherit;opacity:.7;text-underline-offset:3px}
.prd-nav a:hover,.prd-nav a:focus-visible{opacity:1}
.prd-nav span{opacity:.5}
@media print{.prd-nav{display:none}}
"""

TITLE = re.compile(r"<title>(.*?)</title>\s*", re.S)
FENCE = re.compile(r"^```mermaid\n(.*?)\n```$", re.S | re.M)


def html_fragment(source):
    text = source.read_text(encoding="utf-8")
    found = TITLE.search(text)
    title = found.group(1).strip() if found else source.stem
    return title, TITLE.sub("", text, count=1)


def need_markdown():
    """The Markdown library, or a plain word on how to get it."""
    try:
        import markdown
    except ImportError:
        sys.exit("建站需要 markdown 套件，請先執行：pip install markdown==3.7")
    return markdown


def markdown_page(source):
    markdown = need_markdown()

    text = source.read_text(encoding="utf-8")
    heading = re.search(r"^#\s+(.+)$", text, re.M)
    title = heading.group(1).strip() if heading else source.stem
    text = FENCE.sub(lambda m: f'<pre class="mermaid">{html.escape(m.group(1))}</pre>', text)
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists", "md_in_html", "attr_list"]
    )
    body = re.sub(r'href="((?!https?:)[^"#]+)\.md(#[^"]*)?"', r'href="\1.html\2"', body)
    body = body.replace("<table>", '<div class="wide"><table>').replace("</table>", "</table></div>")
    return title, body


def pages_of(repo):
    """Every page in reading order: dicts with source, target, part (key, label, subtitle)."""
    found = []
    docs = repo / "docs"
    for key, (label, subtitle) in PARTS.items():
        for path in sorted((docs / key).glob("*")) if (docs / key).is_dir() else []:
            if path.suffix in (".md", ".html"):
                target = path.relative_to(repo).with_suffix(".html").as_posix()
                found.append({"source": path, "target": target, "part": (key, label, subtitle)})
    for path in sorted(repo.glob("*.html")):
        if path.name != "index.html":
            found.append({"source": path, "target": path.name, "part": ("appendix", *APPENDIX), "own": True})
    return found


def link(here, there):
    """A relative link from one page of the site to another."""
    return "../" * here.count("/") + there


def top_bar(page, pages, number):
    here = page["target"]
    before = pages[number - 1] if number else None
    after = pages[number + 1] if number + 1 < len(pages) else None
    step = lambda other, text: (  # noqa: E731
        f'<a href="{link(here, other["target"])}" title="{html.escape(other["title"])}">{text}</a>'
        if other
        else f"<span>{text}</span>"
    )
    return (
        '<header class="prd-top"><div>'
        f'<a class="home" href="{link(here, "index.html")}">{NAME}</a>'
        f'<span class="where">{page["part"][1]}：{html.escape(page["part"][2].split("：")[0])}</span>'
        f'<span class="steps">{step(before, "← 上一頁")}{step(after, "下一頁 →")}'
        f"<span>{number + 1} / {len(pages)}</span></span></div></header>"
    )


def foot_bar(page, pages, number):
    here = page["target"]
    before = pages[number - 1] if number else None
    after = pages[number + 1] if number + 1 < len(pages) else None
    cell = lambda other, label, side: (  # noqa: E731
        f'<a class="{side}" href="{link(here, other["target"])}"><small>{label}</small>{html.escape(other["title"])}</a>'
        if other
        else "<span></span>"
    )
    return f'<nav class="prd-foot">{cell(before, "上一頁", "prev")}{cell(after, "下一頁", "next")}</nav>'


REVISION = re.compile(r"^\|\s*(\d+\.\d+)\s*\|\s*([\d-]+)\s*\|\s*([^|]+?)\s*\|", re.M)


def home_page(pages, repo, version):
    """The document's particulars, then its contents, part by part."""
    markdown = need_markdown()

    about = (repo / "docs" / "about.md").read_text(encoding="utf-8")
    revisions = (repo / "docs" / "00-part-0" / "01-revision-tracking.md").read_text(encoding="utf-8")
    newest = REVISION.search(revisions)  # the newest revision is the first row
    if newest is None:
        sys.exit("修訂追蹤表還沒有任何一列：請在 docs/00-part-0/01-revision-tracking.md 加上第一版")
    number, date, author = newest.groups()
    about = about.replace("{version}", number).replace("{date}", date).replace("{author}", author)
    body = ['<main class="doc home">', f"<h1>{NAME}</h1>"]
    body.append(markdown.markdown(about, extensions=["tables", "sane_lists", "attr_list"]).replace("<table>", '<table class="meta">', 1))
    body.append('<h2>目錄</h2><div class="wide"><table class="toc"><tbody>')
    groups = list(PARTS.items()) + [("appendix", APPENDIX)]
    for key, (label, subtitle) in groups:
        mine = [p for p in pages if p["part"][0] == key]
        if not mine:
            continue
        items = "".join(f'<li><a href="{p["target"]}">{html.escape(p["title"])}</a></li>' for p in mine)
        body.append(f"<tr><th>{label}<br><small>{html.escape(subtitle)}</small></th><td><ol>{items}</ol></td></tr>")
    body.append("</tbody></table></div>")
    body.append("</main>")
    if version:
        body.append(f"<footer>建置版本 {html.escape(version)}</footer>")
    return "\n".join(body)


def build(repo, out, version=""):
    global NAME, SHORT
    repo, out = Path(repo).resolve(), Path(out).resolve()
    settings = repo / "prd.json"
    if settings.exists():
        named = json.loads(settings.read_text(encoding="utf-8"))
        NAME, SHORT = named.get("name", NAME), named.get("short", SHORT)
    # Without a version given, the commit being built (Cloudflare Pages and GitHub Actions say).
    version = version or (os.environ.get("CF_PAGES_COMMIT_SHA") or os.environ.get("GITHUB_SHA") or "")[:7]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if (repo / "assets").is_dir():
        shutil.copytree(repo / "assets", out / "assets", ignore=shutil.ignore_patterns("*.md"))
    shutil.copy(Path(__file__).with_name("site.css"), out / "site.css")
    vendor = Path(__file__).with_name("vendor")
    if vendor.is_dir():  # mermaid served from the site itself
        shutil.copytree(vendor, out / "vendor")
    # Cloudflare Pages reads this file: no page is to be indexed.
    (out / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n")

    pages = pages_of(repo)
    for page in pages:
        reader = markdown_page if page["source"].suffix == ".md" else html_fragment
        page["title"], page["body"] = reader(page["source"])

    for number, page in enumerate(pages):
        here = page["target"]
        if page.get("own"):
            head = f"<style>{RESET}</style>"
            trail = (
                f'<nav class="prd-nav" aria-label="位置"><a href="{link(here, "index.html")}">{NAME}</a>'
                f"<span>/</span><span>{html.escape(page['title'])}</span></nav>"
            )
            body = trail + page["body"]
        else:
            head = f'<link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="{link(here, "site.css")}">'
            body = (
                top_bar(page, pages, number)
                + f'<main class="doc">{page["body"]}</main>'
                + foot_bar(page, pages, number)
            )
            if 'class="mermaid"' in body:
                script = link(here, "vendor/mermaid.min.js") if vendor.is_dir() else MERMAID_CDN
                body += (
                    f'<script src="{script}"></script><script>mermaid.initialize('
                    '{startOnLoad:true,theme:"neutral",flowchart:{curve:"linear",htmlLabels:true}});</script>'
                )
        text = SHELL.format(title=html.escape(page["title"]) + f"｜{NAME}", head=head, body=body)
        (out / here).parent.mkdir(parents=True, exist_ok=True)
        (out / here).write_text(text, encoding="utf-8")

    home = home_page(pages, repo, version)
    head = f'<link rel="stylesheet" href="{FONTS}"><link rel="stylesheet" href="site.css">'
    (out / "index.html").write_text(SHELL.format(title=NAME, head=head, body=home), encoding="utf-8")
    # The same home page as page content only, for publishing the built site as an Artifact.
    # The Artifact keeps the short name it was first published under.
    style = Path(__file__).with_name("site.css").read_text(encoding="utf-8")
    (out / "_artifact.html").write_text(f'<title>{html.escape(SHORT)}</title>\n<link rel="stylesheet" href="{FONTS}">\n<style>{style}</style>\n{home}', encoding="utf-8")
    print(f"built {len(pages)} page(s) and the home page into {out}")


if __name__ == "__main__":
    # build.py [PRD folder] [output folder] [version]. With no folder given: the PRD this
    # script sits in (<PRD>/tools/site/), built into its _site/.
    given = sys.argv[1:4]
    prd = Path(given[0]) if given else Path(__file__).resolve().parents[2]
    build(prd, given[1] if len(given) > 1 else prd / "_site", *given[2:])
