# 公務車借用 產品需求文件

## 文件在哪裡

| 位置 | 內容 |
|---|---|
| `docs/about.md` | 首頁：文件資訊與本版範圍 |
| `docs/00-part-0/` | Part 0 文件管理：修訂追蹤表、時程安排、決定紀錄 |
| `docs/01-part-1/` | Part 1 背景需求：為什麼要做 |
| `docs/02-part-2/` | Part 2 需求詳述：要怎麼做 |
| `docs/03-part-3/` | Part 3 其他 |
| `notes/intake.md` | 訪談紀錄與素材清單（不進網站） |
| `notes/progress.md` | 每一站做到哪裡（不進網站） |
| `assets/` | 圖片 |
| `tools/site/` | 把這個資料夾建成網站 |

## 怎麼改

- 一節一個檔，檔名前面的數字決定順序；第一行是 `# 標題`。
- 用 Markdown 寫；要放畫面、示意圖、對照時直接寫 HTML，可用的版型在 `tools/site/site.css`。
- 每次修改，在 `docs/00-part-0/01-revision-tracking.md` 的表格最上面加一列。
- 畫面一律用示範資料。

## 在自己電腦上看

```bash
pip install markdown==3.7
python3 tools/site/build.py . _site
python3 -m http.server -d _site 8000
```
