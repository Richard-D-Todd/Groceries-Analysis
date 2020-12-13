import dash
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
import configparser
import dash_auth

with open(r'C:\Users\Richard\Documents\Programming and Data Science\Github\Extract-Email\Dashboard\username_password.txt') as f:
    pair = f.read().splitlines()
    VALID_USERNAME_PASSWORD_PAIRS = {pair[0] : pair[1]}
    print(VALID_USERNAME_PASSWORD_PAIRS)

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.FLATLY])
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
def create_sql_engine():
    config = configparser.ConfigParser()
    config.read('../database.ini')
    username = config['postgresql']['user']
    password = config['postgresql']['password']
    database = config['postgresql']['database']
    con_string = 'postgresql+psycopg2://{}:{}@localhost/{}?gssencmode=disable'.format(username, password, database)
    print(con_string)
    return create_engine(con_string)

# plotly template
template = 'seaborn'
server = app.server