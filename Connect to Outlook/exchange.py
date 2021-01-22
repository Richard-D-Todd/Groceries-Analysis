from exchangelib import Credentials, Account, Folder, Message, EWSDateTime
from requests_html import HTML
import configparser
import datetime


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
messages = receipt_folder.all().order_by('-datetime_received')


