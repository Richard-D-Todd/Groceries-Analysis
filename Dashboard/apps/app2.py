import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table
import datetime

from navbar import Navbar
from app import app, create_sql_engine, template

engine = create_sql_engine()

nav = Navbar()

# Query to import the delivered items along with the delivery date
query = """
select od.delivery_date, item, substitution, price, quantity, unit_price
from delivered_items di
left join order_details od
on od.order_number = di.order_number
order by od.delivery_date
"""

df = pd.read_sql_query(query, con=engine)

df_order_details = pd.read_sql_table('order_details', con=engine)
print(df_order_details)

# function to create the dropdown options from the delivery date
def create_dropdown_options():
    df = df_order_details
    # convert delivery_date to string
    df['delivery_date'] = df['delivery_date'].dt.strftime('%d-%m-%Y')
    options = []
    for x in df['delivery_date']:
        pair = {'label': x, 'value': x}
        options.append(pair)
    return options

options = create_dropdown_options()
# set the fdefault value for the dropdown as the last value in the list
value = options[-1]['value']

body = dbc.Container([
    html.H1("Order Details", style={'textAlign':'center'}),

    dbc.Row([
        dbc.Col([
            dbc.Label("Select Order:"),
            dcc.Dropdown(id="select_order",
                options=options,
                value =value)
        ], width=3),
        dbc.Col(
            dbc.Alert(id="order_total", color="primary"), width=3
        ),
    ]),
    

    html.Div(id="order_table")    






])

layout = html.Div([
    nav,
    body
])

# ----------------------------------------------------------------------------------
@app.callback(
    Output(component_id="order_total", component_property='children'),
    [Input(component_id="select_order", component_property='value')]
)

def get_total_for_order(select_order):
    #print("select order: {}".format(select_order))
    df = df_order_details
    total = df['total'][df['delivery_date'] == select_order]
    ind = df.index[df['delivery_date'] == select_order][0]
    total = total[ind]
    total_str = "Order Total: £{}".format(total)
    return total_str
    
@app.callback(
    Output(component_id="order_table", component_property='children'),
    [Input(component_id="select_order", component_property='value')]
)

def create_order_table(select_order):
    dff = df.copy()
    # convert delivery date to timestamp to change format
    dff['delivery_date'] = pd.to_datetime(dff['delivery_date'])
    dff['delivery_date'] = dff['delivery_date'].dt.strftime('%d-%m-%Y')
    dff = dff[dff['delivery_date'] == select_order]
        
    # change column names
    dff.rename(columns={'delivery_date': 'Delivery Date', 'item': 'Item', 'substitution': 'Substitution', 'price': 'Price / £', 'quantity': 'Quantity', 'unit_price': 'Unit Price / £'}, inplace=True)
    table = dash_table.DataTable(
        
        #columns=[{"name": i, "id": i} for i in dff.columns],
        columns=[{"name": i, "id": i} for i in dff.columns],
        data=dff.to_dict('records'),
        sort_action='native',
        filter_action='native',
        page_action='native',
        page_current= 0,
        page_size= 10,
    )
    return table