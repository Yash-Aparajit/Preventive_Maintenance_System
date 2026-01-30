from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import sqlite3
from datetime import datetime, date, timedelta
from models import init_db, get_connection

app = Flask(__name__)
app.secret_key = "pm_system_secret"

# STATIC USERS
USERS = {
    "developer": {"password": "Your Password", "role": "developer"},
    "user": {"password": "Your Password", "role": "user"},
}

# ---------------- HELPER LOGIC ---------------- #

def get_current_week_number():
    # Continuous week count from a fixed reference date
    reference = date(2024, 1, 1)  # arbitrary stable start
    today = date.today()
    delta_weeks = (today - reference).days // 7
    return delta_weeks + 1


def get_planned_assets_for_week(week_number):
    conn = get_connection()

    # Count active assets
    total_assets = conn.execute(
        "SELECT COUNT(*) FROM assets WHERE status = 'Active'"
    ).fetchone()[0]

    if total_assets == 0:
        conn.close()
        return []

    groups = 4  # fixed groups
    assets_per_group = (total_assets + groups - 1) // groups

    group_index = (week_number - 1) % groups
    start = group_index * assets_per_group
    end = start + assets_per_group

    assets = conn.execute(
        """
        SELECT * FROM assets
        WHERE status = 'Active'
        ORDER BY rotation_slot
        LIMIT ? OFFSET ?
        """,
        (assets_per_group, start)
    ).fetchall()

    conn.close()
    return assets

def get_calendar_label_from_week(week_number):
    reference = date(2024, 1, 1)
    week_start = reference + timedelta(weeks=week_number - 1)

    calendar_week = week_start.isocalendar().week
    month = week_start.strftime("%b")
    year = week_start.year

    return f"W{calendar_week:02d} – {month} – {year}"


def get_week_date_range(week_number):
    reference = date(2024, 1, 1)
    week_start = reference + timedelta(weeks=week_number - 1)

    # PM week = Mon to Sat (6 working days)
    week_end = week_start + timedelta(days=5)

    # display format: Date/Month Name/Year
    from_label = week_start.strftime("%d %b %Y")
    to_label = week_end.strftime("%d %b %Y")

    calendar_week = week_start.isocalendar().week

    return calendar_week, from_label, to_label

# ---------------- END OF HELPER LOGIC ---------------- #

@app.before_request
def require_login():
    if request.endpoint in ("login", "static"):
        return
    if "user" not in session:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username not in USERS or USERS[username]["password"] != password:
            flash("Invalid credentials")
            return render_template("login.html")

        session["user"] = username
        session["role"] = USERS[username]["role"]
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    return render_template("index.html")


# ---------------- ASSET MASTER ---------------- #

@app.route("/asset-master")
def asset_master():
    conn = get_connection()
    assets = conn.execute(
        "SELECT * FROM assets ORDER BY rotation_slot"
    ).fetchall()
    conn.close()
    return render_template("asset_master.html", assets=assets)


@app.route("/asset-master/add", methods=["GET", "POST"])
def asset_add():
    if request.method == "POST":
        asset_id = request.form["asset_id"]
        asset_name = request.form["asset_name"]
        asset_type = request.form["asset_type"]

        conn = get_connection()
        slot = conn.execute(
            "SELECT COALESCE(MAX(rotation_slot), 0) + 1 FROM assets"
        ).fetchone()[0]

        try:
            conn.execute(
                """
                INSERT INTO assets (asset_id, asset_name, asset_type, rotation_slot)
                VALUES (?, ?, ?, ?)
                """,
                (asset_id, asset_name, asset_type, slot),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Asset ID already exists")
            conn.close()
            return redirect(url_for("asset_add"))

        conn.close()
        return redirect(url_for("asset_master"))

    return render_template("asset_add.html")


@app.route("/asset-master/edit/<int:id>", methods=["GET", "POST"])
def asset_edit(id):
    conn = get_connection()
    asset = conn.execute(
        "SELECT * FROM assets WHERE id = ?", (id,)
    ).fetchone()

    if request.method == "POST":
        conn.execute(
            """
            UPDATE assets
            SET asset_name = ?, asset_type = ?
            WHERE id = ?
            """,
            (
                request.form["asset_name"],
                request.form["asset_type"],
                id,
            ),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("asset_master"))

    conn.close()
    return render_template("asset_edit.html", asset=asset)

# ---------------- ASSET MASTER ROUTES END ---------------- #

# ---------------- IMPORT EXPORT ---------------- #

@app.route("/asset-master/import", methods=["GET", "POST"])
def asset_import():
    if request.method == "POST":
        # logic will be added later
        flash("Import feature coming soon")
        return redirect(url_for("asset_master"))

    return render_template("asset_import.html")


@app.route("/asset-master/export")
def asset_export():
    # export logic will be added later
    flash("Export feature coming soon")
    return redirect(url_for("asset_master"))


# ---------------- IMPORT EXPORT ROUTES END---------------- #


# ---------------- PM WEEKLY ATTENDANCE ---------------- #

@app.route("/pm-attendance")
def pm_attendance():
    week = request.args.get("week", type=int) or get_current_week_number()
    entry_mode = request.args.get("entry") == "1"

    assets = get_planned_assets_for_week(week)

    conn = get_connection()
    records = conn.execute(
        "SELECT asset_id, status, recorded_on FROM pm_attendance WHERE week_number = ?",
        (week,)
    ).fetchall()

    # findings count per asset for this week
    finding_counts = conn.execute("""
        SELECT asset_id, COUNT(*) as cnt
        FROM findings_log
        WHERE week_number = ?
        GROUP BY asset_id
    """, (week,)).fetchall()

    # findings labels per asset for tooltip
    finding_labels_rows = conn.execute("""
        SELECT f.asset_id, GROUP_CONCAT(t.tag_label, ', ') AS labels
        FROM findings_log f
        JOIN assets a ON a.asset_id = f.asset_id
        LEFT JOIN finding_tags t 
            ON t.asset_type = a.asset_type 
            AND t.tag_code = f.tag_code
        WHERE f.week_number = ?
        GROUP BY f.asset_id
    """, (week,)).fetchall()

    finding_label_map = {r["asset_id"]: r["labels"] for r in finding_labels_rows}

    conn.close()

    finding_map = {r["asset_id"]: r["cnt"] for r in finding_counts}

    status_map = {r["asset_id"]: r["status"] for r in records}
    recorded_on = records[0]["recorded_on"] if records else None

    calendar_week, week_from, week_to = get_week_date_range(week)

    return render_template(
        "pm_attendance.html",
        week=week,
        calendar_week=calendar_week,
        week_from=week_from,
        week_to=week_to,
        assets=assets,
        status_map=status_map,
        finding_map=finding_map,
        finding_label_map=finding_label_map,
        recorded_on=recorded_on,
        entry_mode=entry_mode
    )

    
@app.route("/pm-attendance/save", methods=["POST"])
def pm_attendance_save():
    week = int(request.form["week"])
    statuses = request.form.getlist("status")

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    conn = get_connection()
    for entry in statuses:
        asset_id, status = entry.split("|")
        conn.execute(
            """
            INSERT OR REPLACE INTO pm_attendance
            (asset_id, week_number, status, recorded_on)
            VALUES (?, ?, ?, ?)
            """,
            (asset_id, week, status, now)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("pm_attendance", week=week))


@app.route("/pm-attendance/print")
def pm_attendance_print():
    week = request.args.get("week", type=int)

    assets = get_planned_assets_for_week(week)

    return render_template(
        "pm_print.html",
        week=week,
        assets=assets
    )

# ---------------- PM WEEKLY ATTENDANCE END ---------------- #

# ---------------- ATTENDANCE HISTORY ---------------- #

@app.route("/history/attendance", methods=["GET"])
def attendance_history():
    current_week = get_current_week_number()

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    asset_id = request.args.get("asset_id")
    status = request.args.get("status")

    query = """
        SELECT 
            p.recorded_on,
            p.asset_id,
            a.asset_name,
            p.status
        FROM pm_attendance p
        JOIN assets a ON a.asset_id = p.asset_id
        WHERE p.week_number < ?
    """
    params = [current_week]

    if from_date:
        query += " AND p.recorded_on >= ?"
        params.append(from_date)

    if to_date:
        query += " AND p.recorded_on <= ?"
        params.append(to_date + " 23:59")

    if asset_id:
        query += " AND p.asset_id = ?"
        params.append(asset_id)

    if status:
        query += " AND p.status = ?"
        params.append(status)

    query += " ORDER BY p.recorded_on DESC"

    conn = get_connection()
    records = conn.execute(query, params).fetchall()

    assets = conn.execute(
        "SELECT asset_id, asset_name FROM assets ORDER BY asset_name"
    ).fetchall()

    conn.close()

    return render_template(
        "attendance_history.html",
        records=records,
        assets=assets,
        filters={
            "from_date": from_date,
            "to_date": to_date,
            "asset_id": asset_id,
            "status": status
        }
    )

# ---------------- ATTENDANCE HISTORY END ---------------- #

# ---------------- EVENT HISTORY  ---------------- #

@app.route("/history/events", methods=["GET"])
def events_history():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    asset_id = request.args.get("asset_id")

    query = """
        SELECT 
            e.created_on,
            e.asset_id,
            a.asset_name,
            e.event_type,
            e.event_subtype,
            e.description,
            e.cost,
            e.name
        FROM events e
        JOIN assets a ON a.asset_id = e.asset_id
        WHERE 1=1
    """
    params = []

    if from_date:
        query += " AND e.created_on >= ?"
        params.append(from_date)

    if to_date:
        query += " AND e.created_on <= ?"
        params.append(to_date + " 23:59")

    if asset_id:
        query += " AND e.asset_id = ?"
        params.append(asset_id)

    query += " ORDER BY e.created_on DESC"

    conn = get_connection()
    records = conn.execute(query, params).fetchall()
    assets = conn.execute(
        "SELECT asset_id, asset_name FROM assets ORDER BY asset_name"
    ).fetchall()
    conn.close()

    return render_template(
        "events_history.html",
        records=records,
        assets=assets,
        filters={
            "from_date": from_date,
            "to_date": to_date,
            "asset_id": asset_id
        }
    )

# ---------------- EVENT HISTORY END ---------------- #

# ---------------- EVENT PAGE ---------------- #

@app.route("/events/add", methods=["GET", "POST"])
def event_add():
    conn = get_connection()

    assets = conn.execute(
        "SELECT asset_id, asset_name FROM assets WHERE status='Active' ORDER BY asset_name"
    ).fetchall()

    if request.method == "POST":
        asset_id = request.form["asset_id"]
        event_type = request.form["event_type"]
        event_subtype = request.form.get("event_subtype") if event_type == "Other" else None
        description = request.form["description"]
        cost = request.form.get("cost")
        name = request.form.get("name")

        created_on = datetime.now().strftime("%d/%m/%Y %H:%M")

        conn.execute(
            """
            INSERT INTO events
            (asset_id, event_type, event_subtype, description, cost, name, created_on)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                event_type,
                event_subtype,
                description,
                float(cost) if cost else None,
                name,
                created_on
            )
        )
        conn.commit()
        conn.close()

        flash("Event logged successfully")
        return redirect(url_for("event_add"))

    conn.close()
    return render_template("event_add.html", assets=assets)

# ---------------- EVENT PAGE END ---------------- #

# ---------------- ATTENDANCE EXPORT  ---------------- #

@app.route("/history/attendance/export")
def attendance_history_export():
    current_week = get_current_week_number()

    conn = get_connection()
    rows = conn.execute("""
        SELECT p.recorded_on, p.asset_id, a.asset_name, p.status
        FROM pm_attendance p
        JOIN assets a ON a.asset_id = p.asset_id
        WHERE p.week_number < ?
        ORDER BY p.recorded_on DESC
    """, (current_week,)).fetchall()
    conn.close()

    output = "Date,Asset ID,Asset Name,Status\n"
    for r in rows:
        output += f"{r['recorded_on']},{r['asset_id']},{r['asset_name']},{r['status']}\n"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_history.csv"}
    )

# ---------------- ATTENDANCE EXPORT END ---------------- #

# ---------------- FINDINGS ---------------- #

@app.route("/findings/add", methods=["GET", "POST"])
def findings_add():
    week = request.args.get("week", type=int) or get_current_week_number()
    asset_id = request.args.get("asset_id")

    if not asset_id:
        flash("Asset not selected")
        return redirect(url_for("pm_attendance", week=week))

    conn = get_connection()

    record = conn.execute("""
        SELECT status FROM pm_attendance
        WHERE asset_id = ? AND week_number = ?
    """, (asset_id, week)).fetchone()

    if not record or record["status"] != "DONE":
        conn.close()
        flash("Findings can only be added for DONE assets")
        return redirect(url_for("pm_attendance", week=week))

    asset = conn.execute("""
        SELECT asset_id, asset_name, asset_type FROM assets
        WHERE asset_id = ?
    """, (asset_id,)).fetchone()

    tags = conn.execute("""
        SELECT tag_code, tag_label FROM finding_tags
        WHERE asset_type = ?
        ORDER BY tag_label
    """, (asset["asset_type"],)).fetchall()

    existing = conn.execute("""
        SELECT tag_code, note FROM findings_log
        WHERE asset_id = ? AND week_number = ?
    """, (asset_id, week)).fetchall()

    existing_map = {r["tag_code"]: r["note"] for r in existing}

    if request.method == "POST":
        selected_tags = request.form.getlist("tags")
        note = request.form.get("note", "").strip()

        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        # remove previous tags for this week then add selected
        conn.execute("""
            DELETE FROM findings_log
            WHERE asset_id = ? AND week_number = ?
        """, (asset_id, week))

        for t in selected_tags:
            conn.execute("""
                INSERT OR IGNORE INTO findings_log
                (asset_id, week_number, tag_code, note, created_on)
                VALUES (?, ?, ?, ?, ?)
            """, (asset_id, week, t, note if note else None, now))

        conn.commit()
        conn.close()

        flash("Findings saved successfully")
        return redirect(url_for("pm_attendance", week=week, entry=1))

    conn.close()

    return render_template(
        "findings_add.html",
        week=week,
        asset=asset,
        tags=tags,
        existing_map=existing_map
    )


@app.route("/history/findings", methods=["GET"])
def findings_history():
    current_week = get_current_week_number()

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    asset_id = request.args.get("asset_id")
    tag_code = request.args.get("tag_code")

    query = """
        SELECT 
            f.created_on,
            f.asset_id,
            a.asset_name,
            a.asset_type,
            f.tag_code,
            t.tag_label,
            f.note
        FROM findings_log f
        JOIN assets a ON a.asset_id = f.asset_id
        LEFT JOIN finding_tags t ON t.tag_code = f.tag_code AND t.asset_type = a.asset_type
        WHERE f.week_number < ?
    """
    params = [current_week]

    if from_date:
        query += " AND f.created_on >= ?"
        params.append(from_date)

    if to_date:
        query += " AND f.created_on <= ?"
        params.append(to_date + " 23:59")

    if asset_id:
        query += " AND f.asset_id = ?"
        params.append(asset_id)

    if tag_code:
        query += " AND f.tag_code = ?"
        params.append(tag_code)

    query += " ORDER BY f.created_on DESC"

    conn = get_connection()
    records = conn.execute(query, params).fetchall()

    assets = conn.execute(
        "SELECT asset_id, asset_name FROM assets ORDER BY asset_name"
    ).fetchall()

    all_tags = conn.execute("""
        SELECT DISTINCT tag_code, tag_label
        FROM finding_tags
        ORDER BY tag_label
    """).fetchall()

    conn.close()

    return render_template(
        "findings_history.html",
        records=records,
        assets=assets,
        all_tags=all_tags,
        filters={
            "from_date": from_date,
            "to_date": to_date,
            "asset_id": asset_id,
            "tag_code": tag_code
        }
    )

@app.route("/history/findings/export")
def findings_history_export():
    current_week = get_current_week_number()

    conn = get_connection()
    rows = conn.execute("""
        SELECT f.created_on, f.asset_id, a.asset_name, a.asset_type, f.tag_code, f.note
        FROM findings_log f
        JOIN assets a ON a.asset_id = f.asset_id
        WHERE f.week_number < ?
        ORDER BY f.created_on DESC
    """, (current_week,)).fetchall()
    conn.close()

    output = "Date,Asset ID,Asset Name,Asset Type,Finding Tag,Note\n"
    for r in rows:
        output += f"{r['created_on']},{r['asset_id']},{r['asset_name']},{r['asset_type']},{r['tag_code']},{(r['note'] or '')}\n"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=findings_history.csv"}
    )

# ---------------- FINDINGS END ---------------- #

# ---------------- EVENT EXPORT  ---------------- #

@app.route("/history/events/export")
def events_history_export():
    conn = get_connection()
    rows = conn.execute("""
        SELECT created_on, asset_id, event_type, event_subtype, description, cost, name
        FROM events
        ORDER BY created_on DESC
    """).fetchall()
    conn.close()

    output = "Date,Asset ID,Event Type,Subtype,Description,Cost,Name\n"
    for r in rows:
        output += f"{r['created_on']},{r['asset_id']},{r['event_type']},{r['event_subtype'] or ''},{r['description']},{r['cost'] or ''},{r['name'] or ''}\n"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=events_history.csv"}
    )

# ---------------- EVENT EXPORT END ---------------- #


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
