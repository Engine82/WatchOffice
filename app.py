from datetime import datetime, date, timedelta
from operator import itemgetter
from sqlalchemy import create_engine, insert, select, text, update
from sqlalchemy.orm import sessionmaker
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

# https://pydoc.dev/werkzeug/latest/werkzeug.security.html
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required
from helpers import Base, User, Hiring, Hiring_list
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
hiring_tiers = [{"tier": "Officers"}, {"tier": "Firefighters"}]

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
                    'id': person['id'],
                    'first_name': person['first_name'],
                    'last_name': person['last_name'],
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
        officers = db.execute(select(User.id, User.first_name, User.last_name, User.rank, User.tag_flipped).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank != "firefighter").order_by(User.id))
        officers = officers.mappings().all()

        firefighters = db.execute(select(User.id, User.first_name, User.last_name, User.rank, User.tag_flipped).where(User.platoon == session['platoon']).where(User.elligible == "1").where(User.active == "1").where(User.rank == "firefighter").order_by(User.id))
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
                    'id': officer['id'],
                    'first_name': officer['first_name'],
                    'last_name': officer['last_name'],
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
                    'id': firefighter['id'],
                    'first_name': firefighter['first_name'],
                    'last_name': firefighter['last_name'],
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
                    'id': officer['id'],
                    'first_name': officer['first_name'],
                    'last_name': officer['last_name'],
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
                print("firefighter: ", firefighter)
                session['firefighters_openings_2'].append({
                    'id': firefighter['id'],
                    'first_name': firefighter['first_name'],
                    'last_name': firefighter['last_name'],
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
        cover_1_firefighters = db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.platoon == cover_1)
            .where(User.active == '1')
            .where(User.rank == "firefighter")
            .order_by(User.id)
        )
        cover_1_firefighters = cover_1_firefighters.mappings().all()

        cover_1_officers = db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.platoon == cover_1)
            .where(User.active == '1')
            .where(User.rank != "firefighter")
            .order_by(User.id)
        )
        cover_1_officers = cover_1_officers.mappings().all()

        cover_2_firefighters = db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.platoon == cover_2)
            .where(User.active == '1')
            .where(User.rank == "firefighter")
            .order_by(User.id)
        )
        cover_2_firefighters = cover_2_firefighters.mappings().all()

        cover_2_officers = db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.platoon == cover_2)
            .where(User.active == '1')
            .where(User.rank != "firefighter")
            .order_by(User.id)
        )
        cover_2_officers = cover_2_officers.mappings().all()


        # Add vacancies to shifts up to full-size
        while len(cover_1_firefighters) < PLATOON_FIREFIGHTERS:
            cover_1_firefighters.append({'id': '0', 'first_name': 'vacancy', 'last_name': " "})
        session['cover_1_firefighters'] = cover_1_firefighters

        while len(cover_1_officers) < PLATOON_OFFICERS:
            cover_1_officers.append({'id': '0', 'first_name': 'vacancy', 'last_name': " "})
        session['cover_1_officers'] = cover_1_officers

        while len(cover_2_firefighters) < PLATOON_FIREFIGHTERS:
            cover_2_firefighters.append({'id': '0', 'first_name': 'vacancy', 'last_name': " "})
        session['cover_2_firefighters'] = cover_2_firefighters

        while len(cover_2_officers) < PLATOON_OFFICERS:
            cover_2_officers.append({'id': '0', 'first_name': 'vacancy', 'last_name': " "})
        session['cover_2_officers'] = cover_2_officers

        return render_template("hiring_c.html", cover_1_firefighters=cover_1_firefighters, cover_1_officers=cover_1_officers, cover_2_firefighters=cover_2_firefighters, cover_2_officers=cover_2_officers, days_covered=days_covered, platoon=session['platoon'])


"""Hire for shifts, return hiring list"""
@app.route("/hired", methods=["GET", "POST"])
@login_required
def hired():
    
    # POST: Save approved hiring in db and print results
    if request.method == "POST":

        ''' UPDATE TAGS IN DB '''
        # Go through each rank
        for index, rank in enumerate(session['hiring_tiers']):
            rnk = rank['tier'].lower()

            # Go through each member in taglist at that rank
            for member in session[rnk + '_tags']:
                
                # If this member isn't next up, their tag is flipped
                if member['tag_flipped'] == 1:
                    db.execute(
                        update(User)
                        .where(User.username == member['id'])
                        .values(tag_flipped=1)
                    )

                # Otherwise, their tag is not flipped
                else:
                    db.execute(
                        update(User)
                        .where(User.username == member['id'])
                        .values(tag_flipped=0)
                    )
                    
        # Commit all updates to db
        db.commit()

        ''' SAVE RESULTS IN DB '''
        # Create list of hiring lists:
        hiring_lists = [
            'officers_hired_day_1', 
            'officers_hired_night_1',
            'officers_hired_day_2',
            'officers_hired_night_2',
            'firefighters_hired_day_1',
            'firefighters_hired_night_1',
            'firefighters_hired_day_2',
            'firefighters_hired_night_2'
        ]

        # Get hiring id and increase by one
        try:
            hiring_id = db.execute(select(Hiring.hiring_id).order_by(Hiring.hiring_id.desc()).limit(1))
            hiring_id = hiring_id.mappings().all()
            hiring_id = hiring_id[0]['hiring_id']
            hiring_id += 1

        # Handle the first iteration of hiring
        except:
            hiring_id = 0


        # Iterate through each hiring entry and save it in db, or if no hiring, save that
        daynight = ['day', 'night']

        # Iterate through each day
        day = 1
        while day <= DAYS_COVERED:

            for rank in session['hiring_tiers']:

                # Iterate through each opening
                rank_lower = rank['tier'].lower()
                for time in daynight:

                    # If hiring at this day/rank/time has been done
                    if session[rank_lower + "_hired_" + time + "_" + str(day)] != []:
                        for shift in session[rank_lower + "_hired_" + time + "_" + str(day)]:
                            db.execute(
                                text("INSERT INTO hiring (hiring_id, platoon, rank, day, time, member_out, member_covering) VALUES (:hiring_id, :platoon, :rank, :day, :time, :member_out, :member_covering)"),
                                [{
                                    "hiring_id": hiring_id,
                                    "platoon": session['platoon'],
                                    "rank": rank['tier'],
                                    "day": day,
                                    "time": time,
                                    "member_out": shift['person_off'],
                                    "member_covering": shift['person_covering']
                                }]
                            )
                            db.commit()

                    # if no hiring at this day/rank/time
                    else:
                        db.execute(
                            text("INSERT INTO hiring (hiring_id, platoon, rank, day, time, member_out, member_covering) VALUES (:hiring_id, :platoon, :rank, :day, :time, :member_out, :member_covering)"),
                            [{
                                "hiring_id": hiring_id,
                                "platoon": session['platoon'],
                                "rank": rank['tier'],
                                "day": day,
                                "time": time,
                                "member_out": "none",
                                "member_covering": "none"
                            }]
                        )
                        db.commit()


            day += 1
        
        # Save this hiring id in list of hirings
        time = db.execute(
                    select(Hiring.created_at)
                    .where(Hiring.hiring_id == hiring_id)
                )
        time = time.mappings().all()
        time = time[0]['created_at']

        db.execute(
            text("INSERT INTO hiring_list (hiring_id, created_at) VALUES (:hiring_id, :created_at)"), [{"hiring_id": hiring_id, "created_at": time}]
        )
        db.commit()

        ''' PRINT OPTIONS ?????? '''

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
                    shift_day = {
                        'id': opening['id'],
                        'name': opening['first_name'] + " " + opening['last_name'],
                        'shift': 'day'
                    }
                    shift_night = {
                        'id': opening['id'],
                        'name': opening['first_name'] + " " + opening['last_name'],
                        'shift': 'night'
                    }
                    print("shift night: ", shift_night)

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
                            'id': member['id'],
                            'first_name': member['first_name'],
                            'last_name': member['last_name'],
                            'day': 'unavailable',
                            'night': 'unavailable'
                        })

                    # Unavailable Day
                    elif member['avail_' + str(day)] == 'day':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'id': member['id'],
                            'first_name': member['first_name'],
                            'last_name': member['last_name'],
                            'day': 'unavailable',
                            'night': 'available'
                        })

                    # Unavailable Night
                    elif member['avail_' + str(day)] == 'night':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'id': member['id'], 
                            'first_name': member['first_name'],
                            'last_name': member['last_name'],
                            'day': 'available',
                            'night': 'unavailable'
                        })
                    
                    # Available
                    elif member['avail_' + str(day)] == 'available':
                        session[rank_lower + "_covering_" + str(day)].append({
                            'id': member['id'],
                            'first_name': member['first_name'],
                            'last_name': member['last_name'],
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
                    'id': member['id'],
                    'name': member['first_name'] + " " + member['last_name'],
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
                                shift_size,
                                day,
                                rnk
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


# Manual hiring input
@app.route("/manual_a", methods=["GET", "POST"])
@login_required
def manual_a():
    
    # After platoon is selected
    if request.method == "POST":

        # Save platoon choice for next route
        session["platoon"] = request.form.get("platoon")
        return redirect("/manual_b")

    # If starting new hiring
    else:
        return render_template("manual_a.html")


# Select any members that are not available on cover days
@app.route("/manual_b", methods=["GET", "POST"])
@login_required
def manual_b():

    # After availability is submitted
    if request.method == "POST":
        
        # Get user input:
        officer = request.form.get("officer")
        firefighter = request.form.get("firefighter")
        ids = [
            {"rank": "officer", "id": officer},
            {"rank": "firefighter", "id": firefighter}
        ]
        print(ids)

        # Update tag_flipped status in db:
        for entry in ids:
            for member in session['covering_' + entry['rank']]:
                if member['id'] < int(entry['id']):
                    db.execute(
                        update(User)
                        .where(User.id == member['id'])
                        .values(tag_flipped=1)
                    )

                # Required if the previous person up was lower in seniority than the new person up
                else:
                    db.execute(
                        update(User)
                        .where(User.id == member['id'])
                        .values(tag_flipped=0)
                    )
        db.commit()

        # Get hiring id and increase by one
        try:
            hiring_id = db.execute(select(Hiring.hiring_id).order_by(Hiring.hiring_id.desc()).limit(1))
            hiring_id = hiring_id.mappings().all()
            hiring_id = hiring_id[0]['hiring_id']
            hiring_id += 1

        # Handle the first iteration of hiring
        except:
            hiring_id = 0
        
        # Record manual override in hiring and hiring_list db's
        daynight = ['day', 'night']

        for day in range(DAYS_COVERED):
            for rank in session['hiring_tiers']:
                for time in daynight:
                    db.execute(
                        text("INSERT INTO hiring (hiring_id, platoon, rank, day, time, member_out, member_covering) VALUES (:hiring_id, :platoon, :rank, :day, :time, :member_out, :member_covering)"),
                        [{
                            "hiring_id": hiring_id,
                            "platoon": session['platoon'],
                            "rank": rank['tier'],
                            "day": day,
                            "time": time,
                            "member_out": "manual override",
                            "member_covering": "manual override"
                        }]
                    )
        db.commit()

        # Record this "hiring" in hiring_list
        time = db.execute(
                    select(Hiring.created_at)
                    .where(Hiring.hiring_id == hiring_id)
                )
        time = time.mappings().all()
        time = time[0]['created_at']

        db.execute(
            text("INSERT INTO hiring_list (hiring_id, created_at) VALUES (:hiring_id, :created_at)"),
            [{"hiring_id": hiring_id, "created_at": time}]
        )
        db.commit()

        return redirect("/")

    # Display the availability form
    else:

        # query db for list of elligible officers & firefighters and save as dicts
        covering_officers = db.execute(
            select(User.id, User.username)
            .where(User.platoon == session['platoon'])
            .where(User.elligible == "1")
            .where(User.active == "1")
            .where(User.rank != "firefighter")
            .order_by(User.id)
        )
        session['covering_officer'] = covering_officers.mappings().all()
        print("covering officer:", session['covering_officer'])

        covering_firefighters = db.execute(
            select(User.id, User.username, User.rank)
            .where(User.platoon == session['platoon'])
            .where(User.elligible == "1")
            .where(User.active == "1")
            .where(User.rank == "firefighter")
            .order_by(User.id)
        )
        session['covering_firefighter'] = covering_firefighters.mappings().all()
        print("covering firefighter:", session['covering_firefighter'])

        return render_template(
            "manual_b.html",
            officers=session['covering_officer'],
            firefighters=session['covering_firefighter'],
            platoon=session['platoon']
        )


# History
@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    
    # POST get and display chosen past hiring:
    if request.method == "POST":

        # Create empty past hiring lists
        session['officers_past_hiring_day_1'] = []
        session['officers_past_hiring_night_1'] = []
        session['officers_past_hiring_day_2'] = []
        session['officers_past_hiring_night_2'] = []
        session['firefighters_past_hiring_day_1'] = []
        session['firefighters_past_hiring_night_1'] = []
        session['firefighters_past_hiring_day_2'] = []
        session['firefighters_past_hiring_night_2'] = []

        # query db for all entries with this id at each day/rank/time, save in list
        past_id = request.form.get("past_hiring")

        past_platoon = db.execute(select(Hiring.platoon).where(Hiring.hiring_id == past_id))
        past_platoon = past_platoon.scalars().all()
        past_platoon = past_platoon[0]

        # Loop through day/rank/time
        daynight = ["day", "night"]
        day = 1
        while day <= DAYS_COVERED:

            for rank in hiring_tiers:
                rnk = rank['tier'].lower()

                for time in daynight:

                    # Query db for hiring at this day/rank/time and save in session
                    past_hiring = db.execute(
                        select(Hiring.rank, Hiring.day, Hiring.time, Hiring.member_out, Hiring.member_covering)
                        .where(Hiring.hiring_id == past_id)
                        .where(Hiring.day == day)
                        .where(Hiring.rank == rank['tier'])
                        .where(Hiring.time == time)
                    )
                    past_hiring = past_hiring.mappings().all()
                    session[rnk + "_" + "past_hiring" + "_" + time + "_" + str(day)].extend(past_hiring)
                    
            day += 1
        
        print(
            "officers day 1:", session['officers_past_hiring_day_1'],
            "officers night 1:", session['officers_past_hiring_night_1'],
            "officers day 2", session['officers_past_hiring_day_2'],
            "officers night 2:", session['officers_past_hiring_night_2'],
            "firefighters day 1", session['firefighters_past_hiring_day_1'],
            "firefighters night 1:", session['firefighters_past_hiring_night_1'],
            "firefighters day 2:", session['firefighters_past_hiring_day_2'],
            "firefighters night 2:", session['firefighters_past_hiring_night_2']
        )

        # display hiring results a la hired.html
        return render_template("history_found.html", 
            officers_day_1=session['officers_past_hiring_day_1'],
            officers_night_1=session['officers_past_hiring_night_1'],
            officers_day_2=session['officers_past_hiring_day_2'],
            officers_night_2=session['officers_past_hiring_night_2'],
            firefighters_day_1=session['firefighters_past_hiring_day_1'],
            firefighters_night_1=session['firefighters_past_hiring_night_1'],
            firefighters_day_2=session['firefighters_past_hiring_day_2'],
            firefighters_night_2=session['firefighters_past_hiring_night_2'],
            platoon=past_platoon
        )

    # GET get list of past hiring and feed to html select
    else:

        # query db for hiring id's
        hiring_list = db.execute(
            select(Hiring_list.hiring_id, Hiring_list.created_at).order_by(Hiring_list.hiring_id.desc())
        )
        hiring_list = hiring_list.mappings().all()

        # feed list of dates & id's to html, where user selects one
        return render_template("history.html", hiring_list=hiring_list)



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
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
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
        db.execute(
            insert(User),
            {
                "username": username, 
                "first_name": first_name,
                "last_name": last_name,
                "hash": hashword,
                "rank": rank,
                "platoon": platoon,
                "active": active,
                "elligible": elligibility
            }
        )
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

        # Get member to be removed from html form        
        member = request.form.get("member")
        
        # Update db: platoon = n/a, active = 0
        db.execute(
            update(User)
            .where(User.username == member)
            .values(active=0, platoon=None)
        )

        # Display "___ removed"
        return render_template("removed.html", member=member)

    # Blank removal form
    else:
        # Query db for active members list, save in list
        member_list = db.execute(
            select(User.username)
            .where(User.active == '1')
            .order_by(User.username)
        )
        member_list = member_list.mappings().all()
        db.commit()

        # Feed list to html
        return render_template("remove.html", member_list=member_list)


# Change member
@app.route("/change_member", methods=["GET", "POST"])
@login_required
def change_member():
    # Remove member from active status
    if request.method == "POST":

        # Get form imput    
        member = request.form.get("member")

        # Check/change password
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != "":
            print("Password:", password)
            if password != confirm_password:
                return render_template("apology.html", type="password mismatch")
            hashword = generate_password_hash(password)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(hash=hashword)
            )
            print("password updated")

        # Check/change rank
        rank = request.form.get("rank")
        if rank != None:
            print("Rank != none")
            print(rank)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(rank=rank)
            )
        
        # Platoon
        platoon = request.form.get("platoon")
        if platoon != None:
            print("Platoon != none")
            print(platoon)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(platoon=platoon)
            )

        # Active status
        active = request.form.get("active")
        if active != None:
            print("Active != none")
            print(active)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(active=active)
            )

        # Elligibility
        elligible = request.form.get("elligible")
        if elligible != None:
            print("Elligible != none")
            print(elligible)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(elligible=elligible)
            )
        
        db.commit()

        return render_template("changed.html", member=member)

    # Blank removal form
    else:

        # Query db for active members list, save in list
        member_list = db.execute(
            select(User.username)
            .where(User.active == '1')
            .order_by(User.username)
        )
        member_list = member_list.mappings().all()

        # Feed list to html
        return render_template("change.html", member_list=member_list)

        

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

        result = db.execute(select(User.id, User.username, User.hash, User.active).where(User.username == username))
        result = result.mappings().first()
        print(result)
        # Verify username in db
        if result == None:
            return render_template("apology.html", type="incorrect username")

        # Verify user is active
        if result['active'] != 1:
            return render_template("apology.html", type="user inactive")

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