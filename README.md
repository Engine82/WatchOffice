# Watch Office

## Video Demo:

[![Watch the video](https://img.youtube.com/vi/2pG_GVW6l5g/hqdefault.jpg)](https://www.youtube.com/embed/2pG_GVW6l5g)

https://youtu.be/2pG_GVW6l5g

## Introduction and History

Watch Office is a tool to simplify hiring for overtime at the Laconia, NH fire department. Overtime is assigned on the first day of a shift's "tour," on a rotating basis by seniority. Historically this has been done manually by the on-duty officer, and Watch Office's purpose is to automate this process, saving time and making shift officers available to accomplish more meaningful tasks.

The name Watch Office comes from the room in many firehouses referred to as the "watch office" or "watch desk." Before electronic alerting systems, one firefighter would be assigned to "house watch" 24 hours a day, where they would listen to the dispatch radio and alert crews when they were dispatched to an emergency.  


## Design Rationale

WatchOffice uses the [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) framework for [Python](https://docs.python.org/3/) for the backend, [SQLite3](https://www.sqlite.org/docs.html) for the database, and [HTML](https://html.spec.whatwg.org/)/[CSS](https://www.w3.org/TR/CSS/#css)/[JavaScript](https://developer.mozilla.org/en-US/docs/Web/javascript) for the frontend. Python is a modern, widely used language with an abundance of freely available resources. This is a low-traffic application, and SQLite is more than capable of handling WatchOffice's anticipated traffic and data-storage needs. HTML, CSS and JavaScript are all standard for web programming, and a natural choice, especially for a new developer.


## Background: Schedule & Overtime Hiring Rules

[The Laconia Fire Department](https://www.laconianh.gov/1002/Fire-Department) is divided into four platoons, working 24 hour shifts on an eight day rotation. Firefighters work one 24 hour shift, have 48 hours off, work another 24 hour shift, and then have 96 hours off. It may also be charactarized as 1-2-1-4: 1 day on duty, 2 off, 1 on, and 4 off. The 1-2-1 portion is referred to as a platoon's "tour." On the first day of a tour, overtime is assigned for the next two days, which is internally referred to as "the hiring"; hire and hiring refer to a member being assigned an overtime shift, not hiring someone from outside the organization. Overtime is mandatory and assigned by seniority, with the first shift assigned to the last person to not be hired (however assigned shifts may be given away freely to other qualified members). For example, if the senior-most firefighter was hired last during the current tour, the second-most senior firefighter would be hired first on the next tour. All overtime is mandatory; if a member does not wish to work their assigned overtime shift they may give it away to any other qualified member.

Newly hired firefighters are not elligible for overtime for their first four months so that they may have adequate time to learn how the department operates.  

## Features Overview

The main feature of WatchOffice is the Hiring function This function takes series of inputs from the user, assigns open shifts to available members, and saves submitted results in a database. The history function allows the user to recall previous hiring results. Manual Hiring allows the user to assign the next-up officer and firefighter for instances where the hiring function does not yet account for. Additionally, there are features that allow a user to create new user accounts, change attributes of a user's account, and delete user accounts.  

## Files

- app.py runs the backend of the application, serving web pages and processing data. This is where the processing of data for assigning overtime shifts, saving hiring instances, recalling previous hirings, and adding, changing, and removing members.

- helpers.py stores the necessary definitions for SQLAlchemy to talk to the database. It is also where functions are defined, to be used by app.py, which is mainly functions handling tasks associated with the hiring algorithm.

- database.db is the SQLite3 database used to store user info, save hiring results, and a list of hirings done.

- database.txt has the create table statements to set up the db, as well as some instructions for entering the first few entries in the users table.

- requirements.txt is a text file that lists all the required programs and files for the application to run.

- /templates directory houses all of the .html files used to form the basis of the frontend.
    - layout.html is the main .html file, which includes the header/navbar, footer, and links for fonts, the stylesheet, etc.
    - All other .html files correspond to their specific page. Some, particularly hired.html and history_found.html, rely heavily on Jinja, loops and if/else statements.

- /static directory holds the CSS, JavaScript and image files used by the application.
    - add.js validates user input in the add user form.
    - alert.js alerts the user, asking if they are sure and wish to proceed when removing a user.
    - change.js validates user input in the change user form.
    - date.js adds today's date to the top of a new hiring result.
    - print.js alters the .html and prints the window to facilitate easier printing of new hiring results, and results from past hirings.
    - vacancy.js automatically sets vacancies' status' to "out 24" because a vacancy will always need 24-hour coverage.
    - watchOffice.css holds all styling for the application, including media queries to adapt to mobile devices.
