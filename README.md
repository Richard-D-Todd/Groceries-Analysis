# Groceries Analysis Project
This is my first Python project. The aim of this project is to use Python to parse the recipe emails I receive for my grocery deliveries so that I can analyse my spending. This project is split into several parts:   
* Parsing the receipt emails for my grocery shops.
* Wrangling the data into a useable form.
* Exporting to the data into a database.
* Creating a Dashboard  so that I can easily view my spending.
* Further analysis into my spending habits and trends.

## Software and tools used
### Python
* The script to extract data from email files and export to file and database is written in Python. Pandas is used for data wrangling while SQLalchemy is used to connect to my PostgeSQL database.
* The dashboard is written using the Dash and Plotly Python libraries.
* Jupyter Notebooks are used for protyping and some inital visualisations.
* Exchangelib Python library is used to connect to my Microsoft Exchange email account.

### Postgres
* A Postgres database is used to store the data extracted from the emails.
* PostreSQL is used to write to the database and queries are used in the dashboard scripts as well as Jupyter Notebooks.

### Raspberry Pi
I used my Raspberry Pi to host the Postgres database and dashboard.

### Heroku
Heroku was used to host a version of my dashboard which I can access remotely.

## How this Project Works
There are two ways to extract the email data. 
1. By running one of the import scrips in the 'Extract from file' drectory which can read in data from .eml format email files.
2. By running the extract from exchange script in the 'Extract From Exchange' directory.
I am currently only actively updating the direct connection to my outlook account method, and I consider the extracting from file method depreciated.

When a receive a receipt email I run the extract_from_exchange_script.py script which does the following:
1. Connects to my outlook email account.
2. Iterates through all my emails in a specific folder my receipt emails get auto moved to. The subject, timestamp and body of the email are saved as variables.
3. I parse the details from the email files and save them to Pandas Dataframes.
4. The dataframes are saved to the PostgreSQL instance I have running on my RaspberryPi, using the SQLalchemy to handle the connection engine.
5. I have a dashboard that I run on my RaspberryPi so that I can access the dashboard from my home network.

My next goal is to run a CRON job on my RaspberryPi to periodically run my extract from exchange script, as well as refresh my Dasboard periodically.
