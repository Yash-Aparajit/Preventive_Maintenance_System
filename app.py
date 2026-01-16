from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, date, timedelta
from models import init_db, get_connection

app = Flask(__name__)
app.secret_key = "pm_system_secret"

# STATIC USERS
USERS = {
    "developer": {"password": "dev@123@123", "role": "developer"},
    "user": {"password": "user@jeena", "role": "maintenance"},
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
    conn.close()

    status_map = {r["asset_id"]: r["status"] for r in records}
    recorded_on = records[0]["recorded_on"] if records else None

    calendar_label = get_calendar_label_from_week(week)

    return render_template(
        "pm_attendance.html",
        week=week,
        calendar_label=calendar_label,
        assets=assets,
        status_map=status_map,
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
