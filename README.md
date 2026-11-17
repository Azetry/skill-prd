# writing-prds

一個給 Claude 用的 skill：撰寫、改寫與持續更新產品需求文件（PRD）。

它把寫 PRD 拆成六站，每一站有一份產出物和一份「標準」。每一站都是先問、再寫、對照標準檢查、改到過，才往下一站。

| 站 | 產出物 |
|---|---|
| 1 | 訪談紀錄與素材清單 |
| 2 | 骨架：寫哪些章節、模組怎麼切 |
| 3 | Part 1：為什麼要做 |
| 4 | Part 2：要怎麼做（角色、流程、功能模組表、各模組的需求與驗收條件） |
| 5 | Part 0、Part 3：修訂追蹤、時程、決策紀錄與其他 |
| 6 | 交付：一節一頁的文件網站 |

三種工作都適用：從零寫一份、更新既有的一份、把已經存在的系統整理成規格。

## 安裝

**Claude Code**：把 `skills/writing-prds` 整個資料夾複製到下面其中一個位置。

- 只有自己用：`~/.claude/skills/writing-prds`
- 整個專案都用：`<專案>/.claude/skills/writing-prds`

```bash
git clone https://github.com/Azetry/skill-prd
cp -r skill-prd/skills/writing-prds ~/.claude/skills/
```

**claude.ai**：打包成 `.skill` 檔，在設定裡的 Skills 上傳。

```bash
cd skills && zip -r ../writing-prds.skill writing-prds -x 'writing-prds/evals/*' -x '*/__pycache__/*'
```

## 怎麼用

裝好之後不用特別叫它。講到 PRD、需求文件、規格書、驗收條件、功能模組表，或說「把這個需求寫成文件」「把會議結論更新到文件」「把現有系統整理成規格」，Claude 會自己打開這個 skill。

它會做的事：

- 先問清楚再寫。一批最多問五題，回答完更新文件，再問下一批。
- 來源沒說的規則不會寫成定案：在頁面上標「待確認」，並列進決策紀錄。
- 只寫有人要的功能。它覺得該加的，列在「建議加，未列入範圍」。
- 每一站寫完，用 `scripts/check_prd.py` 檢查，再請另一個審查者對照標準看一次。同一站最多改兩輪，還有「必改」就交給你決定。
- 修訂追蹤會寫明這一版是誰起草、負責人審閱了沒有。

## 目錄

```
skills/writing-prds/
  SKILL.md                 流程、三種工作怎麼分、每一站的檢查表
  references/              訪談、骨架、各站的標準、審查方式（用到哪一站才讀哪一份）
  scripts/new_prd.py       開一份新 PRD 的骨架
  scripts/check_prd.py     檢查：編號、修訂表、連結、空話、驗收條件、未完成的地方
  assets/template/         PRD 的範本（含接案用的補充頁）
  assets/site/             把 docs/ 建成一節一頁的網站
  evals/                   三個測試情境，各有評分項目
tests/
  trigger-eval.json        20 句話：10 句該打開這個 skill，10 句不該
  groups.json              每個情境的評分項目，哪些看成品、哪些看過程
  results/                 第二輪測試的結果
  harness/                 跑測試用的腳本
```

## 各角色用哪個模型

每一份 PRD 的 `prd.json` 有 `roles`，可以一份文件設一種：

| 角色 | 預設 | 做什麼 |
|---|---|---|
| planner | fable・high | 訪談、寫文件（就是目前這個對話） |
| reviewer | fable・high | 每一站寫完後對照標準審查 |
| implementer | opus・xhigh | 保留給之後照 PRD 實作的人 |

## 測試結果（第二輪，2026-11-17）

三個情境各跑兩次，有 skill 和沒有 skill 各一組，每一次都是獨立的對話，沒有提示它有這個 skill。

| | 有 skill | 沒有 skill |
|---|---|---|
| 成品的評分項目 | 44／48（92%） | 34／48（71%） |
| 過程的評分項目 | 28／28 | 4／28 |
| 從零寫一份 | 12／14 | 5／14 |
| 更新既有的一份 | 17／18 | 16／18 |
| 把既有系統整理成規格 | 15／16 | 13／16 |
| 每次花費 | 約 20 萬 tokens、9 分鐘、4.45 美元 | 約 3.5 萬 tokens、1.4 分鐘、0.80 美元 |

- 六次有 skill 的對話都自己打開了 skill，也都另外開了審查者。
- 觸發測試：該打開的 20 次全部打開，不該打開的 20 次都沒有打開。
- 更新既有的一份時，成品的差距最小（17／18 對 16／18），花費一樣是好幾倍。給小改動用的輕量走法還沒做。
- 還沒修的四個小問題：一次問超過五題（1 次）、沒有來源的規則沒標出來（2 次）、內文留了一句修訂經過（1 次）、小系統寫得偏長。

怎麼跑、評分項目是什麼，見 [`tests/README.md`](tests/README.md)。

## 出處

章節架構（先講為什麼，再講怎麼做）來自「產品先生的 PRD 教學」的分法。
