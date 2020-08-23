import dash
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine
import credentials

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.FLATLY])

def create_sql_engine():
    username = credentials.username
    password = credentials.password
    database = credentials.database
    con_string = 'postgresql+psycopg2://{}:{}@localhost/{}?gssencmode=disable'.format(username, password, database)
    print(con_string)
    return create_engine(con_string)

# plotly template
template = 'seaborn'
server = app.server