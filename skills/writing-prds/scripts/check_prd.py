#!/usr/bin/env python3
"""Check a PRD for what a machine can see.

    python3 scripts/check_prd.py <PRD folder> [--final]

Three kinds of findings:
  必改    the document is broken or misleading as it stands (exit code 1)
  請看    probably a problem; a person decides
  未完成  placeholders still to be filled (必改 with --final, when the document is about
          to be handed over)

It does not judge whether the document is well written: that is what the standards in
references/ are for. It finds missing pieces, dead links, unfilled places, phrases that
say nothing, strings that look like real personal data, and module pages the module table
does not link to.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PARTS = ("00-part-0", "01-part-1", "02-part-2", "03-part-3")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
REVISIONS = "docs/00-part-0/01-revision-tracking.md"
REVISION_ROW = re.compile(r"^\|\s*(\d+\.\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([^|]+?)\s*\|", re.M)
NUMBERED = re.compile(r"^\d{2}-[a-z0-9-]+\.(md|html)$")
PLACEHOLDER = re.compile(r"〔[^〕]*〕|\{\{[A-Z]+\}\}|\bTODO\b|\bTBD\b|lorem ipsum", re.I)
MODULE_PAGE = re.compile(r"^\d{2}-module-")  # one page per module; the table is NN-modules.md
LINK = re.compile(r"\]\(((?!https?:|mailto:|#)[^)#\s]+)(#[^)]*)?\)")
# Words that say nothing by themselves (see references/standard-writing.md).
EMPTY_WORDS = ("賦能", "無縫", "一站式", "全方位", "強大的", "打造", "綜上所述", "值得注意的是", "總而言之")
# Fine with an object and a number after them; flagged so that somebody looks.
VAGUE = re.compile(r"(提升|優化|改善|強化)(整體)?(效率|流程|體驗|使用者體驗|品質)")
PICTURE = re.compile(r'<img|class="(web|tg|pipe|lanes|pair|spec|shot|money|year)|```mermaid|class="mermaid"')
PERSONAL = {
    "電子郵件": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "手機號碼": re.compile(r"(?<!\d)09\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)"),
    "身分證字號": re.compile(r"(?<![A-Za-z0-9])[A-Z][12]\d{8}(?!\d)"),
    "完整的帳號或卡號": re.compile(r"(?<![\d.,/-])\d{11,19}(?![\d.,])"),
}
EXAMPLE_HOSTS = ("example.com", "example.org", "example.net")


class Report:
    def __init__(self) -> None:
        self.found: dict[str, list[str]] = {"必改": [], "請看": [], "未完成": []}

    def add(self, kind: str, where: str, text: str) -> None:
        self.found[kind].append(f"{where}：{text}")


def visible(text: str) -> str:
    """The page without code blocks and HTML comments, where examples of bad wording live."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def check(root: Path, final: bool) -> Report:
    report = Report()
    docs = root / "docs"
    if not docs.is_dir():
        report.add("必改", str(root), "找不到 docs/ 資料夾。這是 PRD 的資料夾嗎？")
        return report
    if not (docs / "about.md").exists():
        report.add("必改", "docs/about.md", "沒有首頁。它放文件資訊與本版範圍")

    revisions = root / REVISIONS
    if not revisions.exists():
        report.add("必改", REVISIONS, "沒有修訂追蹤表")
    else:
        rows = REVISION_ROW.findall(revisions.read_text(encoding="utf-8"))
        if not rows:
            report.add("必改", REVISIONS, "表格裡讀不到任何一列（版本｜YYYY-MM-DD｜修訂人｜…）")
        else:
            versions = [tuple(int(n) for n in row[0].split(".")) for row in rows]
            if versions != sorted(versions, reverse=True):
                report.add("必改", REVISIONS, "最新的版本要在最上面一列")
            newest = next((l for l in revisions.read_text(encoding="utf-8").splitlines() if REVISION_ROW.match(l)), "")
            if final and "尚未審閱" in newest:
                report.add("請看", REVISIONS, "最新一版還寫著「尚未審閱」：負責人看過了嗎？看過就改成「已審閱（日期）」")

    pages = []
    for part in PARTS:
        folder = docs / part
        if not folder.is_dir():
            if part in ("00-part-0", "02-part-2"):
                report.add("必改", f"docs/{part}/", "少了這個 Part")
            continue
        taken: dict[str, str] = {}
        for path in sorted(folder.iterdir()):
            if path.is_dir() or path.name.startswith("."):
                continue
            where = path.relative_to(root).as_posix()
            if not NUMBERED.match(path.name):
                report.add("必改", where, "檔名要是「兩位數字-英文小寫與連字號.md」，數字決定順序")
                continue
            number = path.name[:2]
            if number in taken:
                report.add("必改", where, f"編號 {number} 和 {taken[number]} 重複，順序會不固定")
            taken[number] = path.name
            pages.append(path)

    for path in [docs / "about.md", *pages]:
        if not path.exists() or path.suffix != ".md":
            continue
        where = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if path.name != "about.md":
            first = next((line for line in lines if line.strip()), "")
            if not first.startswith("# "):
                report.add("必改", where, "第一行要是「# 標題」")
        for target, _anchor in LINK.findall(text):
            if not (path.parent / target).exists():
                report.add("必改", where, f"連結指向不存在的檔案：{target}")
        holes = len(PLACEHOLDER.findall(text))
        if holes:
            report.add("必改" if final else "未完成", where, f"還有 {holes} 處沒填")
        shown = visible(text)
        for number, line in enumerate(shown.splitlines(), 1):
            for word in EMPTY_WORDS:
                if word in line:
                    report.add("請看", f"{where}:{number}", f"「{word}」沒有資訊，改寫成它實際做的事")
            vague = VAGUE.search(line)
            if vague and not re.search(r"\d", line):
                report.add("請看", f"{where}:{number}", f"「{vague.group(0)}」：是誰的、哪一段、從多少到多少？")
            for kind, pattern in PERSONAL.items():
                for match in pattern.findall(line):
                    if kind == "電子郵件" and match.split("@")[-1] in EXAMPLE_HOSTS:
                        continue
                    report.add("請看", f"{where}:{number}", f"看起來像真實的{kind}（{match[:4]}…）：畫面與例子請用示範資料")
        if path.parent.name == "02-part-2" and MODULE_PAGE.match(path.name):
            if "驗收條件" not in text:
                report.add("必改" if final else "請看", where, "模組頁沒有「驗收條件」一節")
            if not PICTURE.search(text):
                report.add("請看", where, "這一頁沒有圖、畫面或流程：最重要的一件事能不能畫出來？")

    part2 = [p for p in pages if p.parent.name == "02-part-2" and p.suffix == ".md"]
    tables = [p for p in part2 if p.name.endswith("-modules.md")]
    modules = [p for p in part2 if MODULE_PAGE.match(p.name)]
    if modules and not tables:
        report.add("請看", "docs/02-part-2/", "有模組頁，但沒有功能模組表（NN-modules.md）可以總覽")
    for table in tables:
        linked = {target for target, _anchor in LINK.findall(table.read_text(encoding="utf-8"))}
        for page in modules:
            if page.name not in linked:
                where = table.relative_to(root).as_posix()
                report.add("必改", where, f"功能模組表沒有連到 {page.name}：表和模組頁要對得起來")

    settings = root / "prd.json"
    if settings.exists():
        try:
            roles = json.loads(settings.read_text(encoding="utf-8")).get("roles") or {}
        except json.JSONDecodeError as error:
            roles = {}
            report.add("必改", "prd.json", f"不是合法的 JSON（{error.msg}，第 {error.lineno} 行）")
        for role, chosen in roles.items():
            effort = (chosen or {}).get("effort")
            if effort and effort not in EFFORTS:
                report.add("請看", "prd.json", f"roles.{role}.effort 寫的是「{effort}」，可用的是 {'、'.join(EFFORTS)}")

    decisions = docs / "00-part-0" / "03-decisions.md"
    waiting = [p for p in pages if "待確認" in visible(p.read_text(encoding="utf-8")) and p != decisions]
    if waiting and not decisions.exists():
        names = "、".join(p.name for p in waiting[:3])
        report.add("請看", "docs/00-part-0/", f"{names} 有「待確認」，但沒有決定紀錄可以對照")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="檢查 PRD 的結構與常見問題")
    parser.add_argument("root", type=Path, help="PRD 的資料夾（裡面有 docs/）")
    parser.add_argument("--final", action="store_true", help="交付前：沒填完的地方也算必改")
    args = parser.parse_args()
    report = check(args.root.resolve(), args.final)
    for kind, items in report.found.items():
        if items:
            print(f"\n{kind}（{len(items)}）")
            for item in items:
                print(f"  - {item}")
    if not any(report.found.values()):
        print("沒有發現問題。寫得好不好，請再照 references/ 的標準看一次。")
    elif not report.found["必改"]:
        print("\n沒有必改的項目。")
    return 1 if report.found["必改"] else 0


if __name__ == "__main__":
    sys.exit(main())
