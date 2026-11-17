# 測試

## 三個情境

在 `skills/writing-prds/evals/`，每個情境一個資料夾：

| 情境 | 給它的東西 | 評分項目 |
|---|---|---|
| `new-prd-from-short-brief` | 三四句話的需求 | 13 項 |
| `update-prd-from-meeting-notes` | 一份寫好的 PRD 和一份會議紀錄 | 13 項 |
| `existing-system-to-spec` | 一支 102 行的程式和一份使用手冊 | 12 項 |

- `prompt.md`：使用者說的話。
- `graders/NN-*.md`：一項一個檔，寫成看成品就能判斷對錯的句子。
- `files/`：情境要用到的輸入檔。
- `groups.json`（在這個資料夾）：哪些項目看成品（outcome），哪些看過程（process，例如有沒有先讀標準、有沒有跑檢查腳本）。沒有 skill 的那一組本來就不會做過程那幾項，所以比較時以成品為主。

## 觸發測試

`trigger-eval.json` 有 20 句話，10 句應該讓 Claude 打開這個 skill，10 句不應該（例如把 PRD 做成簡報、照驗收條件寫測試、整理會議紀錄）。

```bash
python3 tests/harness/trigger_rerun.py tests/trigger-eval.json skills/writing-prds 2 > result.json
```

句子裡的專案名稱換成了通用的名字；測試當時用的是實際的專案名，其餘一字未改。

每一句會開一個 `claude -p` 對話，看它的第一個動作是不是打開這個 skill。腳本會在 `~/.claude/commands/` 放暫時的檔案，跑完會刪掉。

## 跑三個情境

```bash
export PRD_TEST_OUT=~/prd-test/results PRD_TEST_WORK=~/prd-test/work
python3 tests/harness/run_round2.py            # 3 個情境 × 有／沒有 skill × 2 次 = 12 個對話
python3 tests/harness/retime.py $PRD_TEST_OUT  # 修正有另外開審查者的對話的時間
```

- 每一次是獨立的 `claude -p` 對話。有 skill 的那一組把 skill 放在工作資料夾的 `.claude/skills/`，不告訴它有這個 skill。
- 12 個對話合計大約 30 美元。要指定模型，設 `PRD_TEST_MODEL`；沒設就用 `claude` 的預設。
- 評分不在腳本裡：每一次的成品要請一個沒看過 skill 的評分者，照 `graders/` 一項一項判斷，寫成 `grading.json`。之後 `summarize_round2.py` 會把成品和過程分開統計。

## 第二輪的結果

`results/round-2-summary.json`：每一次的每一項過或不過、tokens、秒數、花費。
`results/round-2-trigger.json`：觸發測試每一句的結果。

第二輪的評分者和寫文件的對話用不同的模型；第一輪用的是同一個。
