import dash
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from navbar import Navbar
from app import create_sql_engine

engine = create_sql_engine()

# Creating datframe for order totals
df_order_details = pd.read_sql_table('order_details', con=engine)
df_order_details['cum_total'] = df_order_details['total'].cumsum()

fig_cum_total = px.area(
    data_frame=df_order_details,
    x = 'delivery_date',
    y = 'cum_total',
    labels = {
        'delivery_date' : 'Delivery Date',
        'cum_total' : 'Cumulative Total Spend / £'
    }
)

nav = Navbar()

body = dbc.Container(
    [
        html.H1("Groceries Dashboard", style={'textAlign': 'center'}),
       dbc.Row(
           [
               dbc.Col(
                  [
                     html.H3("Introduction", style={'textAlign': 'center'}),
                     dcc.Markdown(
                        """
                        This dashboard is to track my regular groceries shop at ASDA online. The code for this project can be found on my GitHub here.

                        I have also been documenting the development of this project through my website:

                        The dashboard is made of the following views:

                        1. __Orders Overview__
                        Total for each delivery, the total spend per month and the proportion of each delivery that is substituted and unavailable.

                        2. __Order Details__
                        The order details for a selected order, along with the count of substitutions and unavailable items.

                        3. __Spending Overview__
                        The most expensive and common items, along with other insights into spending habits.
                        """
                           )
                   ],
                  md=4,
               ),
              dbc.Col(
                 [
                     html.H3("Summary", style={'textAlign': 'center'}),
                     dcc.Graph(figure=fig_cum_total),
                        ]
                     ),
                ]
            )
       ],
className="mt-4",
)

layout = html.Div([
    nav,
    body
])

