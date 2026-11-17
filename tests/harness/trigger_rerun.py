#!/usr/bin/env python3
"""Trigger test, counted properly.

The stock runner writes one stand-in entry per query into the same folder and counts a hit only
when the model opens *that query's own* entry. With several queries running at once the model
sees several identical entries and may open a sibling's, which was counted as a miss. Here a hit
is: the model's first tool call opens any writing-prds stand-in.

    python3 trigger_rerun.py <eval-set.json> <skill dir> [tries] > result.json
"""
import json, os, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

evals = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
skill = Path(sys.argv[2])
tries = int(sys.argv[3]) if len(sys.argv) > 3 else 2
description = (skill / "SKILL.md").read_text(encoding="utf-8").split("description:", 1)[1].split("\n---", 1)[0].strip()
root = Path.home()  # the stand-in entries go to ~/.claude/commands
PREFIX = "writing-prds-skill-"
# The model the sessions run on: PRD_TEST_MODEL, else whatever `claude` uses by default.
MODEL = ["--model", os.environ["PRD_TEST_MODEL"]] if os.environ.get("PRD_TEST_MODEL") else []

def one(job):
    index, attempt = job
    name = PREFIX + uuid.uuid4().hex[:8]
    command = root / ".claude" / "commands" / f"{name}.md"
    command.parent.mkdir(parents=True, exist_ok=True)
    command.write_text(f"---\ndescription: |\n  {description}\n---\n\n# writing-prds\n\nThis skill handles: {description}\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(["claude", "-p", evals[index]["query"], "--output-format", "stream-json", "--verbose", *MODEL], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=root, env=env, text=True)
    first, start = "nothing within 100 seconds", time.time()
    try:
        for line in proc.stdout:
            if time.time() - start > 100:
                break
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "assistant":
                done = False
                for part in event.get("message", {}).get("content", []):
                    if part.get("type") == "tool_use":
                        given = json.dumps(part.get("input", {}), ensure_ascii=False)
                        first = "skill" if PREFIX in given else f"{part.get('name')}: {given[:80]}"
                        done = True
                        break
                    if part.get("type") == "text" and part.get("text", "").strip():
                        first = "text: " + part["text"].strip().replace("\n", " ")[:80]
                        done = True
                        break
                if done:
                    break
            elif event.get("type") == "result":
                break
    finally:
        proc.kill(); proc.wait()
        command.unlink(missing_ok=True)
    return index, attempt, first

with ThreadPoolExecutor(4) as pool:
    rows = list(pool.map(one, [(i, t) for i in range(len(evals)) for t in range(tries)]))
out = []
for index, item in enumerate(evals):
    firsts = [f for i, _, f in sorted(rows) if i == index]
    hits = sum(f == "skill" for f in firsts)
    out.append({"query": item["query"], "should_trigger": item["should_trigger"], "hits": hits, "tries": tries, "first_actions": firsts})
print(json.dumps(out, ensure_ascii=False, indent=2))
