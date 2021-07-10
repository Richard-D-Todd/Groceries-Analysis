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
    con_string = 'postgresql+psycopg2://{}:{}@{}/{}'.format(username, password, host, database)
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
    remove_list = ['Quantity', 'Price', None, '']
    # concat the categories list to the remove list
    remove_list = remove_list + categories
    if element in remove_list:
        return False
    else:
        return element

def remove_blank_and_price_quantity_labels(ls):
    """Removes blank lines and the quantity and price headings."""
    remove_list = ['Quantity', 'Price', None, '']
    new_list = [element for element in ls if element not in remove_list]
    return new_list

######################################## Set up connection to exchange and get items from ASDA receipt folder ########################################
account = connect_to_exchange()

receipt_folder = account.inbox / 'ASDA Order Receipts'

items = receipt_folder.all().order_by('datetime_received')

# If there are no items in the 'ASDA Order Receipts folder then print below
if len(items) == 0:
    print("No new emails found in Order Receipts folder")

# Continue with processsing if emails are present
else:
    # Connect to database
    engine = create_sqlalchemy_engine()

    # Extract datetime_received, subject and body from each item
    item_details = items.values('datetime_received', 'subject', 'body')

    # For each item in folder we will process, insert into database and then move to 'processed' folder
    email_datetime_list = []
    order_number_list = []
    item_num = 1
    num_emails = len(list(item_details))
    for item in item_details:
        # grab datetime and append to date_time list
        email_datetime = item['datetime_received']
        email_datetime_list.append(email_datetime)

        email_datetime_str = email_datetime.strftime("%Y-%m-%d")
        print(f"Start Processing file {item_num} out of {num_emails}\nemail recieved on {email_datetime_str}")

        # extract subject line, for branching  later
        subject = item['subject']

        # Convert body to lines
        body_raw = item['body']
        body_html = HTML(html = body_raw)
        body = body_html.find('tr')[0].text
        body = re.sub(r'[^\x00-\x7f]',r'', body)
        lines = body.splitlines()
        
        # Extract the data from each email. The method changes depending on the subject of the email
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
            # Remove reference to 'You still get your discount' if present
            for line in lines:
                if line == "You still get your discount":
                    lines.pop(lines.index(line))
                else:
                    continue

            # Order number may be referenced as Order Receipt, Order Number or something else
            try:
                # Look for order receipt
                order_number = lines[lines.index('Order Receipt:') + 1]
            except:
                try:
                    # Look for Order Number
                    order_number = lines[lines.index('Order Number:') + 1]
                except:
                    # May also have order number trailing order on the same line
                    for line in lines:
                        order_number = re.match("Order\s\d+", line)
                        if order_number != None:
                            break
                        else:
                            continue
                    order_number = order_number.group(0)
                    order_number = re.split("\s", order_number)[1]

            # Get total
            try:
                total_str = lines[lines.index('Order total') + 1]
                total = float(total_str)
            except:
                print("No total found")
            
            # Get subtotal
            try:
                subtotal_str = lines[lines.index('Groceries') + 1]
                subtotal = float(subtotal_str)
            except:
                print("No subtotal found")
            
            # Get delivery date from the email datetime
            delivery_date = email_datetime.date()

            we_sent_lines = []
            not_available_lines = []
            i = 0
            subs_end = lines.index('Your order')

            # Checking for substitutions and unavailable items
            while i < subs_end :
                if lines[i] == 'We sent':
                    we_sent_lines.append(i)
                    i += 1
                elif lines[i] == 'Not available':
                    not_available_lines.append(i)
                    i += 1
                else:
                    i += 1

            # Create substitutes list if substitutes are present
            if len(we_sent_lines) > 0:
                substitutes = []
                # lines[i - 2] gives the original item, lines[i + 1], gives the substitution
                # retrieveing the first character, lines[i + 1][0], gives the quantity
                # line[i + 2] gives the price
                for i in we_sent_lines:
                    substitutes.append((lines[i + 1][4:], lines[i - 2][4:], lines[i + 1][0], lines[i + 2]))
                    substitutions_present = True  
            else:
                substitutions_present = False

            # Create unavailable list if unavailable itemss are present
            if len(not_available_lines) > 0:
                unavailable = []
                for i in not_available_lines:
                    # lines[i - 1] gives the unavailable item
                    # lines[i - 1][0] gives the first character which is the quantity
                    # lines[i + 1] gives the price
                    unavailable.append((lines[i - 1][4:], lines[i - 1][0], lines[i + 1])) 
                unavailable_present = True
            else:
                unavailable_present = False   

            # Create ordered items list
            ordered_start = lines.index('Your order')
            ordered_end = lines.index('Groceries')
            ordered = []
            i = ordered_start + 1

            while i < ordered_end:
                ordered.append(lines[i])
                i += 1

            # Get categories headings by looking at line above "Quantity" line. Then remove heading
            for index, line in enumerate(ordered):
                if line == "Quantity":
                    heading_index = index - 1
                    ordered.pop(heading_index)

            # Removing blank lines and headings
            ordered = remove_blank_and_price_quantity_labels(ordered)

            # Create a list of tuples for the ordered items
            i = 0
            ordered_clean = []

            while i < len(ordered) :
                ordered_clean.append((ordered[i], ordered[i + 1], ordered[i + 2]))
                i += 3

        else:
            print('Subject of email not recognised')

        try:
            # Create a dictionary to store the order details
            order_dict = {'order_number': order_number,'delivery_date': delivery_date, 'subtotal': subtotal, 'total': total}

            # Create and format the substitutions dataframe
            if substitutions_present == True:
                df_subs = pd.DataFrame(substitutes, columns = ['item', 'substituting', 'quantity', 'price'])
                col_titles_sub = ['item', 'substituting', 'price', 'quantity']
                df_subs = df_subs.reindex(columns=col_titles_sub)
                insert_order_num_col(df_subs)
                df_subs.insert(2, 'substitution', True)  
                convert_price_col(df_subs, 'price')
                convert_quant_col(df_subs, 'quantity')
                calc_unit_price_col(df_subs)
            else:
                pass

            # Create and format the unavailable items dataframe
            if unavailable_present == True:
                df_unavail = pd.DataFrame(unavailable, columns = ['item', 'quantity', 'price'])
                insert_order_num_col(df_unavail)
                convert_quant_col(df_unavail, 'quantity')
                df_unavail = df_unavail.drop(['price'], axis=1)
            else:
                pass

            # Create ordered and order details DataFrames 
            df_order_details = pd.DataFrame.from_dict([order_dict])
            df_order_details['delivery_date'] = pd.to_datetime(df_order_details['delivery_date'])

            # Swap price and quantity columns for the ordered df
            df_ordered = pd.DataFrame(ordered_clean, columns = ['item', 'quantity', 'price'])
            col_titles_ordered = ['item', 'price', 'quantity']
            df_ordered = df_ordered.reindex(columns=col_titles_ordered)

            # Formatting the ordered items df
            insert_order_num_col(df_ordered) # insert the order number at the start of the df
            df_ordered.insert(2, 'substitution', False) # insert a substitution column with False as the values
            df_ordered.insert(3, 'substituting', 'None') # insert a substitution column with the string None as the values
            convert_price_col(df_ordered, 'price') # convert price column to float
            convert_quant_col(df_ordered, 'quantity') # convert quantity column to int
            calc_unit_price_col(df_ordered) # calculate the unit price for each row

            # Joining ordered and substitution dataframes (if substitution df exists)
            if substitutions_present == True:
                df_delivered = df_subs.append(df_ordered, ignore_index=True)
            else:
                df_delivered = df_ordered

            print(f"Dataframes created for file {item_num} out of {num_emails}")
        except:
            print(f"failed to create dataframes")
        # Insert dataframes into the database

        insert_into_db()

        # Move email to 'processed' folder
        processed_folder = receipt_folder / 'processed'
        items[0].move(processed_folder)
        print(f"Email moved to processed folder for file {item_num} out of {num_emails}")
        item_num += 1

    print("all files processed")