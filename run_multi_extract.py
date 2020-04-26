import glob
import os
import email
from email.policy import default
from requests_html import HTML
import pandas as pd
import numpy as np
import datetime

directory = input("What is the path of the directory containing the email files?",)
files = glob.glob(directory + '\*.eml')

filepath_csv = input('Where do you want to output CSV files (directory)?',)

for file in files:
    # Get filename
    file_name = os.path.abspath(file)
    #Open eml email file
    with open(file_name, 'r') as file:
        msg = email.message_from_file(file, policy=default)

    # Extract body of email message and convert to HTML
    body = msg.get_payload(decode=True)
    html = HTML(html=body)
    match = html.find('tr')

    # Seperate email body into list of lines
    content = match[0].text
    lines = content.splitlines()

    # Extract the order number, delivery date, subtotal and total
    order_number_str = lines[1]
    delivery_date_str = lines[3]
    total_str = lines[lines.index('Total') + 1]
    subtotal_str = lines[lines.index('Subtotal*') + 5]

    # Converting strings above to other data types
    delivery_date_str = delivery_date_str[0:11]
    order_number = int(order_number_str)
    delivery_date = datetime.datetime.strptime(delivery_date_str, '%d %b %Y').date()

    #Converting Subtotal and total to float
    def convert_str_price_to_float(x):
        x = x[1:]
        return float(x)

    subtotal = convert_str_price_to_float(subtotal_str)
    total = convert_str_price_to_float(total_str)

    # Start_substitutes finds the index of the line containing the Substitutes header
    start_substitutes = lines.index('Substitutes')

    # This groups the lines into a new substitutes list which is made up of a tuple of 4 elements
    i = start_substitutes + 3
    substitutes = []
    while len(lines[i]) > 0 :
        substitutes.append((lines[i], lines[i + 1], lines[i + 2], lines[i + 3]))
        i += 4

    # finds unavailable section
    start_unavailable = lines.index('Unavailable')

    # This packs the unavailable section into a list of tuples
    i = start_unavailable + 3
    unavailable = []
    while len(lines[i]) > 0 :
        unavailable.append((lines[i], lines[i + 1], lines[i + 2]))
        i += 3

    # We can find the start and end of the ordered section
    start_ordered = lines.index('Ordered')

    end_ordered = lines.index('Multibuy Savings')

    # Creating a list for the ordered section
    i = start_ordered + 3
    ordered = []
    while i < end_ordered :
        ordered.append(lines[i])
        i += 1

    # Remove blank list elements
    ordered = list(filter(None, ordered))

    # Create a new list without the category headings
    categories = ['Chilled', 'Products By Weight', 'Frozen', 'Groceries, Health & Beauty and Household Items', 'Others', 'Other']
    ordered_items = []
    for element in ordered:
        if element in categories:
            pass
        else:
            ordered_items.append(element)

    # Create a list of tuples for the ordered items
    i = 0
    ordered_clean = []
    while i < len(ordered_items) :
        ordered_clean.append((ordered_items[i], ordered_items[i + 1], ordered_items[i + 2]))
        i += 3

    # Create substitutions dataframe
    df_subs = pd.DataFrame(substitutes, columns = ['Item', 'Substituting', 'Quantity', 'Price'])

    # Creating Unavailable items dataframe
    df_unavail = pd.DataFrame(unavailable, columns = ['Item', 'Quantity', 'Price'])

    # Creating ordered items dataframe
    df_ordered = pd.DataFrame(ordered_clean, columns = ['Item', 'Quantity', 'Price'])

    # Creating Dataframe for the order number, delivery date, subtotal and total
    order_dict = {'Order Number': order_number,'Delivery Date': delivery_date, 'Subtotal Price': subtotal, 'Total Price': total}
    df_order_details = pd.DataFrame.from_dict([order_dict])

    # Swap Price and quantity columns
    col_titles = ['Item', 'Substituting', 'Price', 'Quantity']
    df_subs = df_subs.reindex(columns=col_titles)

    # Insert Order Number Column
    def insert_order_num_col(df):
        df.insert(0, 'Order Number', order_number)
        
    insert_order_num_col(df_subs)

    # Remove the substitution for part of substituting column
    df_subs['Substituting'] = df_subs['Substituting'].str[15:]

    # define function to convert price from email to a float
    def convert_price_col(df, col_name):
        """
        This function converts a string price column that starts with a £ sign to a column with type float64.
        Param 1: df object
        Param 2: Column name with quotes
            """
        df[col_name] = df[col_name].str[1:]
        df[col_name] = df[col_name].apply(pd.to_numeric)
        
    convert_price_col(df_subs, 'Price')

    # Convert quantity to a integer
    df_subs['Quantity'] = pd.to_numeric(df_subs['Quantity'], errors="coerce")

    # Calculate Unit Price Column
    df_subs['Unit Price'] = df_subs['Price'] / df_subs['Quantity']

    df_subs.insert(2, 'Substitution', 1)

    # Swap price and quantity columns
    col_titles_unavail = ['Item', 'Price', 'Quantity']
    df_ordered = df_ordered.reindex(columns=col_titles_unavail)

    # Insert order number column
    insert_order_num_col(df_ordered)

    # Insert substitution column
    df_ordered.insert(2, 'Substitution', 0)

    # Insert Substituting column
    df_ordered.insert(3, 'Substituting', np.nan)

    # Convert Quantity to integer
    df_ordered['Quantity'] = pd.to_numeric(df_ordered['Quantity'], errors="coerce")

    # Convert price column to float
    convert_price_col(df_ordered, 'Price')

    # Calculate unit price
    df_ordered['Unit Price'] = df_ordered['Price'] / df_ordered['Quantity']

    # Joining ordered and substitution dataframes
    df_delivered = df_subs.append(df_ordered, ignore_index=True)

    df_unavail.insert(0, 'Order Number', order_number)

    # Convert quantity to a integer
    df_unavail['Quantity'] = pd.to_numeric(df_unavail['Quantity'], errors="coerce")

    df_unavail = df_unavail.drop(['Price'], axis=1)

    mean_unit_price = df_order_details.iloc[0, 3] / df_delivered['Quantity'].sum()
    count_ordered = pd.isna(df_delivered['Substituting']).sum()
    count_substituted = df_delivered['Substitution'].sum()
    count_delivered = len(df_delivered.index)
    sum_quantity = df_delivered['Quantity'].sum()
    count_unavailable = len(df_unavail.index)

    # Creating a list of values
    values = [mean_unit_price, count_ordered, count_substituted, count_delivered, sum_quantity, count_unavailable]

    #Creating list of Column names
    columns_list = ['Mean Unit Price', 'Count Ordered', 'Count Substituted', 'Count Delivered', 'Sum Quanitity', 'Count Unavailable']

    # Creating dictionary
    df_dict = {columns_list[i]: values[i] for i in range(len(values))}

    # Creating DataFrame
    df = pd.DataFrame([df_dict])

    df_order_details = pd.concat([df_order_details, df], axis=1)

    filename_delivered = filepath_csv + '\Delivered_Items_'+ str(delivery_date) + '.csv'

    df_delivered.to_csv(filename_delivered, index=False)
