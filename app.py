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
app.secret_key = ")\xd9%q\xdb\xae(`hg\x1f\xe1\x9e\x99=y"

# Configure login session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure db
engine = create_engine("sqlite:///database.db", echo=True)
session_factory = sessionmaker(bind=engine)
db = session_factory()

# Constants & Global variables
PLATOON_SIZE = 10


# HOME
# Login / List upcoming shifts
@app.route("/", methods=["GET", "POST"])
def index():
    # If logged in, display schedule
    if not session.get("user_id"):
        return redirect("/login")
    else:
        return render_template("index.html")





# HIRING
# Hiring form / completed hiring
"""Select which platoon is covering OT"""
@app.route("/hiring_a", methods=["GET", "POST"])
@login_required
def hiring_a():
    # After hiring is submitted
    if request.method == "POST":
        # Save platoon choice for next route
        session["platoon"] = request.form.get("platoon")

        return redirect("/hiring_b")

    # If starting new hiring
    else:
        return render_template("hiring_a.html")


"""Select any members that are not available on cover days"""
@app.route("/hiring_b", methods=["GET", "POST"])
@login_required
def hiring_b():

    # After hiring is submitted
    if request.method == "POST":
        # Create lists & variables outside of loop 
        firefighters_availability = []
        firefighters_hours = []
        counter = 1

        # Loop through each firefighter
        for firefighter in session['firefighters']:
            # Create html tag id
            form_id = "1st_day_" + str(counter)

            # Collect this firefighter's availability
            results_avail = {
                'username': firefighter['username'],
                'avail_1': request.form.get(form_id)
            }

            # Add results to firefighters list
            firefighters_availability.append(results_avail)

            # If the firefighter is unavailable for hours, add the hours to the hours list
            if results_avail['avail_1'] == "hours":

                # Create html tag id's
                start_id = "hours_1_start_" + str(counter)
                end_id = "hours_1_end_" + str(counter)

                # Get start & end hours
                results_hours = {
                    'username': firefighter['username'],
                    'hours_1_start': request.form.get(start_id),
                    'hours_1_end': request.form.get(end_id)
                }

                # Add results to hours list
                firefighters_hours.append(results_hours)

            counter += 1

        print(firefighters_availability)
        print(firefighters_hours)
        return redirect("/hiring_c")

    # If starting new hiring via GET
    else:
        # query db for list of elligible firefighters
        firefighters = db.execute(select(User.id, User.username).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").order_by(User.id))
        firefighters = firefighters.mappings().all()
        print(f"result dict: {firefighters}")
        session['firefighters'] = firefighters
        print(session['firefighters'])
        return render_template("hiring_b.html", firefighters=firefighters, platoon=session['platoon'])


"""Load the two platoons to be covered for; select which members are out"""
@app.route("/hiring_c", methods=["GET", "POST"])
@login_required
def hiring_c():
    # After hiring is submitted
    if request.method == "POST":
        return render_template("hiring_d.html")

    # If starting new hiring
    else:
        return render_template("hiring_c.html")


"""Hire for shifts, return hiring list"""
@app.route("/hiring_c", methods=["GET", "POST"])
@login_required
def hiring_d():
    # After hiring is submitted
    if request.method == "POST":
        return render_template("hired.html")

    # If starting new hiring
    else:

        return render_template("hiring_d.html")


# SETTINGS
# Add member
@app.route("/add_member", methods=["GET", "POST"])
# @login_required
def add_member():

    # Add member to db
    if request.method == "POST":

        # Check for inputs
        if not request.form.get("username"):
            return render_template("apology.html", type="username")
        if not request.form.get("password"):
            return render_template("apology.html", type="password")
        if not request.form.get("platoon"):
            return render_template("apology.html", type="platoon")
        if not request.form.get("active"):
            return render_template("apology.html", type="active status")
        if not request.form.get("elligibility"):
            return render_template("apology.html", type="elligibility")

        username = request.form.get("username")
        password = request.form.get("password")
        platoon = request.form.get("platoon")
        active = request.form.get("active")
        elligibility = request.form.get("elligibility")

        # Check availability of username
        result = db.execute(select(User.username))
        users = result.mappings().all()

        for user in users:
            if user.username == username:
                return render_template("apology.html", type="username taken")

        # Hash password
        hashword = generate_password_hash(password)
        
        # Insert username & password into db
        db.execute(insert(User), {"username": username, "hash": hashword, "platoon": platoon, "active": active, "elligible": elligibility})
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

        result = db.execute(select(User.id, User.username, User.hash).where(User.username == username))
        result = result.mappings().first()

        # Verify username in db
        if result == None:
            return render_template("apology.html", type="incorrect username")

        # Verify password is correct
        if check_password_hash(result.hash, password) == False:
            return render_template("apology.html", type="incorrect password")
        
        # Save user in session
        session["user_id"] = result.id

        # Send to homepage
        return redirect("/") 
    # 
    else:
        return render_template("login.html")


# Log out
@app.route("/logout")
def logout():
    session["user_id"] = None
    return redirect("/")