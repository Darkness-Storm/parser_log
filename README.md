
Parser_log
-----------

Parser_log is a Django app for or data processing and aggregation the Apache log.


Quick start
-----------

1. Requirements
---------------

    1. Django==2.0
    2. requests==2.18
    3. xlwt==1.3

2. Installation
---------------

    1. git clone https://github.com/Darkness-Storm/parser_log.git

    (you will need git installed)

    2. Install the required dependencies by running
        cd path/to/project/parser_log (go to the project directory)
        pip install -r requirements.txt

    3. Run `python manage.py migrate` to create database (default SQLite3) and the parser_log models.

    4. Run 'python manage.py downloadlog url\to\logfile\Apache'
    (example "python manage.py downloadlog http://www.almhuette-raith.at/apache-log/access.log",
    for more details on 'python manage.py help downloadlog')

    5. Start the development server 'python manage.py runserver' and visit http://127.0.0.1:8000/apachelog/
    to view aggregated information about the log file
