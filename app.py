from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3
import pickle, base64, io
from PIL import Image
import numpy as np
import mediapipe as mp

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for sessions

mp_face_mesh = mp.solutions.face_mesh

# DB path
DB_PATH = "voting.db"  # Make sure this is inside your project folder

# ---------- Helper functions ----------
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def decode_base64_image(data_url):
    header, encoded = data_url.split(",",1)
    data = base64.b64decode(encoded)
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return np.array(img)[:, :, ::-1]  # BGR

def image_to_embedding(bgr_image):
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as fm:
        import cv2
        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        results = fm.process(rgb)
        if not results.multi_face_landmarks:
            return None
        lm = results.multi_face_landmarks[0]
        flat = []
        for p in lm.landmark:
            flat.extend([p.x, p.y, p.z])
        arr = np.array(flat, dtype=np.float32)
        arr = arr - arr.mean()
        norm = np.linalg.norm(arr)
        if norm > 1e-6:
            arr = arr / norm
        return arr

def compare_embeddings(a, b):
    if a is None or b is None:
        return 0.0
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < 1e-9:
        return 0.0
    return float(np.dot(a,b)/denom)
# ---------- End helpers ----------

# ---------- Frontend Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/vote")
def vote():
    return render_template("vote.html")

@app.route("/results")
def results():
    return render_template("results.html")
# ---------- End Frontend ----------

# ---------- Voter APIs ----------
@app.route("/api/candidates")
def api_candidates():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id,name,party FROM candidates")
    data = [{"id":r[0],"name":r[1],"party":r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(data)

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    name = data.get("name")
    aadhaar = data.get("aadhaar")
    image = data.get("image")
    if not (name and aadhaar and image):
        return jsonify({"success":False,"error":"Missing fields"}),400
    try:
        bgr = decode_base64_image(image)
    except:
        return jsonify({"success":False,"error":"Invalid image"}),400
    emb = image_to_embedding(bgr)
    if emb is None: return jsonify({"success":False,"error":"No face detected"}),400
    pickled = pickle.dumps(emb)
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE aadhaar=?",(aadhaar,))
    if c.fetchone():
        conn.close()
        return jsonify({"success":False,"error":"Aadhaar exists"}),400
    c.execute("INSERT INTO users(name,aadhaar,face_encoding) VALUES (?,?,?)",
              (name,aadhaar,pickled))
    conn.commit()
    conn.close()
    return jsonify({"success":True,"message":"Registered"})

@app.route("/api/verify_and_vote", methods=["POST"])
def api_verify_and_vote():
    data = request.get_json()
    image = data.get("image")
    candidate_id = data.get("candidate_id")
    aadhaar = data.get("aadhaar")
    if not (image and candidate_id):
        return jsonify({"success":False,"error":"Missing image/candidate"}),400
    try:
        bgr = decode_base64_image(image)
    except:
        return jsonify({"success":False,"error":"Invalid image"}),400
    emb = image_to_embedding(bgr)
    if emb is None: return jsonify({"success":False,"error":"No face detected"}),400

    conn = get_db()
    c = conn.cursor()
    matched_user = None

    if aadhaar:
        c.execute("SELECT id,face_encoding,has_voted,name FROM users WHERE aadhaar=?",(aadhaar,))
        row = c.fetchone()
        if not row: conn.close(); return jsonify({"success":False,"error":"Aadhaar not found"}),404
        stored = pickle.loads(row[1])
        if compare_embeddings(stored,emb)<0.45:
            conn.close(); return jsonify({"success":False,"error":"Face mismatch"}),403
        matched_user = {"id":row[0],"has_voted":row[2],"name":row[3]}
    else:
        c.execute("SELECT id,face_encoding,has_voted,name FROM users")
        rows = c.fetchall()
        best_sim = -1; best_user = None
        for r in rows:
            stored = pickle.loads(r[1])
            sim = compare_embeddings(stored,emb)
            if sim > best_sim:
                best_sim = sim
                best_user = {"id":r[0],"has_voted":r[2],"name":r[3]}
        if best_user is None or best_sim<0.45: conn.close(); return jsonify({"success":False,"error":"No match"}),404
        matched_user = best_user

    if matched_user["has_voted"]:
        conn.close(); return jsonify({"success":False,"error":"Already voted"}),403

    c.execute("SELECT id,name FROM candidates WHERE id=?",(candidate_id,))
    cand = c.fetchone()
    if not cand: conn.close(); return jsonify({"success":False,"error":"Invalid candidate"}),400

    c.execute("INSERT INTO votes(user_id,candidate_id) VALUES (?,?)",(matched_user["id"],candidate_id))
    c.execute("UPDATE users SET has_voted=1 WHERE id=?",(matched_user["id"],))
    conn.commit(); conn.close()
    return jsonify({"success":True,"message":"Vote recorded","user":matched_user["name"],"candidate":cand[1]})

@app.route("/api/results")
def api_results():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT candidates.name,candidates.party,COUNT(votes.id)
        FROM candidates LEFT JOIN votes ON candidates.id=votes.candidate_id
        GROUP BY candidates.id
    """)
    results = [{"name":r[0],"party":r[1],"votes":r[2]} for r in c.fetchall()]
    conn.close()
    return jsonify(results)
# ---------- End Voter APIs ----------

# ---------- Admin Routes ----------
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username=? AND password=?",(username,password))
        if c.fetchone():
            session["admin"] = username
            conn.close()
            return redirect("/admin/dashboard")
        conn.close()
        return render_template("admin_login.html", error="Invalid credentials")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session: return redirect("/admin/login")
    return render_template("admin_dashboard.html")

@app.route("/admin/add-candidate", methods=["GET","POST"])
def admin_add_candidate():
    if "admin" not in session: return redirect("/admin/login")
    if request.method=="POST":
        name = request.form["name"]
        party = request.form["party"]
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO candidates(name,party) VALUES (?,?)",(name,party))
        conn.commit(); conn.close()
        return redirect("/admin/view-candidates")
    return render_template("add_candidates.html")

@app.route("/admin/view-candidates")
def admin_view_candidates():
    if "admin" not in session: return redirect("/admin/login")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    candidates = c.fetchall(); conn.close()
    return render_template("view_candidates.html", candidates=candidates)

@app.route("/admin/view-voters")
def admin_view_voters():
    if "admin" not in session: return redirect("/admin/login")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id,name,aadhaar,has_voted FROM users")
    voters = c.fetchall(); conn.close()
    return render_template("view_voters.html", voters=voters)

@app.route("/admin/results")
def admin_results():
    if "admin" not in session: return redirect("/admin/login")
    conn = get_db(); c = conn.cursor()
    c.execute("""
        SELECT candidates.name,candidates.party,COUNT(votes.id)
        FROM candidates LEFT JOIN votes ON candidates.id=votes.candidate_id
        GROUP BY candidates.id
    """)
    results = c.fetchall(); conn.close()
    return render_template("results.html", results=results)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")
# ---------- End Admin Routes ----------

# ---------- RUN SERVER ----------
if __name__=="__main__":
    app.run(debug=True)
