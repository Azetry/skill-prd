"""訪客登記：員工預先登記訪客，櫃台標記到達與離開。"""

import csv
import io
from datetime import date, datetime, timedelta

from flask import Flask, abort, g, redirect, render_template, request

from db import query, run  # 薄薄一層 SQLite 包裝
from auth import login_required  # 設定 g.user：name、role（employee／desk／admin）

app = Flask(__name__)
MAX_DAYS_AHEAD = 14


@app.post("/visits")
@login_required
def create_visit():
    day = date.fromisoformat(request.form["day"])
    if day < date.today():
        abort(400, "不能登記過去的日期")
    if day > date.today() + timedelta(days=MAX_DAYS_AHEAD):
        abort(400, f"最多只能登記 {MAX_DAYS_AHEAD} 天內的訪客")
    name = request.form["visitor_name"].strip()
    company = request.form.get("company", "").strip()
    if not name:
        abort(400, "請填訪客姓名")
    run(
        "insert into visits (day, visitor_name, company, host, status) values (?, ?, ?, ?, 'expected')",
        (day.isoformat(), name, company, g.user.name),
    )
    return redirect("/visits/mine")


@app.get("/visits/mine")
@login_required
def my_visits():
    rows = query("select * from visits where host = ? order by day desc limit 50", (g.user.name,))
    return render_template("mine.html", visits=rows)


@app.post("/visits/<int:visit_id>/cancel")
@login_required
def cancel_visit(visit_id):
    visit = query("select * from visits where id = ?", (visit_id,), one=True)
    if visit is None or visit["host"] != g.user.name:
        abort(404)
    if visit["status"] != "expected":
        abort(400, "訪客已到達，不能取消")
    run("delete from visits where id = ?", (visit_id,))
    return redirect("/visits/mine")


@app.get("/front-desk")
@login_required
def front_desk():
    if g.user.role not in ("desk", "admin"):
        abort(403)
    rows = query("select * from visits where day = ? order by visitor_name", (date.today().isoformat(),))
    return render_template("desk.html", visits=rows)


@app.post("/visits/<int:visit_id>/arrive")
@login_required
def arrive(visit_id):
    if g.user.role not in ("desk", "admin"):
        abort(403)
    badge = request.form["badge_no"].strip()
    if not badge:
        abort(400, "請填訪客證號碼")
    run(
        "update visits set status = 'arrived', badge_no = ?, arrived_at = ? where id = ? and status = 'expected'",
        (badge, datetime.now().isoformat(timespec="minutes"), visit_id),
    )
    return redirect("/front-desk")


@app.post("/visits/<int:visit_id>/leave")
@login_required
def leave(visit_id):
    if g.user.role not in ("desk", "admin"):
        abort(403)
    run(
        "update visits set status = 'left', left_at = ? where id = ? and status = 'arrived'",
        (datetime.now().isoformat(timespec="minutes"), visit_id),
    )
    return redirect("/front-desk")


@app.get("/visits/export.csv")
@login_required
def export():
    if g.user.role != "admin":
        abort(403)
    month = request.args.get("month", date.today().strftime("%Y-%m"))
    rows = query("select * from visits where day like ? order by day, arrived_at", (month + "%",))
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["日期", "訪客", "公司", "接待人", "訪客證", "到達", "離開", "狀態"])
    for r in rows:
        writer.writerow([r["day"], r["visitor_name"], r["company"], r["host"], r["badge_no"], r["arrived_at"], r["left_at"], r["status"]])
    return out.getvalue(), 200, {"Content-Type": "text/csv; charset=utf-8-sig"}
