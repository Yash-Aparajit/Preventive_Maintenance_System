from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import init_db, get_connection

app = Flask(__name__)
app.secret_key = "pm_system_secret"

# STATIC USERS
USERS = {
    "developer": {"password": "your password", "role": "developer"},
    "user": {"password": "your password 2", "role": "maintenance"},
}


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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
