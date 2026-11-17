#!/usr/bin/env python3
"""Recompute each round-two run's time, tokens and final message from its transcript.

A session that starts helper agents ends its turn and is woken again when they report, so its
transcript holds several `result` events. The last one's duration covers only the last turn.
Time is taken from the first and last timestamps, tokens and cost from the cumulative
`modelUsage`, and the final message is every turn's closing text in order.

    python3 retime.py <iteration dir>
"""
import json, sys
from datetime import datetime
from pathlib import Path

for transcript in sorted(Path(sys.argv[1]).glob("*/*/run-*/transcript.jsonl")):
    run = transcript.parent
    stamps, results = [], []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("timestamp"):
            stamps.append(event["timestamp"])
        if event.get("type") == "result":
            results.append(event)
    if not results:
        print("no result yet:", run)
        continue
    when = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in (stamps[0], stamps[-1])]
    seconds = round((when[1] - when[0]).total_seconds(), 1)
    used = results[-1].get("modelUsage") or {}
    tokens = sum(v.get("inputTokens", 0) + v.get("outputTokens", 0) + v.get("cacheCreationInputTokens", 0) for v in used.values())
    timing = json.loads((run / "timing.json").read_text()) if (run / "timing.json").exists() else {}
    timing.update({"total_tokens": tokens, "duration_ms": int(seconds * 1000), "total_duration_seconds": seconds,
                   "cost_usd": results[-1].get("total_cost_usd"), "turns_ended": len(results), "models": sorted(used)})
    (run / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    texts = [r.get("result") or "" for r in results if (r.get("result") or "").strip()]
    body = texts[0] if len(texts) == 1 else "\n\n".join(f"<!-- message {n} of {len(texts)} -->\n\n{t}" for n, t in enumerate(texts, 1))
    (run / "outputs").mkdir(exist_ok=True)
    (run / "outputs" / "final_message.md").write_text(body or "(the session ended without a final message)", encoding="utf-8")
    rel = run.relative_to(sys.argv[1])
    print(f"{str(rel):58s} {seconds:7.1f}s  tokens={tokens:7d}  cost=${timing['cost_usd']:.2f}  skill={timing.get('skill_opened')}  helpers={timing.get('helper_agents')}  messages={len(texts)}")
