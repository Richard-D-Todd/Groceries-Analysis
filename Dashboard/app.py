import dash
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
import configparser



app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.FLATLY])

def create_sql_engine():
    config = configparser.ConfigParser()
    config.read('../database.ini')
    username = config['postgresql']['user']
    password = config['postgresql']['password']
    database = config['postgresql']['database']
    host = config['postgresql']['host']
    con_string = 'postgresql+psycopg2://{}:{}@{}/{}?gssencmode=disable'.format(username, password, host, database)
    print(con_string)
    return create_engine(con_string)

# plotly template
template = 'seaborn'
server = app.server