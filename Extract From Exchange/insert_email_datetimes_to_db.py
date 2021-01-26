################################################### Insert email datetimes into groceries database ###################################################
#                                                                                                                                                    #
#  This script is used to grab the datetime received for each email in the 'ASDA order receipts' folder in my email account.                         #
#  I also grab the order number from the body of each email. these are combined in a dataframe and then the order_number is compared with the        #
# order numbers already present in the database. If the order number exists in the database then I insert the corresponding timestamp into           #
# the email datetime table of the database.                                                                                                          #
#                                                                                                                                                    #
# This script only needs to be ran once so that entries in the database without a email timestamp can have this added.                               #
#                                                                                                                                                    #
######################################################################################################################################################

########## Import Libraries ##########
from exchangelib import Credentials, Account, Folder, Message, EWSDateTime
from requests_html import HTML
import configparser
import datetime
import pandas as pd
import re
from sqlalchemy import create_engine

########## Functions ###########
def create_sqlalchemy_engine():
    """
    This function creates a sqlalchemy engine with the credentials stored in the credentials.py file
    """
    config = configparser.ConfigParser()
    config.read('database.ini')
    username = config['postgresql']['user']
    password = config['postgresql']['password']
    database = config['postgresql']['database']
    host = config['postgresql']['host']
    con_string = 'postgresql+psycopg2://{}:{}@{}/{}?gssencmode=disable'.format(username, password, host, database)
    engine = create_engine(con_string)
    print("Local DB: {}".format(con_string))
    return engine

# Importing account email address and password
config = configparser.ConfigParser()
config.read('exchange_credentials.ini')
email_address = config['credentials']['email_address']
password = config['credentials']['password']

# Defining credentials for exchange account and setting account
credentials = Credentials(email_address, password)
account = Account(email_address, credentials = credentials, autodiscover = True)

# navigating to folder containing my ASDA receipts
receipt_folder = account.inbox / 'ASDA Order Receipts'

# creating list of items in the folder and ordering by received datetime
items = receipt_folder.all().order_by('-datetime_received')

# Extract datetime_received, subject and body from each item
item_details = items.values('datetime_received', 'subject', 'body')

datetime_list = []
order_number_list = []

# For each item we want to check the subject line to decide how to grab the order number. 
# Then extract the order number and datetime to respective lists
for item in item_details:
    datetime = item['datetime_received']
    subject = item['subject']

    # append datetime to datetime_list
    datetime_list.append(datetime)

    # Convert body to lines
    body_raw = item['body']
    body_html = HTML(html = body_raw)
    body = body_html.find('tr')[0].text
    body_lines = body.splitlines()

    if subject == 'Your updated ASDA Groceries order':
        try:
            # order number is on line below line == 'Order Number'
            order_number = body_lines[body_lines.index('Order Number:') + 1]
            # add order_number to list
            order_number_list.append(order_number)
        except:
            order_number_list.append("not found")
            print("Order Number not found for email with datetime: ", datetime)
    
    elif subject == 'Order Receipt':
        # Order number may be reference as Order Receipt, Order Number or something else
        try:
            # Look for order receipt
            order_number = body_lines[body_lines.index('Order Receipt:') + 1]
            order_number_list.append(order_number)
        except:
            try:
                # Look for Order Number
                order_number = body_lines[body_lines.index('Order Number:') + 1]
                order_number_list.append(order_number)
            except:
                # May also have order number trailing order on the same line
                for line in body_lines:
                    order_number = re.match("Order\s\d+", line)
                    if order_number != None:
                        break
                    else:
                        continue
                order_number = order_number.group(0)
                order_number = re.split("\s", order_number)[1]
                order_number_list.append(order_number)

# Create pandas dataframe with the email received datatime and the order number
df_email_details = pd.DataFrame(list(zip(order_number_list, datetime_list)), columns = ['order_number', 'email_datetime'])

# Get Order_numbers which are currently stored in the database
# connect to database
engine = create_sqlalchemy_engine()

query = "select order_number from order_details"

order_number_in_db = pd.read_sql_query(query, con = engine, index_col = None)

# compare each order_number in email details dataframe with the order numbers from the database
check_in_db = df_email_details['order_number'].isin(order_number_in_db['order_number'])

# filtering the email details dataframe so that only values in both lists remain
# This dataframe will be inserted into the database so that each order in the database has an entry for the email recieved datetime
df_insert_into_email_datetime_table = df_email_details[check_in_db == True]

df_insert_into_email_datetime_table.to_sql('email_datetime', con = engine, if_exists = 'append', index = False)

print("inserted into database")