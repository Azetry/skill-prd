#!/usr/bin/env python3
"""Round 2: every test is its own top-level session (so a reviewer agent can be started).

    python3 run_round2.py [case ...]

The with-skill sessions are not told about the skill: it sits in the work folder's
.claude/skills and has to be picked up by itself. Both configurations get the user's message
and nothing else. Each run leaves, under iteration-2/<case>/<configuration>/run-<n>/:
transcript.jsonl, outputs/ (the deliverable and final_message.md), trace.md, timing.json.
"""
import json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "writing-prds"
EVALS = SKILL / "evals"
# Where the results go, and where each session works (both outside the repository).
OUT = Path(os.environ.get("PRD_TEST_OUT", REPO.parent / "writing-prds-workspace" / "iteration"))
WORK = Path(os.environ.get("PRD_TEST_WORK", REPO.parent / "writing-prds-workspace" / "work"))
# The model the sessions run on: PRD_TEST_MODEL, else whatever `claude` uses by default.
MODEL = ["--model", os.environ["PRD_TEST_MODEL"]] if os.environ.get("PRD_TEST_MODEL") else []
DELIVERABLE = {"new-prd-from-short-brief": "lab-prd", "update-prd-from-meeting-notes": "car-prd", "existing-system-to-spec": "visitor-prd"}
RUNS, LIMIT = 2, 3000
SKIP = shutil.ignore_patterns("_site", "tools", "__pycache__", ".gitignore", ".claude")


def prompt_of(case: str) -> str:
    body = (EVALS / case / "prompt.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
    return "\n".join(l for l in body.splitlines() if not l.startswith("Input files:")).strip()


def assertions_of(case: str) -> list[str]:
    return [g.read_text(encoding="utf-8").split("---", 2)[2].strip() for g in sorted((EVALS / case / "graders").glob("*.md"))]


def one(job):
    case, config, n = job
    work = WORK / case / config / f"run-{n}"
    run = OUT / case / config / f"run-{n}"
    shutil.rmtree(work, ignore_errors=True); shutil.rmtree(run, ignore_errors=True)
    work.mkdir(parents=True); (run / "outputs").mkdir(parents=True)
    files = EVALS / case / "files"
    if files.is_dir():
        shutil.copytree(files, work, dirs_exist_ok=True)
    if config == "with_skill":
        shutil.copytree(SKILL, work / ".claude" / "skills" / "writing-prds")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    command = ["claude", "-p", prompt_of(case), *MODEL, "--output-format", "stream-json", "--verbose",
               "--permission-mode", "acceptEdits", "--allowedTools", "Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill", "Agent", "Task"]
    started = time.time()
    with open(run / "transcript.jsonl", "w", encoding="utf-8") as out:
        try:
            code = subprocess.run(command, cwd=work, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.DEVNULL, timeout=LIMIT).returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    calls, final, result, used_skill, agents = [], "", {}, False, 0
    for line in (run / "transcript.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        inner = bool(event.get("parent_tool_use_id"))
        if event.get("type") == "assistant":
            for part in event.get("message", {}).get("content", []):
                if part.get("type") != "tool_use":
                    continue
                given = part.get("input") or {}
                name = part.get("name")
                what = given.get("file_path") or given.get("command") or given.get("skill") or given.get("pattern") or given.get("description") or ""
                if name in ("Agent", "Task"):
                    agents += 0 if inner else 1
                    what = f"{given.get('description', '')} | model={given.get('model')} effort={given.get('effort')} | {str(given.get('prompt', ''))[:500]}"
                if "writing-prds" in json.dumps(given, ensure_ascii=False) and name in ("Skill", "Read"):
                    used_skill = True
                calls.append(f"{'    (inside a helper agent) ' if inner else ''}{name}: {str(what)[:700]}")
        elif event.get("type") == "result":
            result = event
            final = event.get("result") or ""
    usage = result.get("usage") or {}
    tokens = sum(usage.get(k, 0) for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens"))
    seconds = round((result.get("duration_ms") or (time.time() - started) * 1000) / 1000, 1)
    timing = {"total_tokens": tokens, "duration_ms": int(seconds * 1000), "total_duration_seconds": seconds, "cost_usd": result.get("total_cost_usd"),
              "num_turns": result.get("num_turns"), "exit": code, "skill_opened": used_skill, "helper_agents": agents, "tool_calls": len(calls)}
    (run / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    (run / "trace.md").write_text("# Tool calls, in order (from the session's own transcript)\n\n" + "\n".join(f"{i}. {c}" for i, c in enumerate(calls, 1)) + "\n", encoding="utf-8")
    (run / "outputs" / "final_message.md").write_text(final or "(the session ended without a final message)", encoding="utf-8")
    made = work / DELIVERABLE[case]
    if made.is_dir():
        shutil.copytree(made, run / "outputs" / DELIVERABLE[case], ignore=SKIP)
    extra = [p.name for p in work.iterdir() if p.name not in (DELIVERABLE[case], ".claude") and not (files / p.name).exists()]
    print(f"done {case} {config} run-{n}: exit={code} {seconds}s tokens={tokens} skill_opened={used_skill} helpers={agents} deliverable={'yes' if made.is_dir() else 'NO'} other={extra}", flush=True)
    return job


cases = sys.argv[1:] or list(DELIVERABLE)
for case in cases:
    (OUT / case).mkdir(parents=True, exist_ok=True)
    (OUT / case / "eval_metadata.json").write_text(json.dumps({"eval_name": case, "prompt": prompt_of(case), "assertions": assertions_of(case)}, ensure_ascii=False, indent=2), encoding="utf-8")
jobs = [(c, k, n) for n in range(1, RUNS + 1) for c in cases for k in ("with_skill", "without_skill")]
with ThreadPoolExecutor(6) as pool:
    list(pool.map(one, jobs))
print("all done", flush=True)
