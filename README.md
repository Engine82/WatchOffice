# Watch Office

## Introduction and History

Watch office is a tool to automate hiring for overtime at the Laconia, NH fire department. Overtime is assigned on the first day of a shift's "tour," on a rotating basis by seniority. Historically this has been done manually by the on-duty officer, and Watch Office's purpose is to automate this process, saving time and making shift officers available to accomplish more meaningful tasks.

The name Watch Office comes from the room in many firehouses referred to as the "watch office" or "watch desk." Before electronic alerting systems, one firefighter would be assigned to "house watch" 24 hours a day, where they would listen to the dispatch radio and alert crews when they were dispatched to an emergency.  


## Background: Schedule & Overtime Hiring Rules

[The Laconia Fire Department](https://www.laconianh.gov/1002/Fire-Department) is divided into four platoons, working 24 hour shifts on an eight day rotation. Firefighters work one 24 hour shift, have 48 hours off, work another 24 hour shift, and then have 96 hours off. It may also be charactarized as 1-2-1-4: 1 day on duty, 2 off, 1 on, and 4 off. The 1-2-1 portion is referred to as a platoon's "tour." On the first day of a tour, overtime is assigned for the next two days, which is internally referred to as "the hiring." Overtime is assigned by seniority, with the first shift assigned to the last person to not be hired. For example, if the senior-most firefighter was hired last during the current tour, the second-most senior firefighter would be hired first on the next tour. All overtime is mandatory; if a member does not wish to work their assigned overtime shift they may give it away to any other qualified member.

Newly hired firefighters are not elligible for overtime for their first four months so that they may have adequate time to learn how the department operates.  

## Features Overview

The main feature of WatchOffice is the Hiring """"function"""". This """function""" takes series of inputs from the user, assigns open shifts to available members, and saves submitted results in a database. The history function allows the user to recall previous hiring results. Manual Hiring allows the user to assign the next-up officer and firefighter for instances where the hiring """"function""""" does not yet account for. Additionally, there are features that allow a user to create new user accounts, change attributes of a user's account, and delete user accounts.  

## Design Rationale

WatchOffice uses the [Flask](https://flask.palletsprojects.com/en/1.1.x/quickstart/) framework for [Python](https://docs.python.org/3/) for the backend, [SQLite3](https://www.sqlite.org/docs.html) for the database, and [HTML](https://html.spec.whatwg.org/)/[CSS](https://www.w3.org/TR/CSS/#css)/[JavaScript](https://developer.mozilla.org/en-US/docs/Web/javascript) for the frontend. All of these were chosen because at the time of writing they were all the most fammiliar options, having been covered in [cs50](https://cs50.harvard.edu/x/2023/). Additionally, Python is a modern, widely used language with an abundance of freely availably resources. This is a low-traffic application, and SQLite is more than capable of handling WatchOffice's anticipated traffic and data-storage needs. HTML, CSS and JavaScript are all standard for web programming, and a natural choice, especially for a new programmer.
