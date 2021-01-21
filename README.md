# Groceries Analysis Project
This is my first Python project. The aim of this project is to use Python to parse the recipe emails I receive for my grocery deliveries so that I can analyse my spending. This project is split into several parts:   
* Parsing the receipt emails for my grocery shops.
* Wrangling the data into a useable form.
* Exporting to the data into a database.
* Creating a Dashboard  so that I can easily view my spending.
* Further analysis into my spending habits and trends.

## Software and tools used
### Python
* Script to extract data from emails and export to file and database.
* Dashboard is written using the Dash and Plotly libraries.
* Jupyter Notebooks used for protyping and some inital visualisations.

### Postgres
* A Postgres database is used to store the data extracted from the emails.
* PostreSQL is used to write to the database and queries are used in the dashboard scripts as well as Jupyter Notebooks.

### Raspberry Pi
I used my Raspberry Pi to host the Postgres database and dashboard.

### Heroku
Heroku was used to host a version of my dashboard which I can access remotely. None of the code for this remote version of my dashboard is available publicly.


