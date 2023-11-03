from flask import Flask, redirect, render_template, request, session

app = Flask(__name__)

# Flask session


# HOME
# Login / List upcoming shifts
@app.route("/", methods=["GET", "POST"])
def index():
    # If logged in, display schedule
    if request.method == "POST":
        return render_template("index.html")

    # Render login page
    else:
        return render_template("login.html")


# HIRING
# Hiring form / completed hiring
@app.route("/hiring", methods=["GET", "POST"])
def hiring():
    # After hiring is submitted
    if request.method == "POST":
        return render_template("hired.html")

    # If starting new hiring
    else:
        return render_template("hiring.html")


# SETTINGS
# Add member
@app.route("/add_member", methods=["GET", "POST"])
def add_member():
    # Add member to db
    if request.method == "POST":
        return render_template("added.html")

    # Blank add member form
    else:
        return render_template("add.html")


# Remove member
@app.route("/remove_member", methods=["GET", "POST"])
def remove_member():
    # Remove member from active status
    if request.method == "POST":
        return render_template("removed.html")

    # Blank removal form
    else:
        return render_template("remove.html")


# Change member
@app.route("/change_member", methods=["GET", "POST"])
def change_member():
    # Submit member changes
    if request.method == "POST":
        return render_template("changed.html")

    # Blank member change form
    else:
        return render_template("change.html")
        