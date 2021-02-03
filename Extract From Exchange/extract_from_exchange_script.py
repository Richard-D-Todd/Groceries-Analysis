############################################################ Extract from exchange script ############################################################
"""
The script is used to connect to the email account that contains my reciept emails from my groceries shopping and then write the data into pandas
dataframes. The dataframes are then exported to my groceries database hosted on my Raspberry Pi.

The credentials for my outlook exchange account are stored in a .ini files. Also the host details and credentials for my database are also stored in 
a .ini file. The folder containing my groceries emails is hard coded. 

After processing the emails fill be moved to the processed subfoler

Structure of my email account:
root
└── inbox
    └── ASDA Order Receipts
        └── processed
"""
################################################################## Import libraries ##################################################################
from exchangelib import Credentials, Account, Folder, Message, EWSDateTime # excahangelib is used to connect to email account and extract emails
from requests_html import HTML #_________________________________# Used to convert the HTML body of the email to text
import configparser #____________________________________________# Used to read database and account credentials files
import datetime #________________________________________________# Used to convert dates and timestamps
import pandas as pd #____________________________________________# Used to create and manipulate data in the form of dataframe
import re #______________________________________________________# Used searching for patterns using regex and looking for patterns
from sqlalchemy import create_engine #___________________________# Used to create connection to postgres database

###################################################################### Fuctions ######################################################################
def connect_to_exchange():
    """
    Function to connect to microsoft exchange mail server based on credentials in exchange_credentials.ini file
    """
    # Importing account email address and password
    config = configparser.ConfigParser()
    config.read('exchange_credentials.ini')
    email_address = config['credentials']['email_address']
    password = config['credentials']['password']

    # Defining credentials for exchange account and setting account
    credentials = Credentials(email_address, password)
    account = Account(email_address, credentials = credentials, autodiscover = True)
    return account

def insert_order_num_col(df):
    """
    This function adds the order number to the beginning of a dataframe (df)
    """
    df = df.insert(0, 'order_number', order_number)
    return df

def convert_price_col(df, col_name):
    """
    This function casts the price column to a float
    """
    df[col_name] = pd.to_numeric(df[col_name], errors="raise", downcast="float")
    return df[col_name]

def convert_quant_col(df, col_name):
    """
    Ths function converts the quantity column to numeric values using the pandas method, to _numeric. 
    Since the quantity could be a weight with a kg at the end of the value, this function will result in that row becoming a NaN, 
    then converting this NaN to a value of one, before converting to an int.
    """
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
    df[col_name] = df[col_name].fillna(1)
    df[col_name] = df[col_name].astype('int')
    return df[col_name]

def calc_unit_price_col(df):
    """
    This function calculates a unit price column for the dataframe df
    """
    df['unit_price'] = df['price'] / df['quantity']
    return df['unit_price']

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

def insert_into_db():
    """
    This functions inserts the df created into the groceries database
    """
    df_order_details.to_sql('order_details', con = engine, if_exists='append', index=False)
    df_delivered.to_sql('delivered_items', con = engine, if_exists='append', index=False)
    if unavailable_present == True:
        df_unavail.to_sql('unavailable_items', con = engine, if_exists='append', index=False)
    else:
        print("No unavailable items to load to database")
    return print("Finished insert into database")

def remove_blank_and_headings(element):
    """Removes blank lines and heading titles from the categories.txt file from a list"""
    with open('categories.txt') as cat:
        categories = cat.read().splitlines()
    remove_list = ['Quantity', 'Price', None]
    # concat the categories list to the remove list
    remove_list = remove_list + categories
    if element in remove_list:
        return False
    else:
        return element

######################################## Set up connection to exchange and get items from ASDA receipt folder ########################################
account = connect_to_exchange()

receipt_folder = account.inbox / 'ASDA Order Receipts'

items = receipt_folder.all().order_by('datetime_received')

# Extract datetime_received, subject and body from each item
item_details = items.values('datetime_received', 'subject', 'body')

# For each item in folder we will process, insert into database and then move to 'processed' folder
email_datetime_list = []
order_number_list = []
for item in item_details:

    # grab datetime and append to date_time list
    email_datetime = item['datetime_received']
    email_datetime_list.append(email_datetime)

    # extract subject line, for branching  later
    subject = item['subject']

    # Convert body to lines
    body_raw = item['body']
    body_html = HTML(html = body_raw)
    body = body_html.find('tr')[0].text
    body = re.sub(r'[^\x00-\x7f]',r'', body)
    lines = body.splitlines()
    
    # Case for subject line of 'Your updated ASDA groceries order'
    if subject == 'Your updated ASDA Groceries order':
        # get order number and give error if no order number is found
        try:
            # order number is on line below line == 'Order Number'
            order_number = lines[lines.index('Order Number:') + 1]
        except:
            print("Order Number was not found")

        # get delivery date and give error if no delivery date is found
        try:
            # Delivery date is on line below 'Delivery Date:'
            delivery_date_str = lines[lines.index('Delivery Date:') + 1]
            # Converting delivery date to a date object
            delivery_date_str = delivery_date_str[0:11]
            delivery_date = datetime.datetime.strptime(delivery_date_str, '%d %b %Y').date()
        except:
            print("Delivery Date not found")

        # Get the total
        try:
             total_str = lines[lines.index('Total') + 1]
             total = float(total_str)
        except:
            print("total not found")

        # Get the subtotal
        try:
             subtotal_str = lines[lines.index('Subtotal*') + 5]
             subtotal = float(subtotal_str)
        except:
            print("subtotal not found")

        # Get the substitutes
        # Start_substitutes finds the index of the line containing the Substitutes header. Since there may not be substitutes
        # this is set up in a try, except format. the variable substitutions_present tracks if a file has subs or not
        try:
            start_substitutes = lines.index('Substitutes')
            # This groups the lines into a new substitutes list which is made up of a tuple of 4 elements
            # i is the first line with a substitute item, i+1 is the item being substituted, i+2 is the quantity and i+3 is the price
            i = start_substitutes + 3
            substitutes = []
            # loop will continue until it reaches an empty line after a price
            while len(lines[i]) > 0 :
                substitutes.append((lines[i], lines[i + 1][19:], lines[i + 2], lines[i + 3]))
                i += 4
            substitutions_present = True
        except:
            # if no line subsutitions then error will trigger 
            print("No substitutions")
            substitutions_present = False

        # find the start of the unavailable section and pack into a list of tuples
        try:
            start_unavailable = lines.index('Unavailable')
            i = start_unavailable + 3
            unavailable = []
            while len(lines[i]) > 0 :
                unavailable.append((lines[i], lines[i + 1], lines[i + 2]))
                i += 3
            unavailable_present = True
        except:
            print("No unavailable items")
            unavailable_present = False

        # Find the ordered items
        try:
            # We can find the start and end of the ordered section then create a list
            start_ordered = lines.index('Ordered')
            end_ordered = lines.index('Multibuy Savings')

            i = start_ordered + 3
            ordered = []
            while i < end_ordered :
                ordered.append(lines[i])
                i += 1
    
            # Remove blank list elements and headings
            ordered = list(filter(remove_blank_and_headings, ordered))

            # Create a list of tuples for the ordered items
            i = 0
            ordered_clean = []
            while i < len(ordered_items) :
                ordered_clean.append((ordered[i], ordered[i + 1], ordered[i + 2]))
                i += 3
        except:
            print("No ordered items found")

    elif subject == 'Order Receipt':
        # Order number may be referenced as Order Receipt, Order Number or something else
        try:
            # Look for order receipt
            order_number = body_lines[body_lines.index('Order Receipt:') + 1]
        except:
            try:
                # Look for Order Number
                order_number = body_lines[body_lines.index('Order Number:') + 1]
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

