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
# Select which platoon is covering OT
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


# Select any members that are not available on cover days
@app.route("/hiring_b", methods=["GET", "POST"])
@login_required
def hiring_b():

    # After availability is submitted
    if request.method == "POST":

        # Create lists & variables outside of loops
        officers_availability = []
        officers_hours = []
        firefighters_availability = []
        firefighters_hours = []

        #Loop through each rank - Officer and Firefighter
        tier = 1
        for rank in session['personnel']:

            # Loop through each person at that rank
            person_counter = 1
            for person in rank:
                
                # Create html tag id and collect this firefighter's availability
                day_1 = "day_1_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)
                ntw_1 = "ntw_1_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)
                day_2 = "day_2_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)
                ntw_2 = "ntw_2_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)

                results_avail = {
                    'username': person['username'],
                    'avail_1': request.form.get(day_1),
                    'dept_business_1': request.form.get(ntw_1),
                    'avail_2': request.form.get(day_2),
                    'dept_business_2': request.form.get(ntw_2)
                }

                # Add results to firefighters list
                if tier == 1:
                    officers_availability.append(results_avail)
                elif tier  == 2:
                    firefighters_availability.append(results_avail)

                # Handle hours unavailability
                # Loop through each day
                day = 1
                while day <= DAYS_COVERED:

                    # Create the tag to check for hours with
                    avail_tag = 'avail_' + str(day)

                    # If person is out Hours
                    if results_avail[avail_tag] == "hours":

                        # Create html tag id's
                        start_id = "hours_" + str(day) + "_" + session['hiring_tiers'][tier - 1]['tier'] + "_start_" + str(person_counter)
                        end_id = "hours_" + str(day) + "_" + session['hiring_tiers'][tier - 1]['tier'] + "_end_" + str(person_counter)

                        # Get start and end hours, and save in dict
                        results_hours = {
                            'day': day,
                            'username': person['username'],
                            'hours_start': request.form.get(start_id),
                            'hours_end': request.form.get(end_id)
                        }

                        # Add results to appropriate hours list
                        if tier == 1:
                            officers_hours.append(results_hours)

                        elif tier == 2:
                            firefighters_hours.append(results_hours)

                    day += 1

                person_counter += 1

            tier += 1

        # Save all availability in session
        session['officers_avail'] = officers_availability
        session['officers_hours'] = officers_hours
        session['firefighters_avail'] = firefighters_availability
        session['firefighters_hours'] = firefighters_hours

        print(f"officers avail: {officers_availability}")
        print(f"officers hours: {officers_hours}")
        print(f"firefighters avail: {firefighters_availability}")
        print(f"firefighters hours: {firefighters_hours}")

        return redirect("/hiring_c")

    # Display the availability form
    else:

        # query db for list of elligible officers & firefighters and save as dicts
        officers = db.execute(select(User.id, User.username, User.rank).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank != "firefighter").order_by(User.id))
        officers = officers.mappings().all()

        firefighters = db.execute(select(User.id, User.username, User.rank).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank == "firefighter").order_by(User.id))
        firefighters = firefighters.mappings().all()

        session['personnel'] = [officers, firefighters]

        # Create list of titles for HTML
        session['cover_days'] = [{"day": "First Cover Day"}, {"day": "Second Cover Day"}]
        session['hiring_tiers'] = [{"tier": "Officers"}, {"tier": "Firefighters"}]

        return render_template("hiring_b.html", cover_days=session['cover_days'], days_covered=DAYS_COVERED, firefighters=session['personnel'], hiring_tiers=session['hiring_tiers'], platoon=session['platoon'])


# Load the two platoons to be covered for; select which members are out
@app.route("/hiring_c", methods=["GET", "POST"])
@login_required
def hiring_c():

    # Save form input from GET route (shifts to be filled)
    if request.method == "POST":
        
        # Create lists of empty shifts & hours to be filled
        session['ff_openings_1'] = []
        session['ff_hours_1'] = []
        session['ff_openings_2'] = []
        session['ff_hours_2'] = []
        session['officer_openings_1'] = []
        session['officer_hours_1'] = []
        session['officer_openings_2'] = []
        session['officer_hours_2'] = []

        # Get openings for shifts in order:
        # 1st cover day officers:
        counter_officer_1 = 1

        # Loop through each officer and get status
        for officer in session['cover_1_officers']:
            form_id = "officer_1st_day_" + str(counter_officer_1)
            result = request.form.get(form_id)

            # If officer is not working a 24, save their status
            if result != "working":
                session['officer_openings_1'].append({
                    'username': officer['username'],
                    'availability': result
                })

                # If officer is out hours, save the hours in a separate list
                if result == "hours":
                    start_id = "officer_hours_1_start_" + str(counter_officer_1)
                    end_id = "officer_hours_1_end_" + str(counter_officer_1)
                    session['officer_hours_1'].append({
                        'username': officer['username'],
                        'start': request.form.get(start_id),
                        'end': request.form.get(end_id)
                    })

            counter_officer_1 += 1

        # Loop through each firefighter and get status
        counter_firefighter_1 = 1
        for firefighter in session['cover_1_firefighters']:
            form_id = "ff_1st_day_" + str(counter_firefighter_1)
            result = request.form.get(form_id)

            # If ff is not working a 24, save their status
            if result != "working":
                session['ff_openings_1'].append({
                    'username': firefighter['username'],
                    'availability': result
                })

                # If ff is out hours, save the hours in a separate list
                if result == "hours":
                    start_id = "ff_hours_1_start_" + str(counter_firefighter_1)
                    end_id = "ff_hours_1_end_" + str(counter_firefighter_1)
                    session['ff_hours_1'].append({
                        'username': firefighter['username'],
                        'start': request.form.get(start_id),
                        'end': request.form.get(end_id)
                    })

            counter_firefighter_1 += 1

        # Loop through each officer and get status
        counter_officer_2 = 1
        for officer in session['cover_2_officers']:
            form_id = "officer_2nd_day_" + str(counter_officer_2)
            result = request.form.get(form_id)

            # If officer is not working a 24, save their status
            if result != "working":
                session['officer_openings_2'].append({
                    'username': officer['username'],
                    'availability': result
                })

                # If officer is out hours, save the hours in a separate list
                if result == "hours":
                    start_id = "officer_hours_2_start_" + str(counter_officer_2)
                    end_id = "officer_hours_2_end_" + str(counter_officer_2)
                    session['officer_hours_2'].append({
                        'username': officer['username'],
                        'start': request.form.get(start_id),
                        'end': request.form.get(end_id)
                    })

            counter_officer_2 += 1

        # Loop through each firefighter and get status
        counter_firefighter_2 = 1
        for firefighter in session['cover_2_firefighters']:
            form_id = "ff_2nd_day_" + str(counter_firefighter_2)
            result = request.form.get(form_id)

            # If ff is not working a 24, save their status
            if result != "working":
                session['ff_openings_2'].append({
                    'username': firefighter['username'],
                    'availability': result
                })

                # If ff is out hours, save the hours in a separate list
                if result == "hours":
                    start_id = "ff_hours_2_start_" + str(counter_firefighter_2)
                    end_id = "ff_hours_2_end_" + str(counter_firefighter_2)
                    session['ff_hours_2'].append({
                        'username': firefighter['username'],
                        'start': request.form.get(start_id),
                        'end': request.form.get(end_id)
                    })

            counter_firefighter_2 += 1
        
        print(f"Officer 1: {session['officer_openings_1']}")
        print(f"FF 1: {session['ff_openings_1']}")
        print(f"Officer 2: {session['officer_openings_2']}")
        print(f"FF 2: {session['ff_openings_2']}")

        print(f"Officer 1: {session['officer_hours_1']}")
        print(f"FF 1: {session['ff_hours_1']}")
        print(f"Officer 2: {session['officer_hours_2']}")
        print(f"FF 2: {session['ff_hours_2']}")
    
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

        # Get officers & firefighters list for each cover platoon
        cover_1_firefighters = db.execute(select(User.username).where(User.platoon == cover_1).where(User.active == '1').where(User.rank == "firefighter").order_by(User.id))
        cover_1_firefighters = cover_1_firefighters.mappings().all()

        cover_1_officers = db.execute(select(User.username).where(User.platoon == cover_1).where(User.active == '1').where(User.rank != "firefighter").order_by(User.id))
        cover_1_officers = cover_1_officers.mappings().all()

        cover_2_firefighters = db.execute(select(User.username).where(User.platoon == cover_2).where(User.active == '1').where(User.rank == "firefighter").order_by(User.id))
        cover_2_firefighters = cover_2_firefighters.mappings().all()

        cover_2_officers = db.execute(select(User.username).where(User.platoon == cover_2).where(User.active == '1').where(User.rank != "firefighter").order_by(User.id))
        cover_2_officers = cover_2_officers.mappings().all()


        # Add vacancies to shifts up to full-size
        while len(cover_1_firefighters) < PLATOON_FIREFIGHTERS:
            cover_1_firefighters.append({'username': 'vacancy'})
        session['cover_1_firefighters'] = cover_1_firefighters

        while len(cover_1_officers) < PLATOON_OFFICERS:
            cover_1_officers.append({'username': 'vacancy'})
        session['cover_1_officers'] = cover_1_officers

        while len(cover_2_firefighters) < PLATOON_FIREFIGHTERS:
            cover_2_firefighters.append({'username': 'vacancy'})
        session['cover_2_firefighters'] = cover_2_firefighters

        while len(cover_2_officers) < PLATOON_OFFICERS:
            cover_2_officers.append({'username': 'vacancy'})
        session['cover_2_officers'] = cover_2_officers

        print(f"Cover 1: {session['cover_1_firefighters']}")
        print(f"Cover 2: {session['cover_2_firefighters']}")
        print(f"Cover 1: {session['cover_1_officers']}")
        print(f"Cover 2: {session['cover_2_officers']}")

        return render_template("hiring_c.html", cover_1_firefighters=cover_1_firefighters, cover_1_officers=cover_1_officers, cover_2_firefighters=cover_2_firefighters, cover_2_officers=cover_2_officers, days_covered=days_covered, platoon=session['platoon'])


"""Hire for shifts, return hiring list"""
@app.route("/hired", methods=["GET", "POST"])
@login_required
def hired():
    
    # Save approved hiring in db and print results
    if request.method == "POST":
        return render_template("hired.html")

    # Assign shifts & Display completed hiring
    else request.method == "GET":
        # For each cover day
        # For officers and firefighters
        # Iterate over each opening
        # Assign NTW or next up person to open shift & flip tags
            # If next up person is unavailable because of dept business, assign NTW
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