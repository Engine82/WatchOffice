from datetime import datetime, date, timedelta
from operator import itemgetter
from sqlalchemy import create_engine, insert, select, update
from sqlalchemy.orm import sessionmaker
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

# https://pydoc.dev/werkzeug/latest/werkzeug.security.html
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required
from helpers import Base, User, Ntw
from helpers import find_next_up, hire


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
        firefighters_availability = []

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
                    'avail_2': request.form.get(day_2),
                    'tag_flipped': session['personnel'][tier - 1][person_counter - 1]['tag_flipped']
                }
                # Add results to firefighters list
                if tier == 1:
                    officers_availability.append(results_avail)
                elif tier  == 2:
                    firefighters_availability.append(results_avail)

                person_counter += 1

            tier += 1

        # Save all availability in session
        session['officers_avail'] = officers_availability
        session['firefighters_avail'] = firefighters_availability

        return redirect("/hiring_c")

    # Display the availability form
    else:

        # query db for list of elligible officers & firefighters and save as dicts
        officers = db.execute(select(User.id, User.username, User.rank, User.tag_flipped).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank != "firefighter").order_by(User.id))
        officers = officers.mappings().all()

        firefighters = db.execute(select(User.id, User.username, User.rank, User.tag_flipped).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank == "firefighter").order_by(User.id))
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
        session['firefighters_openings_1'] = []
        session['firefighters_openings_2'] = []
        session['officers_openings_1'] = []
        session['officers_openings_2'] = []

        # Get openings for shifts in order:
        # 1st cover day officers:
        counter_officer_1 = 1

        # Loop through each officer and get status - Day 1
        for officer in session['cover_1_officers']:
            form_id = "officers_1st_day_" + str(counter_officer_1)
            result = request.form.get(form_id)

            # If officer is not working a 24, save their status
            if result != "working":
                session['officers_openings_1'].append({
                    'username': officer['username'],
                    'availability': result
                })

            counter_officer_1 += 1

        # Loop through each firefighter and get status - Day 1
        counter_firefighter_1 = 1
        for firefighter in session['cover_1_firefighters']:
            form_id = "firefighters_1st_day_" + str(counter_firefighter_1)
            result = request.form.get(form_id)

            # If ff is not working a 24, save their status
            if result != "working":
                session['firefighters_openings_1'].append({
                    'username': firefighter['username'],
                    'availability': result
                })

            counter_firefighter_1 += 1

        # Loop through each officer and get status - Day 2
        counter_officer_2 = 1
        for officer in session['cover_2_officers']:
            form_id = "officers_2nd_day_" + str(counter_officer_2)
            result = request.form.get(form_id)

            # If officer is not working a 24, save their status
            if result != "working":
                session['officers_openings_2'].append({
                    'username': officer['username'],
                    'availability': result
                })

            counter_officer_2 += 1

        # Loop through each firefighter and get status - Day 2
        counter_firefighter_2 = 1
        for firefighter in session['cover_2_firefighters']:
            form_id = "firefighters_2nd_day_" + str(counter_firefighter_2)
            result = request.form.get(form_id)

            # If ff is not working a 24, save their status
            if result != "working":
                session['firefighters_openings_2'].append({
                    'username': firefighter['username'],
                    'availability': result
                })

            counter_firefighter_2 += 1
    
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

        return render_template("hiring_c.html", cover_1_firefighters=cover_1_firefighters, cover_1_officers=cover_1_officers, cover_2_firefighters=cover_2_firefighters, cover_2_officers=cover_2_officers, days_covered=days_covered, platoon=session['platoon'])


"""Hire for shifts, return hiring list"""
@app.route("/hired", methods=["GET", "POST"])
@login_required
def hired():
    
    # POST: Save approved hiring in db and print results
    if request.method == "POST":
    # {'username': kyle, 'tag_flipped': 0}

        # Go through each rank
        for index, rank in enumerate(session['hiring_tiers']):
            rnk = rank['tier'].lower()

            # Go through each member in taglist at that rank
            for member in session[rnk + '_tags']:
                
                # If this member isn't next up, their tag is flipped
                if member['tag_flipped'] == 1:
                    db.execute(
                        update(User)
                        .where(User.username == member['username'])
                        .values(tag_flipped=1)
                    )

                # Otherwise, their tag is not flipped
                else:
                    db.execute(
                        update(User)
                        .where(User.username == member['username'])
                        .values(tag_flipped=0)
                    )
                    
        # Commit all updates to db
        db.commit()
        return redirect("/")

    # GET: Assign shifts & Display completed hiring
    else:
        # Break hiring lists down into day/night
        # Create lists for covered shifts
        session['officers_covered_day_1'] = []
        session['officers_covered_night_1'] = []
        session['officers_covered_day_2'] = []
        session['officers_covered_night_2'] = []
        session['firefighters_covered_day_1'] = []
        session['firefighters_covered_night_1'] = []
        session['firefighters_covered_day_2'] = []
        session['firefighters_covered_night_2'] = []

        # Create lists for availability
        session['officers_covering_1'] = []
        session['officers_covering_2'] = []
        session['firefighters_covering_1'] = []
        session['firefighters_covering_2'] = []

        # Create lists for completed hiring
        session['officers_hired_day_1'] = []
        session['officers_hired_night_1'] = []
        session['officers_hired_day_2'] = []
        session['officers_hired_night_2'] = []
        session['firefighters_hired_day_1'] = []
        session['firefighters_hired_night_1'] = []
        session['firefighters_hired_day_2'] = []
        session['firefighters_hired_night_2'] = []
        
        # Create lists for covering tag status
        session['officers_tags'] = []
        session['firefighters_tags'] = []

        # Create list for hiring results
        session['results'] = []

        # Create list for who's up next
        session['up_next'] = []

        day_night = ["day_", "night_"]
        daynight = ['day', 'night']


        """ OPEN SHIFTS """
        # Break down each shift opening into it's appropriate list
        # Iterate through each rank
        for rank in session['hiring_tiers']:

            # Iterate through each day
            day = 1
            while day <= DAYS_COVERED:

                # Iterate through each opening
                rank_lower = rank['tier'].lower()
                for opening in session[rank_lower + "_openings_" + str(day)]:

                    # Get this open shift's info
                    shift_day = {'username': opening['username'], 'shift': 'day'}
                    shift_night = {'username': opening['username'], 'shift': 'night'}

                    # Day
                    if opening['availability'] == 'day':
                        session[rank_lower + "_covered_day_" + str(day)].append(shift_day)

                    # Night
                    elif opening['availability'] == 'night':
                        session[rank_lower + "_covered_night_" + str(day)].append(shift_night)

                    # 24
                    elif opening['availability'] == '24':
                        session[rank_lower + "_covered_day_" + str(day)].append(shift_day)
                        session[rank_lower + "_covered_night_" + str(day)].append(shift_night)
                    
                day += 1

        """ AVAILABILITY """
        # Break down each covering member's availability into it's appropriate list
        # Iterate through each rank
        for rank in session['hiring_tiers']:

            # Iterate through each day
            day = 1
            while day <= 2:

                # Iterate through each opening
                rank_lower = rank['tier'].lower()
                member_counter = 0
                for member in session[rank_lower + "_avail"]:

                    # 24
                    if member['avail_' + str(day)] == '24':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'username': member['username'], 
                            'day': 'unavailable',
                            'night': 'unavailable'
                        })

                    # Unavailable Day
                    elif member['avail_' + str(day)] == 'day':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'username': member['username'], 
                            'day': 'unavailable',
                            'night': 'available'
                        })

                    # Unavailable Night
                    elif member['avail_' + str(day)] == 'night':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'username': member['username'], 
                            'day': 'available',
                            'night': 'unavailable'
                        })
                    
                    # Available
                    elif member['avail_' + str(day)] == 'available':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'username': member['username'],
                            'day': 'available',
                            'night': 'available'
                        })
                    
                    member_counter += 1
                
                day += 1

        """ TAG STATUS """
        # Create list with tag status of covering members
        for rank in session['hiring_tiers']:
            rnk = rank['tier'].lower()
            counter = 0
            for member in session[rnk + "_avail"]:
                session[rnk + "_tags"].append({
                    'username': member['username'],
                    'tag_flipped': session[rnk + "_avail"][counter]['tag_flipped']
                })
                counter += 1


        """ HIRE """
        # Loop through each day/rank/time/opening from above, and fill each opening with next available person or from 96-off

        # DAY - Iterate through each day
        day = 1
        while day <= DAYS_COVERED:

            # RANK - Iterate through each rank: [{"tier": "Officers"}, {"tier": "Firefighters"}]
            for rank in session['hiring_tiers']:
                
                # create lowercase rank name for use in variables, get number of people on covering shift for future use
                rnk = rank['tier'].lower()
                shift_size = len(session[rnk + "_covering_" + str(day)])

                # TIME - Iterate through time (day/night):
                for time in daynight:
                    
                    # Zero covering person counter
                    session['covering_count'] = 0

                    # Iterate through each opening
                    for opening in session[rnk + "_covered_" + time + "_" + str(day)]:
                        
                        # Hire for this opening using hiring function in helpers.py
                        result = hire(
                                opening,
                                session[rnk + "_covering_" + str(day)],
                                session[rnk + '_tags'],
                                session['results'],
                                time,
                                session['covering_count'],
                                shift_size
                            )

                        # Add hiring results to the results dict
                        session[rnk + "_hired_" + time + "_" + str(day)].extend(result[0])

                        # Increase counter for number of covering members checked (hired or unavailable)
                        session['covering_count'] = result[1]

            day += 1

        # Save next-up officer & firefighter and update taglist in db
        for rank in session['hiring_tiers']:
            rnk = rank['tier'].lower()
            
            # Save next up members
            session['up_next'].append({
                'rank': rnk,
                'up_next': find_next_up(session[rnk + '_tags'])
            })

        # Display hired form with hiring results
        return render_template("hired.html", 
            officers_day_1=session['officers_hired_day_1'],
            officers_night_1=session['officers_hired_night_1'],
            officers_day_2=session['officers_hired_day_2'],
            officers_night_2=session['officers_hired_night_2'],
            firefighters_day_1=session['firefighters_hired_day_1'],
            firefighters_night_1=session['firefighters_hired_night_1'],
            firefighters_day_2=session['firefighters_hired_day_2'],
            firefighters_night_2=session['firefighters_hired_night_2'],
            up_next=session['up_next'],
            platoon=session['platoon'])    


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