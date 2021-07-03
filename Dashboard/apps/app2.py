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

template = template

# Query to import the delivered items along with the delivery date
q1 = """
select od.delivery_date, item, substitution, price, quantity, unit_price
from delivered_items di
left join order_details od
on od.order_number = di.order_number
order by od.delivery_date
"""

# Query to import the count of ordered, substituted and unavailable items
q2 = """
select x.delivery_date, available, substituted, unavailable
from(
	select i.delivery_date, available, substituted
	from(
		select od.delivery_date, count(di.substitution) as available
		from order_Details od
		inner join delivered_items di
		on od.order_number = di.order_number
		where di.substitution = false
		group by od.delivery_date
		order by od.delivery_date asc
	) as i
	left join
	(
		select od.delivery_date, count(di.substitution) as substituted
		from order_details od
		inner join delivered_items di
		on od.order_number = di.order_number
		where di.substitution = true
		group by od.delivery_date
		order by od.delivery_date asc
	) as j on i.delivery_date = j.delivery_date
) as x
left join
(
select od.delivery_date, count(ui.id) as unavailable
from order_details od
inner join unavailable_items ui
on od.order_number = ui.order_number
group by od.delivery_date
order by od.delivery_date asc
) as y on x.delivery_date = y.delivery_date;
"""
# function to create the dropdown options from the delivery date
def create_dropdown_options():
    df= pd.read_sql_table('order_details', con=engine)
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

        html.Div(id="order_table")
    ]),

      
    html.Div(dcc.Graph(id="counts", figure={})),

    html.Div(dcc.Graph(id="proportions", figure={}))
])

layout = html.Div([
    nav,
    body,
    dcc.Interval(
        id='interval_component',
        interval=3600000, #1 hour in milliseconds
        n_intervals=0
    )
])

# ----------------------------------------------------------------------------------
@app.callback(
    Output(component_id="order_total", component_property='children'),
    [Input(component_id="select_order", component_property='value'),
    Input(component_id='interval_component', component_property='n_intervals')]
)

def get_total_for_order(select_order,n):
    df = pd.read_sql_table('order_details', con=engine)
    total = df['total'][df['delivery_date'] == select_order]
    ind = df.index[df['delivery_date'] == select_order][0]
    total = total[ind]
    total_str = f"Order Total: £{total:.2f}"
    return total_str
    
@app.callback(
    Output(component_id="order_table", component_property='children'),
    [Input(component_id="select_order", component_property='value'),
    Input(component_id='interval_component', component_property='n_intervals')]
)

def create_order_table(select_order, n):
    df = pd.read_sql_query(q1, con=engine)
    # convert delivery date to timestamp to change format
    df['delivery_date'] = pd.to_datetime(df['delivery_date'])
    df['delivery_date'] = df['delivery_date'].dt.strftime('%d-%m-%Y')
    df = df[df['delivery_date'] == select_order]
        
    # change column names
    df.rename(columns={'delivery_date': 'Delivery Date', 'item': 'Item', 'substitution': 'Substitution', 'price': 'Price / £', 'quantity': 'Quantity', 'unit_price': 'Unit Price / £'}, inplace=True)
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        sort_action='native',
        filter_action='native',
        page_action='native',
        page_current= 0,
        page_size= 10,
    )
    return table

@app.callback(
    [Output(component_id="counts", component_property='figure'),
    Output(component_id="proportions", component_property='figure')],
    [Input(component_id="select_order", component_property='value'),
    Input(component_id='interval_component', component_property='n_intervals')]
)

def create_count_and_proportion_graphs(select_order, n):
    df = pd.read_sql_query(q2, con=engine)

    df['delivery_date'] = pd.to_datetime(df['delivery_date'])
    df['delivery_date'] = df['delivery_date'].dt.strftime('%d-%m-%Y')
    df = df[df['delivery_date'] == select_order]
    df['total'] = df.sum(axis=1)

    df = df.melt(id_vars=['delivery_date'], value_vars=['total', 'available', 'substituted', 'unavailable'], var_name='type', value_name='count')
  
    # colours
    colours_fig1 = ['rgb(196,78,82)', 'rgb(221,132,82)', 'rgb(85,168,104)', 'rgb(76,114,176)']
    fig1 = px.bar(data_frame=df,
            x='count',
            y='type',
            orientation="h",
            template=template,
            labels={'count': 'Count', 'type': 'Item Availability'},
            color='type',
            color_discrete_map={
                "total": 'rgb(76,114,176)',
                "available": 'rgb(85,168,104)',
                "substituted": 'rgb(221,132,82)',
                "unavailable": 'rgb(196,78,82)'
            }
            )
    fig1.update_layout(showlegend=False)

    # colours
    colours_fig2 = ['rgb(85,168,104)', 'rgb(221,132,82)', 'rgb(196,78,82)']

    dff = df.copy()
    dff = dff[dff['type'] != 'total']
    dff['proportion'] = dff['count']/dff['count'].sum()
   
    fig2 = px.bar(
        data_frame=dff,
        x='proportion',
        y='delivery_date',
        barmode='stack',
        template=template,
        color='type',
        color_discrete_map={
            "available": 'rgb(85,168,104)',
            "substituted": 'rgb(221,132,82)',
            "unavailable": 'rgb(196,78,82)'
                },
        labels={
            'type': 'Item Availability',
            'proportion': 'Proportion'
        },
        height=250,
        range_x=[0,1]
    )

    fig2.update_yaxes(zeroline=False, visible=False)
    fig2.update_layout(legend={
        'orientation': 'h',
        'yanchor': 'bottom',
        'y': 1})
   
    return fig1, fig2