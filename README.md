=====
Parser_log
=====

Parser_log is a Django app for or data processing and aggregation the Apache log.


Quick start
-----------

1. Add "parser_log" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'parser_log',
    ]

2. Include the log_doctor URLconf in your project urls.py like this::

    path(r'^log/', include('parser_log.urls')),

3. Run `python manage.py migrate` to create the parser_log models.

4. Run python manage.py downloadlog url\to\logfile\Apache. 
   (example "python manage.py downloadlog http://www.almhuette-raith.at/apache-log/access.log")

5. Start the development server and visit http://127.0.0.1:8000/log/
   to view aggregated information about the log file