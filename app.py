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
def hire():
    # After hiring is submitted
    if request.method == "POST":
        return render_template("hired.html")

    # If starting new hiring
    else:
        return render_template("hiring.html")
