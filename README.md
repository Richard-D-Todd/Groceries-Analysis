# Extract-Email
This is my first python project. The aim is use the email receipts for my online grocery shops and analyse my spending. This project will also give me experience in:
* Using Jupyter Notebooks to clean and analyse data.
* Loading data into a database and then querying the data.
* Writing scripts in Python to automate the processing of the email files, before exporting to CSV files and to a PostgreSQL database.

## Software used:
1. Jupyter Notebooks
    * Write and test code to extract and clean data using python. 
    * Load and extract data into and from a PostgreSQL DB.
    * Visualise my spending using Matplotlib.

2. Python
    * I will create a python script to take an email receipt, extract the data, then export the data to a csv and a postgreSQL database. This will be based on the code tested in the Jupyter Notebook _Extract data from ASDA emails_.
    * Create a second script which can process multiple email files from a directory.

3. PostgreSQL
    * Store the order details, delivered items and unavailable items for each shop in tables in a database. Data can then easily be extracted for analysis using SQL queries.

## Files:
These are the main files in which I will be processing, analysing and exploring my data.
### Analysis of Groceries Data.ipynb
This is the Juypter Notebook in which I visualise my spending and write queries to explore my data.

### Extract data from ASDA emails.ipynb
This is the Notebook in which I tested code to help extract and clean the data from my groceries emails. The code used here was the basis for my Python scripts.

### extract_script.py
Extract the data from receipt email file. Can export to both  CSV or PostgreSQL DB. The email file has to be in the _.eml_ file format.

### run_multi_extract.py
Similar to the _extract\_script.py_ script, but can be used to process all the email files in a directory.

### Other Files:
These are the support files.
* __categories.txt;__ This is used to contain the category headings from the ordered section of the emails. If a new category heading is needed then it is added to this file.
* __config.py;__ Used to read a database.ini file to easily obtain the database parameters.
* __create tables queries.sql;__ A SQL query to create the tables needed for this project on a database.
* __Your updated ASDA Groceries order.eml;__ A copy of a receipt email with personal details redacted.
* __Order Recipt.eml;__ ASDA updated the formattting of their receipt email. This is a copy of one of these recipt emails with personal information redacted.

