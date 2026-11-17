---
name: writing-prds
description: 撰寫、改寫與持續更新產品需求文件（PRD、產品規格、需求規格書）。涵蓋需求訪談、背景與目標、產品用戶與流程、功能模組表、各模組的需求詳述與驗收條件、修訂追蹤與時程，並可把文件建成一節一頁的網站。當使用者提到 PRD、產品需求文件、需求文件、規格書、功能規格、spec、驗收條件、功能模組表、修訂追蹤，或要求「把這個需求寫成文件」「把會議結論更新到文件」「把現有系統整理成規格」時使用，即使沒有說出 PRD 這個字。Writes and maintains product requirements documents (PRD, product spec), covering the intake interview, background and goals, users and flows, the module table, per-module requirements with acceptance criteria, and the revision log.
---

# 撰寫與維護 PRD

一份 PRD 要同時服務三種人：決定要不要做的人，看得懂為什麼做；動手做的人，知道要做成什麼樣、怎樣算完成；之後接手的人，查得到當初怎麼決定。寫不好的 PRD 通常不是文筆問題，而是沒問清楚就開始寫，或寫完沒有人拿標準對過。

所以這個 skill 把工作拆成六個產出物，每個產出物配一份「標準」。每一站都是：先問、再寫、對照標準檢查、改到過，才往下一站。

## 產出物與標準

| 站 | 產出物 | 放在哪裡 | 進站前要有 | 寫之前讀、寫完對照 |
|---|---|---|---|---|
| 1 | 訪談紀錄與素材清單 | `notes/intake.md` | 使用者的需求描述，或這次要改的事 | `references/interview.md` |
| 2 | 骨架：寫哪些章節、模組怎麼切 | `docs/` 的檔案、`docs/about.md` | 訪談紀錄裡有讀者、範圍、負責人，並知道是自己的產品還是接案 | `references/structure.md` |
| 3 | Part 1：為什麼要做 | `docs/01-part-1/` | 骨架定了：要寫的檔案都在，不寫的已刪 | `references/standard-why.md` |
| 4 | Part 2：要怎麼做 | `docs/02-part-2/` | 第 3 站已過，或使用者說這次不寫 Part 1；訪談紀錄裡有角色與主線流程 | `references/standard-how.md`、`references/standard-visuals.md` |
| 5 | Part 0、Part 3：文件管理與其他 | `docs/00-part-0/`、`docs/03-part-3/` | 模組與功能點定了 | `references/standard-housekeeping.md` |
| 6 | 交付：一節一頁的網站 | `_site/` | `check_prd.py --final` 沒有「必改」 | 本檔的「交付與回饋」 |

「進站前要有」的東西不齊，不要硬寫：回上一站補，或去問使用者。出站的條件就是那一站的標準。

`references/standard-writing.md`（語氣與用詞）每一站都適用，開始寫第 3 站前讀一次。

只讀目前這一站需要的那一份。標準裡的例子是示意，不要照抄到使用者的文件裡。

## 先分辨是哪一種工作

開工先選一條路，之後照那一列走：

| 這次的工作 | 走哪幾站 | 開始前先做 |
|---|---|---|
| 從零寫一份 | 1 到 6 依序 | 用 `scripts/new_prd.py` 建骨架 |
| 更新既有的 PRD（最常見） | 只走受影響的站；第 5 站的修訂追蹤一定做 | 讀修訂追蹤表最上面幾列和要改的頁；讀 `references/standard-housekeeping.md` 的「更新既有的文件」；確認這次改動的來源與日期 |
| 把已經存在的系統整理成規格 | 1 到 6 依序，第 1 站改成盤點現況；Part 1 可以很短 | 把程式和既有文件整份讀完再動筆 |

更新時，照這次改的內容決定讀哪一份標準，不用全讀：

| 這次改的是 | 讀 |
|---|---|
| 規則、畫面、特殊情況、驗收條件、功能模組表 | `references/standard-how.md`；動到圖再加 `references/standard-visuals.md` |
| 目標、痛點、效益、名詞 | `references/standard-why.md` |
| 時程、決定紀錄、任務清單 | `references/standard-housekeeping.md` |
| 章節增減、新增模組 | `references/structure.md`，再加上面對應的一份 |
| 只改用字 | `references/standard-writing.md` |

整理既有系統時，素材是程式、畫面和操作手冊，不是訪談。每個功能標成「已上線」，之後要改的另外標。程式和文件對不起來的地方，照程式寫，並把每一處不一致列出來給使用者，不要自己挑一邊默默帶過。

## 進度紀錄

`notes/progress.md` 記每一站的狀態。PRD 很少一次對話寫完；沒有這份紀錄，下一次對話不是從頭來，就是跳站。

- 開工先讀它。從第一個狀態不是「已過」或「這次不做」的站接著做。
- 每一站做完、卡住或交給使用者決定時，更新那一列。
- 既有的 PRD 沒有這個檔，就照文件實際的狀況建一份。

## 每一站的循環

把下面這段複製到回覆或工作筆記裡，逐項打勾：

```
站 N：<產出物>
- [ ] 問：這一站還缺的事實列出來，一批最多問五題；答完先更新文件，再問下一批（見 interview.md 的問法）
- [ ] 寫：只寫這一站的產出物
- [ ] 查：跑 <skill>/scripts/check_prd.py，再照這一站的標準逐條對
- [ ] 審：能開 subagent 時，請審查者照 references/review.md 審這一站（給它完整路徑）
- [ ] 改：有不過的就改，改完重查。同一站最多兩輪；第二輪還有「必改」，就照 references/review.md 的交接格式交給使用者決定
- [ ] 看：給使用者看這一站的成果，收到回饋再往下
- [ ] 記：更新 notes/progress.md 這一站的狀態
```

三件事不能省：

1. **缺的事實用問的，不要用猜的。** 文件負責人、角色名稱、金額、日期、誰決定，猜錯一個，整份文件的可信度就沒了。程式和既有文件查得到的就自己查，不要拿去問人。為了把規則寫完整而自己補的細節，要在那一句旁邊標「待確認」，做法在 `references/standard-writing.md` 的「來源沒說的，當場標出來」。
2. **寫的人不要自己當唯一的審查者。** 同一個對話寫完再自己看，幾乎都會覺得沒問題。審查者只拿到標準和成品，不拿到寫作過程，才看得出讀者會卡在哪裡。不能開 subagent 時，至少隔一段工作再回頭，只拿著標準讀成品。
3. **每次給人看之前，文件要是「現在的真相」。** 過時的段落直接改掉或刪掉，歷史留在修訂追蹤表和版本紀錄裡，不要留在正文。

## 各角色用哪個模型

每份 PRD 的 `prd.json` 有一段 `roles`，記這份文件各角色用的模型和 effort。預設是：寫的人（planner）`fable`／`high`，審查者（reviewer）`fable`／`high`，實作者（implementer）`opus`／`xhigh`。

- **審查者**：開審查者時，把 `roles.reviewer` 的 model 和 effort 帶進去（開 agent 的工具有這兩個參數）。`prd.json` 沒有這一段就用預設。
- **寫的人**就是目前這個對話，skill 換不了它的模型。開工時說一句這份 PRD 設定寫的人用什麼，讓使用者自己確認；同一個對話說一次就好。
- **實作者**不在這個 skill 裡用到。設定留給之後照這份 PRD 寫程式的流程讀。
- 使用者想換，就改那份 PRD 的 `prd.json`，不要改這個 skill。

## 工具

`<skill>` 是這個 skill 的資料夾，也就是本檔所在的位置。指令和交給別人的檔案路徑一律寫完整路徑：你工作時所在的資料夾通常是使用者的專案，在那裡 `scripts/…`、`references/…` 這種相對路徑找不到檔案。路徑用正斜線。

需要 Python 3.10 以上；建網站另外需要 `markdown` 套件（`pip install markdown==3.7`），沒裝時腳本會說明怎麼裝。

```bash
# 建一份新 PRD 的骨架（甲方自家產品型；接案用 --type vendor）
python3 <skill>/scripts/new_prd.py <目標資料夾> --name "<產品名> 產品需求文件" --author "<負責人>"

# 檢查結構與常見問題；有「必改」時結束碼是 1
python3 <skill>/scripts/check_prd.py <PRD 資料夾>

# 建成網站：一節一頁，首頁的版本、日期、負責人取自修訂追蹤表最上面一列
python3 <PRD 資料夾>/tools/site/build.py <PRD 資料夾> <PRD 資料夾>/_site
```

`check_prd.py` 查的是機器看得出來的事：檔案與編號、修訂追蹤表、沒填完的佔位、空泛用語、看起來像真實個資的字串、模組頁有沒有驗收條件、功能模組表和模組頁對不對得起來。交付前加 `--final`，沒填完的地方也會算成「必改」。它過了不代表文件寫得好，寫得好不好要照標準看。

既有的 PRD 如果不是用這個骨架建的（沒有 `tools/site/`、檔案排法不同），不要為了套工具去搬動對方的檔案：照它原本的結構改內容，標準照用；對方想要網站時，再問要不要把 `assets/site/` 複製過去並調整排法。

## 交付與回饋

- 使用者要在哪裡看，就交付到哪裡：能發布成網頁的環境，把 `_site/` 發布出去讓人直接留言；否則給資料夾路徑和建站指令。
- 使用者的每一則回饋都是一次修訂：改文件、在修訂追蹤表加一列、需要對方決定的事記進決定紀錄。
- 問題和決定就在文件上談。網頁可以留言時，把這一批最多五題放在決定紀錄那一頁，請對方在頁面上留言；答完把文件更新到最新，再放下一批。一站的問題沒談完，不往下一站。
- 回饋如果一再指向同一類問題（太多字、語氣、圖不夠），先回頭看對應的標準是不是沒照做；標準本身不夠用時，告訴使用者，建議把這一條補進 `references/` 對應的檔案。

## 參考檔一覽

- `references/interview.md`：開工前和每一站要問什麼、怎麼問。
- `references/structure.md`：四個 Part 的骨架、甲方型與乙方型的差別、哪些可以不寫、檔名與編號。
- `references/standard-why.md`：Part 1 六節的標準。
- `references/standard-how.md`：產品用戶、流程、功能模組表、需求詳述、驗收條件的標準。
- `references/standard-visuals.md`：什麼時候用哪一種圖、畫面怎麼標號、可用的版型。
- `references/standard-housekeeping.md`：修訂追蹤、時程、決定紀錄、Part 3，以及怎麼更新既有文件。
- `references/standard-writing.md`：語氣、用詞、該避免的寫法。
- `references/review.md`：審查者怎麼審、回報格式。
