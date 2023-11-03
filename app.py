from flask import Flask, redirect, render_template, request, session
from flask_session import Session

from helpers import login_required


# Configure app
app = Flask(__name__)

# Configure secret key
app.secret_key = '5b80b04e505142179ddb441c2a2cd1e067038e3b422e1fd6add2e8c9961fe4aa'

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# HOME
# Login / List upcoming shifts
@app.route("/", methods=["GET", "POST"])
def index():
    # If logged in, display schedule
    if not session.get("name"):
        return redirect("/login")
    else:
        return render_template("index.html")


# HIRING
# Hiring form / completed hiring
@app.route("/hiring_a", methods=["GET", "POST"])
@login_required
def hiring_a():
    # After hiring is submitted
    if request.method == "POST":
        return redirect("/hiring_b")

    # If starting new hiring
    else:
        return render_template("hiring_a.html")


@app.route("/hiring_b", methods=["GET", "POST"])
@login_required
def hiring_b():
    # After hiring is submitted
    if request.method == "POST":
        return redirect("/hiring_c")

    # If starting new hiring
    else:
        return render_template("hiring_b.html")


@app.route("/hiring_c", methods=["GET", "POST"])
@login_required
def hiring_c():
    # After hiring is submitted
    if request.method == "POST":
        return render_template("hired.html")

    # If starting new hiring
    else:
        return render_template("hiring_c.html")


# SETTINGS
# Add member
@app.route("/add_member", methods=["GET", "POST"])
@login_required
def add_member():
    # Add member to db
    if request.method == "POST":
        return render_template("added.html")

    # Blank add member form
    else:
        return render_template("add.html")


# Remove member
@app.route("/remove_member", methods=["GET", "POST"])
@login_required
def remove_member():
    # Remove member from active status
    if request.method == "POST":
        return render_template("removed.html")

    # Blank removal form
    else:
        return render_template("remove.html")


# Change member
@app.route("/change_member", methods=["GET", "POST"])
@login_required
def change_member():
    # Submit member changes
    if request.method == "POST":
        return render_template("changed.html")

    # Blank member change form
    else:
        return render_template("change.html")
        

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["name"] = request.form.get("name")
        return redirect("/")
    else:
        return render_template("login.html")


# Log out
@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")