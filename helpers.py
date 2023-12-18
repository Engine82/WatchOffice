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
                place = tag_list.index(person)
                return place
    # If nobody is flipped, return first person
    return 0


# Re-order list function for starting with first-up on tag board
def reorder_tagboard(tag_list):
    start = find_next_up(tag_list)
    it = iter(tag_list)
    next(islice(it, start, start), None)
    return chain(it, islice(tag_list, start))