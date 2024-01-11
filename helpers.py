from functools import wraps
from flask import redirect, session

from datetime import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, MappedAsDataclass


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
    first_name: Mapped[str]
    last_name: Mapped[str]
    hash: Mapped[str]
    rank: Mapped[str]
    platoon: Mapped[int]
    active: Mapped[int]
    elligible: Mapped[int]
    tag_flipped: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(init=False, server_default=func.now())


# SQLAlchemy class for hiring table
class Hiring (Base):
    __tablename__ = "hiring"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    hiring_id: Mapped[int]
    platoon: Mapped[int]
    rank: Mapped[str]
    day: Mapped[int]
    time: Mapped[str]
    member_out: Mapped[str]
    member_covering: Mapped[str]
    created_at: Mapped[str]


# SQLAlchemy class for hiring_list table
class Hiring_list (Base):
    __tablename__ = "hiring_list"
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    hiring_id: Mapped[int]
    created_at: Mapped[str]


# Find next-up person from tag list/tag board
def find_next_up(tag_list):
    for person in tag_list:
        match person:
            case {'tag_flipped': tag_flipped} if tag_flipped != 1:
                index = tag_list.index(person)
                return(tag_list[index])


    # If nobody is flipped, return first person
    for person in tag_list:
        person['tag_flipped'] = 0
    return(tag_list[0])


# Find this person (member_up)'s entry in the availability list  and return it
def get_availability(member_up, availability):
    for person in availability:
        match person:
            case {'id': id} if id == member_up:
                return(person)
    return 1


# Match the person who is up and flip their tag
def flip_tag(taglist, member_up):
    for person in taglist:
        match person:
            case {'id': id} if id == member_up:
                person['tag_flipped'] = 1
                return()


# Hire function
def hire(opening, availability, taglist, results, time, covering_count, shift_size, day, rank):

    # Session is used here to make results available upon each iteration when recursing
    # Clear session['results'] from previous openings' hiring
    session['results'] = []
    
    # If the entire covering shift has not been hired/unavailable
    if covering_count < shift_size:

        # Find next person up (tag_flipped == 0)
        next_up = find_next_up(taglist)
        print("next_up: ", next_up)

        # Get availability of next_up person
        avail = get_availability(next_up['id'], availability)

        # Flip tag of this person and increase counter
        flip_tag(taglist, next_up['id'])
        covering_count += 1

        # If available save results and return results and number of members checked
        if avail[time] == 'available':
            results.append({
                'person_covering': next_up['id'],
                'covering_name': next_up['name'],
                'person_off': opening['id'],
                'off_name': opening['name'],
                'day': day,
                'time': time, 
                'rank': rank
            })
            return([results, covering_count])

        # If unavailable save that result and call hiring function to fill opening
        else:
            results.append({
                'person_covering': next_up['id'],
                'covering_name': next_up['name'],
                'person_off': 'unavailable',
                'off_name': 'unavailable',
                'day': day,
                'time': time,
                'rank': rank
            })
            return(hire(opening, availability, taglist, results, time, covering_count, shift_size, day, rank))

    # If everyone has been checked and either hired or unavailable, hire from 96 off
    # Save 96 off and return results and number of members checked
    else:
        results.append({
            'person_covering': "96 Off",
            'covering_name': "96 Off",
            'person_off': opening['id'],
            'off_name': opening['name'],
            'day': day,
            'time': time, 
            'rank': rank
        })
        return([results, covering_count])

def find_name(member_list, member):
    for person in member_list:
        print(member)
        print(person)
        print(person['id'])
        if person['id'] == str(member):
            member_name = person['first_name'] + " " + person['last_name']
            print("Name", member_name)
            return(member_name)