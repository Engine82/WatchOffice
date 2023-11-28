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
PLATOON_OFFICERS = 2
PLATOON_FIREFIGHTERS = 8
DAYS_COVERED = 2
HIRING_TIERS = 2

# Shifts covered:
PLT_1 = {'first_day': '4', 'second_day': '2'}
PLT_2 = {'first_day': '1', 'second_day': '3'}
PLT_3 = {'first_day': '2', 'second_day': '4'}
PLT_4 = {'first_day': '3', 'second_day': '1'}


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

    # After platoon is selected
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

    # After availability is submitted
    if request.method == "POST":

        # Create lists & variables outside of loop 
        officers_availability = []
        officers_hours = []
        firefighters_availability = []
        firefighters_hours = []

        # Loop through each day
        day = 1
        while day <= DAYS_COVERED:

            #Loop through each rank - Officer and Firefighter
            tier = 1
            for rank in session['personnel']:

                # Loop through each firefighter
                person_counter = 1
                for person in rank:
                    
                    # Create html tag id
                    form_id = "day_" + str(day) + "_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)

                    # Collect this firefighter's availability
                    results_avail = {
                        'username': person['username'],
                        'avail_1': request.form.get(form_id),
                        'avail_2': request.form.get(form_id)
                    }

                    # Add results to firefighters list
                    if tier == 1:
                        officers_availability.append(results_avail)
                    elif tier  == 2:
                        firefighters_availability.append(results_avail)

                    # If the firefighter is unavailable for hours, add the hours to the hours list
                    # Create html tag for this cover day
                    avail_tag = 'avail_' + str(day)

                    # If firefighter is unavailable for hours
                    if results_avail[avail_tag] == "hours":

                        # Create html tag id's
                        start_id = "hours_" + str(day) + "_" + session['hiring_tiers'][tier - 1]['tier'] + "_start_" + str(person_counter)
                        end_id = "hours_" + str(day) + "_" + session['hiring_tiers'][tier - 1]['tier'] + "_end_" + str(person_counter)
                        # Get start & end hours
                        results_hours = {
                            'day': day,
                            'username': person['username'],
                            'hours_start': request.form.get(start_id),
                            'hours_end': request.form.get(end_id)
                        }

                        # Add results to hours list
                        if tier == 1:
                            officers_hours.append(results_hours)

                        elif tier == 2:
                            firefighters_hours.append(results_hours)
                        
                    person_counter += 1

                tier += 1

            day += 1
        print(f"firefighters avail: {firefighters_availability}")
        print(f"firefightyers hours: {firefighters_hours}")
        return redirect("/hiring_c")

    # Display the availability form
    else:

        # query db for list of elligible officers & firefighters and save as dicts
        officers = db.execute(select(User.id, User.username, User.rank).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank != "firefighter").order_by(User.id))
        officers = officers.mappings().all()

        firefighters = db.execute(select(User.id, User.username, User.rank).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank == "firefighter").order_by(User.id))
        firefighters = firefighters.mappings().all()

        session['personnel'] = [officers, firefighters]
        print(session['personnel'])
        print(session['personnel'][0])
        print(session['personnel'][1])


        # Create list of titles for HTML
        session['cover_days'] = [{"day": "First Cover Day"}, {"day": "Second Cover Day"}]
        session['hiring_tiers'] = [{"tier": "Officers"}, {"tier": "Firefighters"}]

        return render_template("hiring_b.html", cover_days=session['cover_days'], days_covered=DAYS_COVERED, firefighters=session['personnel'], hiring_tiers=session['hiring_tiers'], platoon=session['platoon'])


"""Load the two platoons to be covered for; select which members are out"""
@app.route("/hiring_c", methods=["GET", "POST"])
@login_required
def hiring_c():

    # Fill empty shifts with available firefighters
    if request.method == "POST":
        
        # Create lists of empty shifts to be filled
        cover_1_openings = []
        cover_2_openings = []

        # Loop through each cover day
        day = 1
        while day <= 2:

            # 
            covered_shift = "cover_" + str(day) + "_firefighters"
            counter = 1

            # Loop through each firefighter (or vacancy)
            for firefighter in session[covered_shift]:
                
                # Create form identifier
                if day == 1:
                    place = "1st_"
                elif day == 2:
                    place = "2nd_"
                
                identifier = place + "day_" + str(counter)

                # Get firefighter's status from html
                availability = request.form.get(identifier)

                # Add open shift to list of shifts to be filled:
                print(firefighter)
                if not firefighter.username:
                    print("vacancy")
                elif availability != "Available":

                    open_shift = {
                        'day': day,
                        'username': firefighter.username,
                        'shift': availability
                    }
                    print(open_shift)
#         ^ ^ ^ ^ CONTINUE WORK HERE ^ ^ ^ ^ 
                # Add to counter for next firefighter
                counter += 1

            # Add to counter for next cover day
            day += 1



        
        return redirect("/hired")

    # Display the covered shifts form
    else:
        # Get cover platoons
        if session['platoon'] == '1':
            cover_1 = 4
            cover_2 = 2
        elif session['platoon'] == '2':
            cover_1 = 1
            cover_2 = 3
        elif session['platoon'] == '3':
            cover_1 = 2
            cover_2 = 4
        elif session['platoon'] == '4':
            cover_1 = 3
            cover_2 = 1
        
        days_covered = {'day_1': cover_1, 'day_2': cover_2}

        # Get firefighters list for each cover platoon
        cover_1_firefighters = db.execute(select(User.username).where(User.platoon == cover_1).where(User.active == '1').order_by(User.id))
        cover_1_firefighters = cover_1_firefighters.mappings().all()

        cover_2_firefighters = db.execute(select(User.username, User.active).where(User.platoon == cover_2).where(User.active == '1').order_by(User.id))
        cover_2_firefighters = cover_2_firefighters.mappings().all()

        # Add vacancies to shifts up to full-size
        while len(cover_1_firefighters) < PLATOON_FIREFIGHTERS:
            cover_1_firefighters.append({'username': 'vacancy'})
        session['cover_1_firefighters'] = cover_1_firefighters

        while len(cover_2_firefighters) < PLATOON_FIREFIGHTERS:
            cover_2_firefighters.append({'username': 'vacancy'})
        session['cover_2_firefighters'] = cover_2_firefighters

        print(f"Cover 1: {session['cover_1_firefighters']}")
        print(f"Cover 2: {session['cover_2_firefighters']}")
        return render_template("hiring_c.html", days_covered=days_covered, platoon=session['platoon'])


"""Hire for shifts, return hiring list"""
@app.route("/hired", methods=["GET", "POST"])
@login_required
def hired():
    
    # 
    if request.method == "POST":
        return render_template("hired.html")

    # Display completed hiring
    if request.method == "GET":
        return render_template("hired.html")


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
        rank = request.form.get("rank")
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
        db.execute(insert(User), {"username": username, "hash": hashword, "rank": rank, "platoon": platoon, "active": active, "elligible": elligibility})
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