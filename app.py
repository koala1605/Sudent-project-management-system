import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        week TEXT,
        title TEXT,
        description TEXT,
        filename TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (email,password) VALUES (?,?)",(email,password))
            conn.commit()
        except:
            conn.close()
            return "User already exists"

        conn.close()
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password))
    user = cur.fetchone()
    conn.close()

    if user:
        session["user_id"] = user[0]
        return redirect("/dashboard")

    return "Invalid credentials"


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # total projects
    cur.execute("SELECT COUNT(*) FROM projects WHERE user_id=?", (session["user_id"],))
    total = cur.fetchone()[0]

    # project list
    cur.execute("SELECT week, title, description, filename FROM projects WHERE user_id=?", (session["user_id"],))
    projects = cur.fetchall()

    conn.close()

    return render_template("dashboard.html", total=total, projects=projects)


# ✅ FIXED ROUTE (IMPORTANT)
@app.route("/submit_project")
def submit_page():
    if "user_id" not in session:
        return redirect("/")
    return render_template("submit.html")


@app.route("/submit_project", methods=["POST"])
def submit_project():
    if "user_id" not in session:
        return redirect("/")

    week = request.form["week"]
    title = request.form["title"]
    description = request.form["description"]
    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO projects(user_id,week,title,description,filename)
    VALUES (?,?,?,?,?)
    """,(session["user_id"],week,title,description,filename))
    conn.commit()
    conn.close()

    return redirect("/view_projects")


@app.route("/view_projects")
def view_projects():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT week,title,description,filename FROM projects WHERE user_id=?",
                (session["user_id"],))
    projects = cur.fetchall()
    conn.close()

    return render_template("view_projects.html", projects=projects)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)