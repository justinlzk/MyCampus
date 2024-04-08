import os
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    classes = db.execute("SELECT id, user_id, class FROM schedules WHERE user_id = ? ORDER BY period", session["user_id"])
    display_grade = {}
    assignments = {}
    for c in classes:
        points_earned = db.execute("SELECT SUM(points_earned) AS 'pe' FROM grades WHERE user_id = ? AND class_id = ?", session["user_id"], c["id"])[0]['pe']
        points_possible = db.execute("SELECT SUM(points_possible) AS 'pp' FROM grades WHERE user_id = ? AND class_id = ?", session["user_id"], c["id"])[0]['pp']
        if points_earned is not None and points_possible is not None:
            pe = round(float(points_earned), 2)
            pp = round(float(points_possible), 2)
            final = round(pe / pp * 100, 2)
            display_grade[c["id"]] = str(final) + "%"
        else:
            display_grade[c["id"]] = "No Grade"
        assignments[c['id']] = str(db.execute("SELECT COUNT(id) as total FROM homework WHERE class_id = ?", c['id'])[0]['total']) + " assignment"
        if assignments[c['id']] != 1:
            assignments[c['id']] += "s"

    return render_template("index.html", classes=classes, display_grade=display_grade, assignments=assignments)

@app.route("/schedule", methods=["GET"])
@login_required
def schedule():
    schedule = db.execute("SELECT * FROM schedules WHERE user_id = ? ORDER BY period", session["user_id"])
    return render_template("schedule.html", schedule=schedule)

@app.route("/add-class", methods=["POST"])
def add_class():
    to_add = {}
    to_add["class"] = request.form.get("class")
    to_add["period"] = request.form.get("period")
    to_add["teacher"] = request.form.get("teacher")
    to_add["location"] = request.form.get("location")
    to_add["email"] = request.form.get("email")

    db.execute("INSERT INTO schedules (user_id, class, period, teacher, location, email) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], to_add["class"], to_add["period"], to_add["teacher"], to_add["location"], to_add["email"])

    flash(f"{to_add['class']} added successfully")
    return redirect("/schedule")

@app.route("/edit-class", methods=["POST"])
def edit_class():
    to_edit = {}
    to_edit["id"] = request.form.get("id")
    to_edit["class"] = request.form.get("class")
    to_edit["period"] = request.form.get("period")
    to_edit["teacher"] = request.form.get("teacher")
    to_edit["location"] = request.form.get("location")
    to_edit["email"] = request.form.get("email")

    db.execute("UPDATE schedules SET class = ?, period = ?, teacher = ?, location = ?, email = ? WHERE id = ?", to_edit["class"], to_edit["period"], to_edit["teacher"], to_edit["location"], to_edit["email"], to_edit["id"])
    flash(f"{to_edit['class']} edited successfully")
    return redirect("/schedule")

@app.route("/delete-class", methods=["POST"])
def delete_class():
    to_delete = {}
    to_delete["id"] = request.form.get("id")
    to_delete["class"] = request.form.get("class")

    db.execute("DELETE FROM schedules WHERE id = ?", to_delete['id'])
    db.execute("DELETE FROM grades WHERE class_id = ?", to_delete['id'])
    flash(f"{to_delete['class']} deleted successfully")
    return redirect("/schedule")

@app.route("/delete-all-classes", methods=["POST"])
def delete_all_classes():
    db.execute("DELETE FROM schedules WHERE user_id = ?", session["user_id"])
    db.execute("DELETE FROM grades WHERE user_id = ?", session["user_id"])
    flash("All classes deleted successfully")
    return redirect("/schedule")

@app.route("/grades", methods=["GET"])
@login_required
def grades():
    classes = db.execute("SELECT id, user_id, class, teacher FROM schedules WHERE user_id = ? ORDER BY period", session["user_id"])
    grades = {}
    display_grade = {}
    for c in classes:
        points_earned = db.execute("SELECT SUM(points_earned) AS 'pe' FROM grades WHERE user_id = ? AND class_id = ?", session["user_id"], c["id"])[0]['pe']
        points_possible = db.execute("SELECT SUM(points_possible) AS 'pp' FROM grades WHERE user_id = ? AND class_id = ?", session["user_id"], c["id"])[0]['pp']
        # If there are existing grades
        if points_earned is not None and points_possible is not None:
            pe = round(float(points_earned), 2)
            pp = round(float(points_possible), 2)
            final = round(pe / pp * 100, 2)
            display_grade[c["id"]] = [pe, pp, str(final) + "%"]
        else:
            display_grade[c["id"]] = ["", "", "No Grade"]
        grades[c["id"]] = db.execute("SELECT id, user_id, name, points_earned, points_possible FROM grades WHERE user_id = ? AND class_id = ? ORDER BY name", session["user_id"], c["id"])
    return render_template("grades.html", classes=classes, display_grade=display_grade, grades=grades)

@app.route("/add-grade", methods=["POST"])
def add_grade():
    to_add = {}
    to_add["name"] = request.form.get("name")
    to_add["class_id"] = request.form.get("class_id")
    to_add["class"] = request.form.get("class")
    to_add["points_earned"] = request.form.get("points_earned")
    to_add["points_possible"] = request.form.get("points_possible")

    db.execute("INSERT INTO grades (user_id, name, class_id, class, points_possible, points_earned) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], to_add["name"], to_add["class_id"], to_add["class"], to_add["points_possible"], to_add["points_earned"])
    flash(f"\"{to_add['name']}\" added to {to_add['class']} successfully")
    return redirect("/grades")

@app.route("/edit-grade", methods=["POST"])
def edit_grade():
    to_edit = {}
    to_edit["id"] = request.form.get("id")
    to_edit["class"] = request.form.get("class")
    to_edit["name"] = request.form.get("name")
    to_edit["points_earned"] = request.form.get("points_earned")
    to_edit["points_possible"] = request.form.get("points_possible")

    db.execute("UPDATE grades SET name = ?, points_earned = ?, points_possible = ? WHERE id = ?", to_edit["name"], to_edit["points_earned"], to_edit["points_possible"], to_edit["id"])
    flash(f"\"{to_edit['name']}\" for {to_edit['class']} edited successfully")
    return redirect("/grades")

@app.route("/delete-grade", methods=["POST"])
def delete_grade():
    to_delete = {}
    to_delete['id'] = request.form.get("id")
    to_delete['class'] = request.form.get("class")
    to_delete['name'] = request.form.get("name")

    db.execute("DELETE FROM grades WHERE id = ?", to_delete['id'])
    flash(f"{to_delete['name']} deleted from {to_delete['class']} successfully")
    return redirect("/grades")

@app.route("/delete-all-grades", methods=["POST"])
def delete_all_grade():
    to_delete = {}
    to_delete['id'] = request.form.get("class_id")
    to_delete['class'] = request.form.get("class")

    db.execute("DELETE FROM grades WHERE class_id = ?", to_delete['id'])
    flash(f"All grades for {to_delete['class']} deleted successfully")
    return redirect("/grades")

def format_date(date):
    if date is None:
        return "No due date"
    x = date.split('-')
    x = datetime.datetime(int(x[0]), int(x[1]), int(x[2]))
    return f"{x.strftime('%A')}, {x.strftime('%B')} {x.strftime('%d')}, {x.strftime('%Y')}"

@app.route("/homework")
@login_required
def homework():
    classes = db.execute("SELECT id, user_id, class, teacher FROM schedules WHERE user_id = ? ORDER BY period", session["user_id"])
    homework= {}
    for c in classes:
        homework[c['id']] = db.execute("SELECT * FROM homework WHERE user_id = ? AND class_id = ? ORDER BY due_date NULLS LAST", session['user_id'], c['id'])
        for h in homework[c['id']]:
            h['due_date_display'] = format_date(h['due_date'])
    return render_template("homework.html", classes=classes, homework=homework)

@app.route("/add-homework", methods=["POST"])
def add_homework():
    to_add = {}
    to_add["name"] = request.form.get("name")
    to_add["class_id"] = request.form.get("class_id")
    to_add["class"] = request.form.get("class")
    to_add["due_date"] = None if not request.form.get("due_date") else request.form.get("due_date")
    to_add["note"] = request.form.get("note")

    db.execute("INSERT INTO homework (user_id, name, class_id, class, due_date, note) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], to_add["name"], to_add["class_id"], to_add["class"], to_add["due_date"], to_add["note"])
    flash(f"\"{to_add['name']}\" added to {to_add['class']} successfully")
    return redirect("/homework")

@app.route("/edit-homework", methods=["POST"])
def edit_homework():
    to_edit = {}
    to_edit["id"] = request.form.get("id")
    to_edit["class"] = request.form.get("class")
    to_edit["name"] = request.form.get("name")
    to_edit["due_date"] = None if not request.form.get("due_date") else request.form.get("due_date")
    to_edit["note"] = request.form.get("note")

    db.execute("UPDATE homework SET name = ?, due_date = ?, note = ? WHERE id = ?", to_edit["name"], to_edit["due_date"], to_edit["note"], to_edit["id"])
    flash(f"\"{to_edit['name']}\" for {to_edit['class']} edited successfully")
    return redirect("/homework")

@app.route("/finish-homework", methods=["POST"])
def finish_homework():
    finished = {}
    finished["name"] = request.form.get("name")
    finished["id"] = request.form.get("id")
    finished["class"] = request.form.get("class")

    db.execute("DELETE FROM homework WHERE id = ?", finished['id'])
    flash(f"\"{finished['name']}\" for {finished['class']} completed")
    return redirect("/homework")


@app.route("/clear-homework", methods=["POST"])
def clear_homework():
    class_id = request.form.get("class_id")
    name = request.form.get("class")

    db.execute("DELETE FROM homework WHERE class_id = ?", class_id)
    flash(f"Homework for {name} cleared")
    return redirect("/homework")



@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Please enter a username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Please enter a password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Please enter a valid username and password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash("Logged in successfully")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    flash("Logged out succesfully")
    return render_template("login.html", out=True)


def upper(password):
    for c in password:
        if c.isupper():
            return True
    return False

def lower(password):
    for c in password:
        if c.islower():
            return True
    return False

def numeric(password):
    for c in password:
        if c.isnumeric():
            return True
    return False

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    # Accessed via post
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username is not empty
        if not username:
            flash("Please provide a username")
            return render_template("register.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username is not taken
        if len(rows) != 0:
            flash("The username you have chosen is already taken")
            return render_template("register.html")

        # Ensure password is not empty
        elif not password:
            flash("Please provide a passowrd")
            return render_template("register.html")

        elif password != request.form.get("confirmation"):
            flash("The passwords you have entered do not match")
            return render_template("register.html")

        # Password requirements
        elif len(password) < 8:
            flash("Please provide a longer password")
            return render_template("register.html")

        elif not upper(password):
            flash("Please provide an uppercase letter in your password")
            return render_template("register.html")

        elif not lower(password):
            flash("Please provide an lowercase letter in your password")
            return render_template("register.html")

        elif not numeric(password):
            flash("Please provide an numeric character in your password")
            return render_template("register.html")

        elif password.isalnum():
            flash("Please provide an special character in your password")
            return render_template("register.html")

        hash = generate_password_hash(request.form.get("password"))

        # Create new user by inserting into users database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)

        # Get session id of user that just regiestered
        user = db.execute("SELECT id FROM users WHERE username = ?", username)

        session["user_id"] = user[0]["id"]

        # Redirect user to home page
        flash("Account created successfully")
        return redirect("/")
    # Accessed via get
    else:
        return render_template("register.html")

