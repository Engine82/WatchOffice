from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

# https://pydoc.dev/werkzeug/latest/werkzeug.security.html
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required
from helpers import Base, User


# Configure app
app = Flask(__name__)

# Configure secret key
app.secret_key = '5b80b04e505142179ddb441c2a2cd1e067038e3b422e1fd6add2e8c9961fe4aa'

# Configure login session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure db
engine = create_engine("sqlite:///database.db", echo=True)
session_factory = sessionmaker(bind=engine)
db = session_factory()

# Global variables
PLATOON_SIZE = 10


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
# @login_required
def add_member():

    # Add member to db
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("apology.html", type="username")
        if not request.form.get("password"):
            return render_template("apology.html", type="password")
        if not request.form.get("platoon"):
            return render_template("apology.html", type="platoon")

        # Check for username, password and platoon
        username = request.form.get("username")
        password = request.form.get("password")
        platoon = request.form.get("platoon")

        # Check availability of username
        result = db.execute(select(User.username))
        users = result.mappings().all()

        for user in users:
            if user.username == username:
                return render_template("apology.html", type="username taken")

        # Hash password
        hashword = generate_password_hash(password)
        
        # Insert username & password into db
        db.execute(insert(User), {"username": username, "hash": hashword, "platoon": platoon})
        db.commit()
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
        

# Session
# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # When login form is submitted
    if request.method == "POST":

        # Check for username and password
        if not request.form.get("username"):
            render_template("apology.html", type="username")

        elif not request.form.get("password"):
            render_template("apology.html", type="password")
        
        # Query db for username
        username = request.form.get("username")
        password = request.form.get("password")

        
        """user_data = db.execute(
            "SELECT * FROM users WHERE username = (?)", request.form.get("username")        
        )

        stmt = select(User.username, User.hash, User.id).where(User.username.in_([username]))
        with engine.connect() as connection:
            for row in connection.execute(stmt):
                print(row)
                check = check_password_hash(row, password)
                print("check")
        

        ````1!!!!!!!!!!!!!!!! NEW BELOW !!!!!!!!!!!!!!!!!!!!!!"""
        result = db.execute(select(User.id, User.username, User.hash).where(User.username == username))
        user_dict = result.mappings().first()
        print(user_dict)
        print(user_dict.id)

        # Verify username in db and password is correct


        # Save user in session
        session['username'] = user_dict.username

        # Send to homepage
        return redirect("/")
    
    # 
    else:
        return render_template("login.html")


# Log out
@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")