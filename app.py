from datetime import datetime
from sqlalchemy import create_engine, insert, join, select, text, update
from sqlalchemy.orm import sessionmaker
from flask import Flask, redirect, render_template, request, session
from flask_session import Session

# https://pydoc.dev/werkzeug/latest/werkzeug.security.html
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, gen_meme
from helpers import Base, User, Hiring, Hiring_list
from helpers import find_next_up, hire

from helpers import make_phone_call


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
NUM_PLATOONS = 4
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
    # If logged in, display schedule; if not logged in, redirect to login page
    if not session.get("user_id"):
        return redirect("/login")

    else:
        # Initialize lists for html
        offs_up = []
        ffs_up = []

        # Loop through each platoon, add next up ff and officer to list
        for i in range(1, NUM_PLATOONS + 1):

            # Initialize lists
            officers = []
            firefighters = []

            # get next-up members for this platoon and save in corresponding lists
            officer = db.execute(
                select(User.id, User.first_name, User.last_name, User.tag_flipped)
                .where(User.platoon == i)
                .where(User.active == 1)
                .where(User.rank != "firefighter")
            )
            officer = officer.mappings().all()
            officers.append(officer)
            if len(officers[0]) > 0:
                off_up = find_next_up(officers[0])
                offs_up.append(off_up)
            else: 
                offs_up.append({'first_name': 'No officers assigned to this platoon'})

            firefighter = db.execute(
                select(User.id, User.first_name, User.last_name, User.tag_flipped)
                .where(User.platoon == i)
                .where(User.active == 1)
                .where(User.rank == "firefighter")
            )
            firefighter = firefighter.mappings().all()
            firefighters.append(firefighter)
            if len(firefighters[0]) > 0:
                ff_up = find_next_up(firefighters[0])
                ffs_up.append(ff_up)
            else:
                ffs_up.append({'first_name': 'No firefighters assigned to this platoon'})

        return render_template("index.html", offs=offs_up, ffs=ffs_up)


# HIRING
# Hiring form / completed hiring
# Select which platoon is covering OT
@app.route("/hiring_a", methods=["GET", "POST"])
@login_required
def hiring_a():

    # After platoon is selected
    if request.method == "POST":

        # Save platoon choice in session
        session["platoon"] = request.form.get("platoon")
        return redirect("/hiring_b")

    # If starting new hiring
    else:

        # Render the hiring_a page
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
                day_2 = "day_2_" + session['hiring_tiers'][tier - 1]['tier'] + "_" + str(person_counter)

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

        # query db for list of elligible officers & firefighters from this platoon, and save as dicts
        officers = db.execute(
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.rank,
                User.tag_flipped
            )
            .where(User.platoon == session['platoon'])
            .where(User.elligible == "1")
            .where(User.active == "1")
            .where(User.rank != "firefighter")
            .order_by(User.id)
        )
        officers = officers.mappings().all()

        firefighters = db.execute(
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.rank,
                User.tag_flipped
            )
            .where(User.platoon == session['platoon'])
            .where(User.elligible == "1")
            .where(User.active == "1")
            .where(User.rank == "firefighter")
            .order_by(User.id)
        )
        firefighters = firefighters.mappings().all()

        session['personnel'] = [officers, firefighters]

        # Create list of titles for HTML
        session['cover_days'] = [{"day": "First Cover Day"}, {"day": "Second Cover Day"}]
        session['hiring_tiers'] = [{"tier": "Officers"}, {"tier": "Firefighters"}]

        return render_template(
            "hiring_b.html",
            cover_days=session['cover_days'],
            days_covered=DAYS_COVERED,
            firefighters=session['personnel'],
            hiring_tiers=session['hiring_tiers'],
            platoon=session['platoon']
        )


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


        # For each cover day and rank, add vacancies to shifts up to full-size
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

        return render_template(
            "hiring_c.html",
            cover_1_firefighters=cover_1_firefighters,
            cover_1_officers=cover_1_officers,
            cover_2_firefighters=cover_2_firefighters,
            cover_2_officers=cover_2_officers,
            days_covered=days_covered,
            platoon=session['platoon']
        )


# Hire for shifts, return hiring list
@app.route("/hired", methods=["GET", "POST"])
@login_required
def hired():
    
    # POST: Save approved hiring in db and print results
    if request.method == "POST":

        # UPDATE TAGS IN DB
        # Go through each rank
        for index, rank in enumerate(session['hiring_tiers']):
            rnk = rank['tier'].lower()

            # Go through each member in taglist at that rank
            for member in session[rnk + '_tags']:
                
                # If this member isn't next up, their tag is flipped
                if member['tag_flipped'] == 1:
                    db.execute(
                        update(User)
                        .where(User.id == member['id'])
                        .values(tag_flipped=1)
                    )

                # Otherwise, their tag is not flipped
                else:
                    db.execute(
                        update(User)
                        .where(User.id == member['id'])
                        .values(tag_flipped=0)
                    )
                    
        # Commit all updates to db
        db.commit()

        # SAVE RESULTS IN DB
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
            hiring_id = db.execute(
                select(Hiring.hiring_id)
                .order_by(Hiring.hiring_id.desc())
                .limit(1)
            )
            hiring_id = hiring_id.mappings().all()
            hiring_id = hiring_id[0]['hiring_id']
            hiring_id += 1

        # Handle the first iteration of hiring
        except:
            hiring_id = 0

        # Iterate through each hiring entry and save it in db, or if no hiring, save that
        daynight = ['day', 'night']

        # Iterate through each day and rank
        day = 1
        while day <= DAYS_COVERED:
            for rank in session['hiring_tiers']:

                # Iterate through each opening
                rank_lower = rank['tier'].lower()
                for time in daynight:

                    # If hiring at this day/rank/time has been done,
                    if session[rank_lower + "_hired_" + time + "_" + str(day)] != []:
                        for shift in session[rank_lower + "_hired_" + time + "_" + str(day)]:
                            db.execute(
                                text("""INSERT INTO hiring (
                                    hiring_id,
                                    platoon,
                                    rank,
                                    day,
                                    time,
                                    out_id,
                                    out_first,
                                    out_last,
                                    covering_id,
                                    covering_first,
                                    covering_last
                                ) VALUES (
                                    :hiring_id,
                                    :platoon,
                                    :rank,
                                    :day,
                                    :time,
                                    :out_id,
                                    :out_first,
                                    :out_last,
                                    :covering_id,
                                    :covering_first,
                                    :covering_last)
                                """), [{
                                    "hiring_id": hiring_id,
                                    "platoon": session['platoon'],
                                    "rank": rank['tier'],
                                    "day": day,
                                    "time": time,
                                    "out_id": shift['out_id'],
                                    "out_first": shift['out_first'],
                                    "out_last": shift['out_last'],
                                    "covering_id": shift['covering_id'],
                                    "covering_first": shift['covering_first'],
                                    "covering_last": shift['covering_last']
                                }]
                            )
                            db.commit()

                    # if no hiring at this day/rank/time
                    else:
                        db.execute(
                            text("""INSERT INTO hiring (
                                hiring_id,
                                platoon,
                                rank,
                                day,
                                time,
                                out_id,
                                out_first,
                                out_last,
                                covering_id,
                                covering_first,
                                covering_last
                            ) VALUES (
                                :hiring_id,
                                :platoon,
                                :rank,
                                :day,
                                :time,
                                :out_id,
                                :out_first,
                                :out_last,
                                :covering_id,
                                :covering_first,
                                :covering_last)
                            """), [{
                                "hiring_id": hiring_id,
                                "platoon": session['platoon'],
                                "rank": rank['tier'],
                                "day": day,
                                "time": time,
                                "out_id": "0",
                                "out_first": "none",
                                "out_last": "none",
                                "covering_id": "0",
                                "covering_first": "none",
                                "covering_last": "none"
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

        # redirect to homepage, where user will see the updated tagboard
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

                    # Get this open shift's info - who's out 
                    shift_day = {
                        'id': opening['id'],
                        'first_name': opening['first_name'],
                        'last_name': opening['last_name'],
                        'shift': 'day'
                    }
                    shift_night = {
                        'id': opening['id'],
                        'first_name': opening['first_name'],
                        'last_name': opening['last_name'],
                        'shift': 'night'
                    }

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
                    'first_name': member['first_name'],
                    'last_name': member['last_name'],
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
                
                # Create lowercase rank name for use in variables, get number of people on covering shift for future use
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

        # Save next-up officer & firefighter, and update taglist in db
        for rank in session['hiring_tiers']:
            rnk = rank['tier'].lower()
            
            # Save next up members
            if len( session[rnk + '_tags']) > 0:
                session['up_next'].append({
                    'rank': rnk,
                    'up_next': find_next_up(session[rnk + '_tags'])
                })
            else:
                session['up_next'].append({
                    'rank': rnk,
                    'up_next': {'first_name': 'No members at this rank'}
                })

        # Display hired form with hiring results
        return render_template(
            "hired.html", 
            officers_day_1=session['officers_hired_day_1'],
            officers_night_1=session['officers_hired_night_1'],
            officers_day_2=session['officers_hired_day_2'],
            officers_night_2=session['officers_hired_night_2'],
            firefighters_day_1=session['firefighters_hired_day_1'],
            firefighters_night_1=session['firefighters_hired_night_1'],
            firefighters_day_2=session['firefighters_hired_day_2'],
            firefighters_night_2=session['firefighters_hired_night_2'],
            up_next=session['up_next'],
            platoon=session['platoon']
        )    


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

        for day in range(1, DAYS_COVERED + 1):
            print("day:", day)
            for rank in hiring_tiers:
                for time in daynight:
                    db.execute(
                        text("""INSERT INTO hiring (
                            hiring_id,
                            platoon,
                            rank,
                            day,
                            time,
                            out_id,
                            out_first,
                            out_last,
                            covering_id,
                            covering_first,
                            covering_last
                        ) VALUES (
                            :hiring_id,
                            :platoon,
                            :rank,
                            :day,
                            :time,
                            :out_id,
                            :out_first,
                            :out_last,
                            :covering_id,
                            :covering_first,
                            :covering_last)
                        """), [{
                            "hiring_id": hiring_id,
                            "platoon": session['platoon'],
                            "rank": rank['tier'],
                            "day": day,
                            "time": time,
                            "out_id": 1,
                            "out_first": "manual",
                            "out_last": "override",
                            "covering_id": 1,
                            "covering_first": "manual",
                            "covering_last": "override"
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
            select(User.id, User.first_name, User.last_name)
            .where(User.platoon == session['platoon'])
            .where(User.elligible == "1")
            .where(User.active == "1")
            .where(User.rank != "firefighter")
            .order_by(User.id)
        )
        session['covering_officer'] = covering_officers.mappings().all()
        print("covering officer:", session['covering_officer'])

        covering_firefighters = db.execute(
            select(User.id, User.first_name, User.last_name)
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

        # get date of the hiring
        hiring_date = db.execute(select(Hiring_list.created_at).where(Hiring_list.hiring_id == past_id))
        hiring_date = hiring_date.scalars().all()
        hiring_datetime = datetime.strptime(hiring_date[0], '%Y-%m-%d %H:%M:%S')
        display_date = datetime.strftime(hiring_datetime, '%-m/%-d/%Y')   

        # Loop through day/rank/time
        daynight = ["day", "night"]
        day = 1
        while day <= DAYS_COVERED:

            for rank in hiring_tiers:
                rnk = rank['tier'].lower()

                for time in daynight:

                    # Query db for hiring at this day/rank/time and save in session
                    past_hiring = db.execute(
                        select(Hiring.covering_first, Hiring.covering_last, Hiring.out_first, Hiring.out_last)
                        .where(Hiring.hiring_id == past_id)
                        .where(Hiring.day == day)
                        .where(Hiring.rank == rank['tier'])
                        .where(Hiring.time == time)
                    )
                    past_hiring = past_hiring.mappings().all()
                    print("Past hiring:", past_hiring)

                    session[rnk + "_" + "past_hiring" + "_" + time + "_" + str(day)].extend(past_hiring)
                    
            day += 1
        
        print(
            session['officers_past_hiring_day_1']
        )

        # display hiring results a la hired.html
        return render_template(
            "history_found.html", 
            officers_day_1=session['officers_past_hiring_day_1'],
            officers_night_1=session['officers_past_hiring_night_1'],
            officers_day_2=session['officers_past_hiring_day_2'],
            officers_night_2=session['officers_past_hiring_night_2'],
            firefighters_day_1=session['firefighters_past_hiring_day_1'],
            firefighters_night_1=session['firefighters_past_hiring_night_1'],
            firefighters_day_2=session['firefighters_past_hiring_day_2'],
            firefighters_night_2=session['firefighters_past_hiring_night_2'],
            platoon=past_platoon,
            display_date=display_date
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
@login_required
def add_member():

    # Add member to db
    if request.method == "POST":

        # Check for inputs
        if not request.form.get("username"):
            return render_template("apology.html", source=gen_meme("username"))
        if not request.form.get("first_name"):
            return render_template("apology.html", source=gen_meme("first_name"))
        if not request.form.get("last_name"):
            return render_template("apology.html", source=gen_meme("last_name"))
        if not request.form.get("password"):
            return render_template("apology.html", source=gen_meme("password"))
        if not request.form.get("rank"):
            return render_template("apology.html", source=gen_meme("rank"))
        if not request.form.get("platoon"):
            return render_template("apology.html", source=gen_meme("platoon"))
        if not request.form.get("active"):
            return render_template("apology.html", source=gen_meme("active_status"))
        if not request.form.get("elligibility"):
            return render_template("apology.html", source=gen_meme("elligibility"))

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
                return render_template("apology.html", source=gen_meme("username_taken"))

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

        fullname = first_name + " " + last_name
        return render_template("added.html", member=fullname)

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
        member = int(member)
        
        # Get member's name for display
        name = db.execute(
            select(User.first_name, User.last_name, User.platoon, User.rank)
            .where(User.id == member)
        )
        name = name.mappings().all()
        name_txt = name[0]['first_name'] + " " + name[0]['last_name']

        # update tag list for case if member was up and is lowest:
        plt_list = db.execute(
            select(User.id, User.tag_flipped)
            .where(User.platoon == name[0]['platoon'])
            .where(User.rank == name[0]['rank'])
        )
        plt_list = plt_list.mappings().all()
        up = find_next_up(plt_list)

        # If removed member is up
        if up['id'] == member:

            # And if removed member is last on their platoon at that rank,
            # Un-flip all the tags on that platoon at that rank status
            if plt_list[-1]['id'] == member:

                # handle firefighters
                if name[0]['rank'] == 'firefighter':
                    db.execute(
                        update(User)
                        .where(User.platoon == name[0]['platoon'])
                        .where(User.rank == 'firefighter')
                        .values(tag_flipped=0)
                    )
                
                # handle officers
                else:
                    db.execute(
                        update(User)
                        .where(User.platoon == name[0]['platoon'])
                        .where(User.rank != 'firefighter')
                        .values(tag_flipped=0)
                    )

                # if removed is any other member member, make next-most-senior member up..
                # which he will be simply by removing the current member, requiring no action

            
        # Update db: platoon = n/a, active = 0
        db.execute(
            update(User)
            .where(User.id == member)
            .values(active=0, platoon=0)
        )
        db.commit()

        # Display "[member] removed"
        return render_template("removed.html", member=name_txt)

    # Blank removal form
    else:
        # Query db for active members list, save in list
        member_list = db.execute(
            select(
                User.username,
                User.id,
                User.first_name,
                User.last_name
            )
            .where(User.active == '1')
            .order_by(User.last_name)
        )
        member_list = member_list.mappings().all()
        db.commit()

        # Render html with list of members to be selected
        return render_template("remove.html", member_list=member_list)


# Change member
@app.route("/change_member", methods=["GET", "POST"])
@login_required
def change_member():

    # Remove member from active status
    if request.method == "POST":

        # Get form imput    
        member = request.form.get("member")
        if member == str(0):
            return render_template("apology.html", source=gen_meme("select_member"))

        # Count changes:
        changes = 0
        # Check/change username
        username = request.form.get("username")
        if username != '':
            # Check availability of username
            result = db.execute(select(User.username))
            users = result.mappings().all()

            for user in users:
                if user.username == username:
                    return render_template("apology.html", source=gen_meme("username_taken"))

            db.execute(
                update(User)
                .where(User.username == member)
                .values(username=username)
            )
            changes += 1

        # Check/change first name
        first = request.form.get("first")
        if first != '':
            db.execute(
                update(User)
                .where(User.first_name == first)
                .values(first_name=first)
            )
            changes += 1

        # Check/change last name
        last = request.form.get("last")
        if last != '':
            db.execute(
                update(User)
                .where(User.last_name == last)
                .values(last_name=last)
            )
            changes += 1

        # Check/change password
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != '':
            if len(password) < 8 or len(password) > 64:
                return render_template("apology.html", source=gen_meme("password_length"))
            if password != confirm_password:
                return render_template("apology.html", source=gen_meme("password_mismatch"))

            hashword = generate_password_hash(password)
            db.execute(
                update(User)
                .where(User.username == member)
                .values(hash=hashword)
            )
            changes += 1

        # Check/change rank
        rank = request.form.get("rank")
        if rank != '':
            db.execute(
                update(User)
                .where(User.username == member)
                .values(rank=rank)
            )
            changes += 1
        
        # Platoon
        platoon = request.form.get("platoon")
        if platoon != str(0):
            db.execute(
                update(User)
                .where(User.username == member)
                .values(platoon=platoon)
            )
            changes += 1

        # Elligibility
        elligible = request.form.get("elligible")
        if int(elligible) != 2:
            db.execute(
                update(User)
                .where(User.username == member)
                .values(elligible=elligible)
            )
            changes += 1

        # Ensure something has been submitted to change before moving forward
        if changes == 0:
            return render_template("apology.html", source=gen_meme("no_changes_made"))

        db.commit()

        return render_template("changed.html", member=member)

    # Blank removal form
    else:

        # Query db for active members list, save in list
        member_list = db.execute(
            select(User.username, User.first_name, User.last_name)
            .where(User.active == '1')
            .order_by(User.last_name)
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

    # POST: When login form is submitted
    if request.method == "POST":

        # Check for username and password
        if not request.form.get("username"):
            return render_template("apology.html", source=gen_meme("username"))

        if not request.form.get("password"):
            return render_template("apology.html", source=gen_meme("password"))
        
        # Query db for username 
        username = request.form.get("username")
        password = request.form.get("password")

        result = db.execute(select(User.id, User.username, User.hash, User.active).where(User.username == username))
        result = result.mappings().first()

        # Verify username in db
        if result == None:
            return render_template("apology.html", source=gen_meme("incorrect_username"))

        # Verify user is active
        if result['active'] != 1:
            return render_template("apology.html", source=gen_meme("user_inactive"))

        # Verify password is correct
        if check_password_hash(result.hash, password) == False:
            return render_template("apology.html", source=gen_meme("incorrect_password"))
        
        # Save user in session
        session["user_id"] = result.id

        # Send to homepage
        return redirect("/") 
    
    # GET: Display login form
    else:
        return render_template("login.html")


# Log out
@app.route("/logout")
def logout():

    # Remove user from session
    session["user_id"] = None

    # Send to login
    return redirect("/login")


# 96-Off
@app.route("/off_shift", methods=["GET", "POST"])
def off_shift():

    # POST make calls, save results:
    if request.method == "POST":

        # Create calling results list:
        calling_results = []
    
        # Get shift info
        in_station = request.form.get("in_station")
        if not in_station:
            return render_template('apology.html', source=gen_meme("on duty status required"))

        member_out = request.form.get("member")
        if not member_out:
            return render_template('apology.html', source=gen_meme("member required"))

        date = request.form.get('date')
        if not date:
            return render_template('apology.html', source=gen_meme("date required"))
        
        # Validate date is in the future (front-end too)
        date_today = datetime.today()
        date_today = date_today.strftime('%Y-%m-%d')
        if date < date_today:
            return render_template('apology.html', source=gen_meme("shift date is in the past"))

        shift = request.form.get('shift')
        if not shift:
            return render_template('apology.html', source=gen_meme("shift required"))

        if shift == "3": #hours
            start_time = request.form.get('hours_start')
            if not start_time:
                return render_template('apology.html', source=gen_meme("start time required"))

            end_time = request.form.get('hours_end')
            if not end_time:
                return render_template('apology.html', source=gen_meme("end time required"))

        day_out = request.form.get('day_out')
        if not day_out:
            return render_template('apology.html', source=gen_meme("day out required"))
        print("Day out: ", day_out)

        # Get info of member who is out
        member_info = db.execute(
            select(User.first_name, User.last_name, User.rank, User.platoon)
            .where(User.id == member_out)
        )
        member_info = member_info.mappings().all()
        print(member_info)

        # Determine order in which to call shifts:
        plt = member_info[0].platoon
        print(plt)

        # Day out; 1 = on duty, 2 = off duty
        match (plt, day_out):
            
            # Platoon 1: 
            case(1, 1)
                plt_order = [1, 2]
            
            case(1, 2)
                plt_order = [1, 2]

            # Platoon 2
            case(2, 1)
                plt_order = [1, 2]
            
            case(2, 2)
                plt_order = [1, 2]

            # Platoon 3
            case(3, 1)
                plt_order = [1, 2]

            case(3, 2)
                plt_order = [1, 2]
        
            # Platoon 4
            case(4, 1)    
                plt_order = [1, 2]

            case(4, 2)
                plt_order = [1, 2]


        # Loop through each shift to be hired for
        # for platoon in plt_1_1st:

        # # Assemble list of numbers to call
        #     # Loop through each platoon in ordered list (for platoon 3 day 2: [1, 2, 4])
        # # Make calls
        #     to_number = input("Enter the phone number to call: ")
            
        #     # Create text for call
        #     if shift == 3:
        #         message = "You are elligible for an overtime shift with the Laconia Fire Department. This shift is for hours from " + start_time + "to " + end_time + 
        #         "on" + date + ". Please call the central station if you want to accept this shift."
        #     else:
        #         message = "You are elligible for an overtime shift with the Laconia Fire Department. This shift is for hours from " + start_time + "to " + end_time + 
        #         "on" + date + ". Please call the central station if you want to accept this shift."

        #     call_success = make_phone_call(to_number, message)
            
        #     # Log results of each call
        #     if call_success:
        #         calling_results.append({'time': time, 'member out': member, 'member called': member_id, 'call successful': 1})

        #     else:
        #         calling_results.append({'time': time, 'member out': member, 'member called': member_id, 'call successful': 0})
        #         return redirect("/calling_error")

                # If shift is taken, save and display results
            # If no one takes the shift, render mandatory page/form
        return redirect("/")

    # GET: Serve form
    else:

        # Query db for active members list, save in list
        members = db.execute(
            select(User.id, User.first_name, User.last_name)
            .where(User.active == '1')
            .order_by(User.last_name)
        )
        members = members.mappings().all()

        # Feed list to html
        return render_template("off_shift_a.html", members=members)

@app.route("/calling_error", methods=["GET", "POST"])
def off_shift_2():

    # POST
    if request.method == "POST":
        return redirect("/")
        
    else:
        return redirect("/")

    

    # Also create feature to send text with a message (fior disregard or testing messaging for example)
    # Will have to add phone numbers to users table in db
    # For now, add column in hirings table for off-shift usage
