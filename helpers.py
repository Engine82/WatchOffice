from functools import wraps
from flask import redirect, session

from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, MappedAsDataclass

from itertools import islice, chain


# Apology function for errors
def apology():
    return render_template("apology.html")

# Login required decorator
# Reference: https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



# SQLAlchemy declarative base - enables ORM mapping
class Base(MappedAsDataclass, DeclarativeBase):
    pass

# SQLAlchemy User class for users table
class User (Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    username: Mapped[str]
    hash: Mapped[str]
    rank: Mapped[str]
    platoon: Mapped[int]
    active: Mapped[int]
    elligible: Mapped[int]
    tag_flipped: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


# SQLAlchemy class for next_to_work table
class Ntw (Base):
    __tablename__ = "next_to_work"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[str]
    platoon: Mapped[int]


# Find next-up person
def find_next_up(tag_list):
    for person in tag_list:
        match person:
            case {'tag_flipped': tag_flipped} if tag_flipped != 1:
                # Return {'username': 'kyle', 'tag_flipped': 0}
                return tag_list.index(person)
    # If nobody is flipped, return first person
    for person in tag_list:
        person['tag_flipped'] = 0
    return 0


def get_availability(member_up, availability):
    for person in availability:
        match person:
            case {'username': username} if username == member_up:
                return(person)
    return 1


def flip_tag(taglist, member_up):
    for person in taglist:
        match person:
            case {'username': username} if username == member_up:
                person['tag_flipped'] = 1
                return()


# Hire function
# opening: {'username': opening['username'], 'shift': 'day'}
# availability: [{'username': member['username'], 'day': 'available', 'night': 'unavailable'}, {}]
# taglist: [{'username': member['username'], 'tag_flipped': 0}, {}]
def hire(opening, availability, taglist, results, time, covering_count, shift_size):

    # Session is used here to make results available upon each iteration when recursing
    # Clear session['results']
    session['results'] = []
    
    if covering_count < shift_size:
        # Find next person up (tag_flipped == 0)
        next_up = find_next_up(taglist)
        next_up_name = taglist[next_up]['username']

        # Get availability of next_up person
        avail = get_availability(next_up_name, availability)

        # Flip tag
        flip_tag(taglist, next_up_name)
        
        # Goal: session[tag_list][{'username': 'kyle', 'tag_flipped': 1}
        covering_count += 1

        # If available
        if avail[time] == 'available':
            results.append({
                'person_covering': next_up_name,
                'person_off': opening['username']
            })
            return([results, covering_count])

        # If unavailable:
        else:
            results.append({
                'person_covering': next_up_name,
                'person_off': 'unavailable'
            })
            print(results)
            return(hire(opening, availability, taglist, results, time, covering_count, shift_size))

    # If everyone has been checked and either hired or unavailable, hire from 96 off
    else:
    # if session['count'] >= shift_size:
        results.append({
            'person_covering': "96 Off",
            'person_off': opening['username']
        })
        return([results, covering_count])
    #return(hire(opening, availability, taglist, results, time, covering_count, shift_size))

    #    return(taglist[next_up])
    '''list of results for this opening - all unavailable skipped + covering person hired/96 off'''
