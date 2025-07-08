
# Insurance Regulatory Management System - Final Version
# Includes: User Registration, Email Confirmation, Login Restriction, Resend Confirmation
import sqlite3
import hashlib
import secrets
import smtplib
from email.message import EmailMessage
from flask import Flask, request, session, redirect, url_for, render_template

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database initialization
def init_db():
    conn = sqlite3.connect("insurance_regulatory.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            email TEXT UNIQUE,
            confirmed INTEGER DEFAULT 0,
            confirmation_token TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Email sending function
def send_confirmation_email(email, token):
    msg = EmailMessage()
    msg["Subject"] = "LIRC Email Confirmation"
    msg["From"] = SMTP_USERNAME
    msg["To"] = email
    msg.set_content(f"Please confirm your email by clicking the link: http://localhost:5000/confirm/{token}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)

# SMTP credentials (replace with your actual credentials)
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"

# Landing page
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("""
        <h2>Welcome to LIBERIA INSURANCE REGULATORY COMMISSION (LIRC)</h2>
        <p>LIRC Portal is an online application that manages all of your formal communications with your regulator.</p>
        <form method="POST" action="/login">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Login</button>
        </form>
        <p><a href="/register">Register</a> | <a href="/resend">Resend Confirmation</a></p>
    """)

# Dashboard
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("dashboard_1_updated.html")
    if "user_id" not in session:
        return redirect(url_for("home"))
    return f"<h2>Welcome {session['user_id']}</h2><p>Email confirmed: Yes</p><a href='/logout'>Logout</a>"

# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        token = secrets.token_urlsafe(16)

        try:
            conn = sqlite3.connect("insurance_regulatory.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash, email, confirmation_token) VALUES (?, ?, ?, ?)",
                           (username, password_hash, email, token))
            conn.commit()
            conn.close()
            send_confirmation_email(email, token)
            return "Registration successful! Please check your email to confirm."
        except sqlite3.IntegrityError:
            return "Username or email already exists."
    return '''
        <h2>Register</h2>
        <form method="POST">
            Username: <input name="username"><br>
            Email: <input name="email"><br>
            Password: <input name="password" type="password"><br>
            <button type="submit">Register</button>
        </form>
    '''

# Email confirmation
@app.route("/confirm/<token>")
def confirm_email(token):
    conn = sqlite3.connect("insurance_regulatory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE confirmation_token = ?", (token,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET confirmed = 1 WHERE id = ?", (user[0],))
        conn.commit()
        conn.close()
        return "Email confirmed! You can now log in."
    conn.close()
    return "Invalid or expired token."

# Login
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect("insurance_regulatory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, confirmed FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        if user[1] == 1:
            session["user_id"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Email not confirmed. Please check your inbox."
    return "Invalid credentials."

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("home"))

# Resend confirmation
@app.route("/resend", methods=["GET", "POST"])
def resend():
    if request.method == "POST":
        email = request.form["email"]
        conn = sqlite3.connect("insurance_regulatory.db")
        cursor = conn.cursor()
        cursor.execute("SELECT confirmation_token, confirmed FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user:
            if user[1] == 1:
                return "Email already confirmed."
            send_confirmation_email(email, user[0])
            return "Confirmation email resent."
        return "Email not found."
    return '''
        <h2>Resend Confirmation Email</h2>
        <form method="POST">
            Email: <input name="email"><br>
            <button type="submit">Resend</button>
        </form>
    '''

if __name__ == "__main__":
    app.run(debug=True)



