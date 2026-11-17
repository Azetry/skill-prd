#!/usr/bin/env python3
"""Start a new PRD from the template.

    python3 scripts/new_prd.py <target> --name "<產品> 產品需求文件" --author "<負責人>"
                               [--short "<產品> PRD"] [--type client|vendor] [--date YYYY-MM-DD]

Copies the skeleton (docs/, notes/, README, prd.json) and the site builder (tools/site/)
into <target>, and fills in the name, the author and the date of the first revision.
`--type vendor` is for work done for a client: Part 1 becomes the client's requirements,
and a change-control table is added to Part 0.

Nothing is overwritten: a target that already holds files is refused.
"""

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "template"
SITE = SKILL / "assets" / "site"
OVERLAY = "vendor-overlay"
# Sections of the client-side skeleton that the vendor-side one replaces.
CLIENT_ONLY = [
    "docs/01-part-1/01-describe-requirements.md",
    "docs/01-part-1/02-requirements-goals.md",
    "docs/01-part-1/03-user-needs.md",
    "docs/01-part-1/04-roi.md",
    "docs/01-part-1/05-glossary.md",
    "docs/01-part-1/06-competitor-analysis.md",
]
TEXT = {".md", ".json", ".html", ".css", ".txt"}


def main() -> int:
    parser = argparse.ArgumentParser(description="建立一份新 PRD 的骨架")
    parser.add_argument("target", type=Path, help="要建立的資料夾")
    parser.add_argument("--name", required=True, help="文件名稱，例如「會議室預約 產品需求文件」")
    parser.add_argument("--author", required=True, help="文件負責人（向使用者確認過的名字）")
    parser.add_argument("--short", help="短名稱，預設取名稱的第一個詞加 PRD")
    parser.add_argument("--type", choices=["client", "vendor"], default="client")
    parser.add_argument("--date", default=date.today().isoformat(), help="第一版的日期")
    args = parser.parse_args()

    target = args.target.resolve()
    if target.exists() and any(target.iterdir()):
        print(f"{target} 裡面已經有檔案，沒有建立任何東西。請換一個空的資料夾。", file=sys.stderr)
        return 1
    try:
        date.fromisoformat(args.date)
    except ValueError:
        print(f"日期「{args.date}」請寫成 YYYY-MM-DD。", file=sys.stderr)
        return 1

    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns(OVERLAY))
    if args.type == "vendor":
        for name in CLIENT_ONLY:
            (target / name).unlink()
        shutil.copytree(TEMPLATE / OVERLAY, target, dirs_exist_ok=True)
    shutil.copytree(SITE, target / "tools" / "site", ignore=shutil.ignore_patterns("__pycache__"))
    (target / "assets").mkdir(exist_ok=True)
    # The built site is an output: rebuilt every time, never committed.
    (target / ".gitignore").write_text("_site/\n__pycache__/\n", encoding="utf-8")

    short = args.short or f"{args.name.split()[0]} PRD"
    values = {"{{NAME}}": args.name, "{{SHORT}}": short, "{{AUTHOR}}": args.author, "{{DATE}}": args.date}
    for path in target.rglob("*"):
        if path.is_file() and path.suffix in TEXT and "tools" not in path.relative_to(target).parts:
            text = path.read_text(encoding="utf-8")
            for mark, value in values.items():
                text = text.replace(mark, value)
            path.write_text(text, encoding="utf-8")

    kind = "乙方型（替客戶做）" if args.type == "vendor" else "甲方型（自己的產品）"
    print(f"已建立 {target}：{kind}")
    print("接下來：")
    print("  0. 進度記在 notes/progress.md，每一站做完就更新")
    print("  1. 把訪談結果寫進 notes/intake.md")
    print("  2. 決定要寫哪些章節，刪掉用不到的檔案；模組頁照 04-module-example.md 複製")
    print(f"  3. 檢查：python3 {Path(__file__).with_name('check_prd.py')} {target}")
    print(f"  4. 建站：pip install markdown==3.7 && python3 {target}/tools/site/build.py {target} {target}/_site")
    return 0


if __name__ == "__main__":
    sys.exit(main())
