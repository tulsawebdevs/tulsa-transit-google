**This project is archived.**
*Tulsa Transit began publishing their GTFS data in 2013, and now the 
[Tulsa bus schedule is available in Google Maps](https://www.tulsaworld.com/news/local/government-and-politics/tulsa-transit-schedules-integrated-into-google-maps/article_8d65eea9-9d31-5d89-aedd-9ca525eab424.html)
and other trip planning software. Tulsa Transit does not use this project to
generate their GTFS feed.*

This project is for converting is the code a transit 'signup' from the
Metropolitan Tulsa Transit Authority (MTTA) into a General Transit Feed
Specification (GTFS), that can be used with other transit software such as
OpenTripPlanner.  Our goal is to get this data onto Google Maps and any other
publicly available transit database.

To run the project:

1. Install python, pip, virtualenv, and virtualenvwrapper
2. Run `mkvirtualenv ttg` to create the new virtualenv
3. Run `pip install -r requirements.txt` to download the third-party libraries
4. Install the GeoDjango requirements.  PostgreSQL and PostGIS recommended.
   See https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ref-gis-install
5. Get a copy of the Tulsa Transit Authority's signup data.  It should be a zip file.
6. Change to the `ttgsite` folder, copy `local_settings.example.py` to `local_settings.py`, change as needed.
7. Back in the main folder, run `./manage.py syncdb; ./manage.py migrate` to create a new database.
8. Run `./manage.py importmttasignup signup.zip` to import into SignUp #1
9. Run `./manage.py copymttatogtfs 1` to copy SignUp #1 to Feed #1 
10. Run `./manage.py exportgtfs --name feed.zip 1` to export Feed #1 to feed.zip
11. Run `feedvalidator.py feed.zip` to validate the feed
12. Run `schedule_viewer.py feed.zip` to view the schedule
13. Run `/manage.py runserver` to start up Django.  The Django admin may be the only interesting part.

Required files for this project
===============================
You'll need a signup file from the Tulsa Transit Authority to populate your
database.  Contact John Whitlock or Luke Crouch to get a copy.

Other useful information:

* http://www.ntdprogram.gov/ntdprogram/Glossary.htm
* http://code.google.com/transit/spec/transit_feed_specification.html
* http://nrtap.zendesk.com/home
* http://tripplanner.tulsawebdevs.org/index.html
* http://www.gtfs-data-exchange.com/
