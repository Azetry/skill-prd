#!/usr/bin/env python3
"""Round 2 in one table: outcome and process checks apart, two runs per configuration.

    python3 summarize_round2.py            # prints the table and writes summary.json beside the results
"""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# The folder run_round2.py wrote to (PRD_TEST_OUT), holding the gradings as well.
IT = Path(os.environ.get("PRD_TEST_OUT", REPO.parent / "writing-prds-workspace" / "iteration"))
groups = json.loads((REPO / "tests" / "groups.json").read_text())
summary = {}
for case, split in groups.items():
    names = json.loads((IT / case / "eval_metadata.json").read_text(encoding="utf-8"))["assertions"]
    for config in ("with_skill", "without_skill"):
        rows = []
        for run in sorted((IT / case / config).glob("run-*")):
            g = run / "grading.json"
            if not g.exists():
                rows.append(None)
                continue
            marks = [e["passed"] for e in json.loads(g.read_text(encoding="utf-8"))["expectations"]]
            t = json.loads((run / "timing.json").read_text())
            rows.append({"marks": marks, "tokens": t["total_tokens"], "seconds": t["total_duration_seconds"], "cost": t.get("cost_usd"),
                         "skill_opened": t.get("skill_opened"), "helpers": t.get("helper_agents")})
        summary[f"{case}/{config}"] = rows
        for kind in ("outcome", "process"):
            cells = []
            for r in rows:
                if r is None:
                    cells.append("  (no grading)")
                    continue
                picked = [r["marks"][i - 1] for i in split[kind] if i - 1 < len(r["marks"])]
                cells.append(f"{sum(picked)}/{len(picked)} " + "".join("P" if m else "F" for m in picked))
            print(f"{case:32s} {config:14s} {kind:8s} " + "   ".join(cells))
    print()
total = {}
for key, rows in summary.items():
    case, config = key.split("/")
    for kind in ("outcome", "process"):
        for r in rows:
            if r is None:
                continue
            picked = [r["marks"][i - 1] for i in groups[case][kind] if i - 1 < len(r["marks"])]
            got = total.setdefault((config, kind), [0, 0])
            got[0] += sum(picked); got[1] += len(picked)
for (config, kind), (p, n) in sorted(total.items()):
    print(f"TOTAL {config:14s} {kind:8s} {p}/{n} = {p / n:.0%}")
for config in ("with_skill", "without_skill"):
    rs = [r for k, rows in summary.items() if k.endswith("/" + config) for r in rows if r]
    if rs:
        print(f"{config}: mean tokens {sum(r['tokens'] for r in rs) / len(rs):,.0f}, mean seconds {sum(r['seconds'] for r in rs) / len(rs):.0f}, mean cost ${sum(r['cost'] or 0 for r in rs) / len(rs):.2f}")
(IT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
# failed checks, by name
for key, rows in summary.items():
    case, _ = key.split("/")
    names = json.loads((IT / case / "eval_metadata.json").read_text(encoding="utf-8"))["assertions"]
    for n, r in enumerate(rows, 1):
        if r:
            failed = [i + 1 for i, m in enumerate(r["marks"]) if not m]
            print(f"{key} run-{n} failed: {failed}")
