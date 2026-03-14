from flask import Blueprint, render_template, request, redirect, session
import sqlite3

admin_bp = Blueprint("admin", __name__)

def get_db():
    return sqlite3.connect("voting.db", check_same_thread=False)

# ----------------------------
# ADMIN LOGIN PAGE
# ----------------------------
@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM admin WHERE username=? AND password=?", (username, password))
        admin = cur.fetchone()

        if admin:
            session["admin"] = username
            return redirect("/admin/dashboard")
        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

# ----------------------------
# ADMIN DASHBOARD
# ----------------------------
@admin_bp.route("/admin/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin/login")
    return render_template("admin_dashboard.html")

# ----------------------------
# ADD CANDIDATE
# ----------------------------
@admin_bp.route("/admin/add-candidate", methods=["GET", "POST"])
def add_candidate():
    if "admin" not in session:
        return redirect("/admin/login")

    if request.method == "POST":
        name = request.form["name"]
        party = request.form["party"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO candidates (name, party) VALUES (?, ?)", (name, party))
        conn.commit()
        return redirect("/admin/view-candidates")

    return render_template("add_candidate.html")

# ----------------------------
# VIEW CANDIDATES
# ----------------------------
@admin_bp.route("/admin/view-candidates")
def view_candidates():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates")
    candidates = cur.fetchall()

    return render_template("view_candidates.html", candidates=candidates)

# ----------------------------
# VIEW VOTERS
# ----------------------------
@admin_bp.route("/admin/view-voters")
def view_voters():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM voters")
    voters = cur.fetchall()

    return render_template("view_voters.html", voters=voters)

# ----------------------------
# VIEW RESULTS
# ----------------------------
@admin_bp.route("/admin/results")
def results():
    if "admin" not in session:
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT candidates.name, candidates.party, COUNT(votes.id) 
        FROM candidates 
        LEFT JOIN votes ON candidates.id = votes.candidate_id
        GROUP BY candidates.id
    """)
    results = cur.fetchall()

    return render_template("results.html", results=results)

# ----------------------------
# LOGOUT
# ----------------------------
@admin_bp.route("/admin/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin/login")
