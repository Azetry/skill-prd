# 2.2 流程

一次用車從預約到還車，同仁和總務各做兩件事。

```mermaid
flowchart LR
  A[同仁選車與時段] --> B{這個時段這輛車有空嗎？}
  B -- 否 --> A
  B -- 是 --> C{時段不超過 3 天嗎？}
  C -- 否 --> A
  C -- 是 --> D[送出預約]
  D --> E{總務核准嗎？}
  E -- 否 --> F[退回，同仁收到原因]
  E -- 是 --> G[總務交鑰匙，標記已取車]
  G --> H[同仁還車，填里程]
  H --> I[總務確認還車]
```

<div class="wide">
<table class="lanes">
<tr><th>同仁</th><td>1 送出預約</td><td></td><td></td><td>4 還車、填里程</td><td></td></tr>
<tr><th>總務</th><td></td><td>2 核准或退回</td><td>3 交鑰匙</td><td></td><td>5 確認還車</td></tr>
</table>
</div>
