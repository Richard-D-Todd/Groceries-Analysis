import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import datetime
from dateutil.relativedelta import relativedelta

from navbar import Navbar
from app import app, create_sql_engine, template

engine = create_sql_engine()

# Creating dataframes from database tables ------------------------------------------------------------------------
df_order_details = pd.read_sql_table('order_details', con=engine)
df_delivered_items = pd.read_sql_table('delivered_items', con=engine)

# Setting calendar month on the order details dataframe
df_order_details['cal_month'] = df_order_details['delivery_date'].map(lambda x: x.strftime("%Y-%m"))

# Creating Period dataframe to create month column from pay dates --------------------------------------------------
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
years = ['2020', '2021', '2022', '2023', '2024', '2025']
months_years = []
for y in years:
    for m in months:
        months_years.append(y + '-' + m)

start_date_1 = datetime.datetime.strptime('27/12/2019', '%d/%m/%Y')
start_date = [start_date_1]
i = 0
while len(start_date) < len(months_years):
    start_date.append(start_date[i] + relativedelta(months=1))
    i+=1

end_date_1 = datetime.datetime.strptime('26/01/2020', '%d/%m/%Y')
end_date = [end_date_1]
i = 0
while len(end_date) < len(months_years):
    end_date.append(end_date[i] + relativedelta(months=1))
    i+=1

df_period = pd.DataFrame(list(zip(months_years, start_date, end_date)), columns = ['pay_month', 'start_date', 'end_date'])
df_period.index = pd.IntervalIndex.from_arrays(df_period['start_date'],df_period['end_date'],closed='both')

#------------------------------| Adding pay month to the order details  |--------------------------
df_order_details['delivery_date'] = pd.to_datetime(df_order_details['delivery_date'])
df_order_details['pay_month'] = df_order_details['delivery_date'].apply(lambda x : df_period.iloc[df_period.index.get_loc(x)]['pay_month'])

# Calculating means |------------------------------------------------------------------------------
# Average Order cost
mean_cost_per_order = df_order_details['total'].mean().round(decimals=2)

# Queries |----------------------------------------------------------------------------------------
proportion_query = """
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
df_counts = pd.read_sql_query(proportion_query, con=engine)

#---------------------------| Create Proportions dataframe for graph 3 |---------------------------

df_prop = df_counts.copy()
df_prop['total'] = df_prop.sum(axis=1)
df_prop['substituted'] = df_prop['substituted']/df_prop['total']
df_prop['available'] = df_prop['available']/df_prop['total']
df_prop['unavailable'] = df_prop['unavailable']/df_prop['total']

#----------------------------------------| app layout |--------------------------------------------
nav = Navbar()

body = dbc.Container([

    html.H1("Orders Overview", style={'textAlign': 'center'}),

    dbc.Row(
            dbc.Col(dcc.Graph(id='total_per_delivery', figure={}))
    ),

    dbc.Row([
            dbc.Col([
                    html.H3("Summary Details"),
                    
                    dbc.Alert(id="month_to_date", color="primary"),

                    dbc.Card(
                        dbc.CardBody([
                            html.H4('£ {}'.format(mean_cost_per_order), className="card-title"),
                            html.H6("The average cost of an order", className="card-subtitle"),
                        ])
                    ),                    
                    
                    dbc.Card(
                        dbc.CardBody([
                            #html.H4('£ {}'.format(mean_spend_by_pay_month), className="card-title"),
                            html.H4(id ='monthly_average'), #className="card-title"),
                            html.H6("The average spend per month", className="card-subtitle"),
                        ])
                    ),
                    html.Br(),
                    html.Label("Month Type"),
                    dcc.RadioItems(id="select_month_type",
                    options=[
                        {'label': 'Calendar', 'value': 'calendar'},
                        {'label': 'Pay Period', 'value': 'pay'}
                    ], value='pay', labelStyle={'display': 'block'}),  

            ], width=3),
            dbc.Col([
                    dcc.Graph(id='total_by_month', figure={})      
            ], width=9),
    ]),

    dbc.Row(
        dbc.Col(
            dbc.Tabs([
                dbc.Tab(label="Compact", tab_id='compact'),
                dbc.Tab(label="Time Series", tab_id='time-series'),
            ], id='tabs', active_tab='compact')
        )
    ),

    dbc.Row(
        dbc.Col(
            dcc.Graph(id='proportion_sub', figure={})
        )
    )
    ])

layout = html.Div([
    nav,
    body
    ])

#----------------------------------------| Callbacks |---------------------------------------------
@app.callback(
    Output(component_id='total_per_delivery', component_property='figure'),
    [Input(component_id='total_by_month', component_property='selectedData'),
    Input(component_id='select_month_type', component_property='value')]
)

def create_graph_1(selected, month_type):
    # Copying df_order_details dataframe. We only want the delivery date and the total
    df = df_order_details
 
     # Calculate the 3 order rolling mean
    df['rolling_mean'] = df.total.rolling(window=3).mean()
    
    # Extracting points from selection data
    if selected != None:
        selected_values = selected['points']
        selected_months = []
        i=0
        while i < len(selected_values):
            # From the selected data I only want the year and month part, not the day
            selected_months.append(selected_values[i]['x'][:-3])
            i+=1
    else:
        pass

    # fig1 total of all deliveries -------------------------------------
    fig1 = px.bar(data_frame=df, 
            x='delivery_date',
            y='total',
            title='Total for Each Delivery',
            range_y=[0, 225],
            labels={'delivery_date': 'Delivery Date', 'total': 'Amount / £', 'subtotal': 'Amount / £'},
            template=template
            )
    # Add 3 order rolling mean line
    fig1.add_trace(
        go.Scatter(x = df['delivery_date'], y=df['rolling_mean'], name = '2 order rolling average')
    )
    # Make ticks on x axis for each month
    fig1.update_xaxes(
        dtick = "M1",
        tickformat = "%b\n%Y"
    )
  
    # Function to find the indices for the selected month, based on if the month type is set as calendar or pay month
    def indices_from_selected_months(month_type):
        if month_type == 'pay':
            return df.index[df['pay_month'].isin(selected_months)]
        else:
            return df.index[df['cal_month'].isin(selected_months)]

    # extracting selectedpoints (int index) from the selected months data
    if selected != None:
        selectedpoints = indices_from_selected_months(month_type)
    else:
        selectedpoints = df.index

    # Updating figure when points are selected
    fig1.update_traces(selectedpoints = selectedpoints, unselected={'marker': {'opacity': 0.5}})
    return fig1

@app.callback(
    [Output(component_id='monthly_average', component_property='children'),
    Output(component_id='month_to_date', component_property='children')],
    [Input(component_id='select_month_type', component_property='value')]
    )

# Average cost per month (either calendar or pay month)
def mean_by_month(month_type):
    """Calculate the mean for either the calendar month or pay month. The arguement should be the type of month"""
    if month_type == 'pay':
        # Average spend by month
        df_pay_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
        df_pay_month = df_pay_month.groupby('pay_month').sum()
        # Removing the current incomplete month
        df_pay_month = df_pay_month.iloc[:-1]
        mean_spend_by_month = df_pay_month.total.mean().round(decimals=2)
        mean_spend_by_month_str = f"£{mean_spend_by_month}" 
        
         #month to date spend
        month_to_date = df_pay_month['total'].iloc[-1]
        month_to_date_str = f'The month-to-date spend is £{month_to_date} (pay month)'

    elif month_type == 'calendar':
        # Average per month
        df_cal_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'pay_month'])
        df_cal_month = df_cal_month.groupby('cal_month').sum()
        df_cal_month = df_cal_month.iloc[:-1]
        mean_spend_by_month = df_cal_month.total.mean().round(decimals=2)
        mean_spend_by_month_str = f"£{mean_spend_by_month}"

        # Month to date
        month_to_date = df_cal_month['total'].iloc[-1]
        month_to_date_str = f'The month-to-date spend is £{month_to_date} (calendar month)' 
    
    return mean_spend_by_month_str, month_to_date_str

@app.callback(
    Output(component_id='total_by_month', component_property='figure'),
    [Input(component_id='select_month_type', component_property='value')]
    )

def create_graph_2(month_type):
    """Create figure 2, the total cost of orders by month"""

    # Graph when month set to pay month
    if month_type == 'pay':
        # Group by pay month
        df_pay_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
        df_pay_month = df_pay_month.groupby('pay_month').sum()
        df_pay_month.reset_index(inplace=True)

        # 3 month rolling average by month
        df_pay_month['rolling_mean'] = df_pay_month['total'].rolling(window = 3).mean()
        # setting the colours so that the last bar is a different colour to the other bars
        colours = ['rgb(76,114,176)'] * len(df_pay_month)
        colours[-1] = 'rgb(221,132,82)'
        
        fig2 = px.bar(data_frame=df_pay_month,
            x='pay_month',
            y='total',
            title='Total Spend per Pay Month, Current Month in Orange',
            labels={'pay_month': 'Month', 'total': 'Amount / £',},
            template=template,
            )
        fig2.add_trace(go.Scatter(x = df_pay_month['pay_month'], y = df_pay_month['rolling_mean'], name = '3 month rolling average', mode = 'lines'))
            
    # Graph when month set to calendar month 
    else:
        # Group by cal month
        df_cal_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'pay_month'])
        df_cal_month = df_cal_month.groupby('cal_month').sum()
        df_cal_month.reset_index(inplace=True)
          
        # 3 month rolling average by cal month
        df_cal_month['rolling_mean'] = df_cal_month['total'].rolling(window = 3).mean()
        # setting the colours so that the last bar is a different colour to the other bars
        colours = ['rgb(76,114,176)'] * len(df_cal_month)
        colours[-1] = 'rgb(221,132,82)'

        fig2 = px.bar(data_frame=df_cal_month,
        x='cal_month',
        y='total',
        title='Total Spend per Calendar Month, Current Month in Orange',
        labels={'cal_month': 'Month', 'total': 'Amount / £'},
        template=template
        )
        fig2.add_trace(go.Scatter(x = df_cal_month['cal_month'], y = df_cal_month['rolling_mean'], name = '3 month rolling average', mode = 'lines'))
    # Make ticks on x axis for each month
    fig2.update_xaxes(dtick = "M1", tickformat = "%b\n%Y")
    fig2.update_traces(marker_color=colours)
    fig2.update_layout(clickmode='event+select')
    
    return fig2

@app.callback(
    Output(component_id='proportion_sub', component_property='figure'),
    [Input(component_id='tabs', component_property='active_tab')]
)

def create_graph_3(active_tab):
    df = df_prop.copy()
    
    if active_tab == 'compact':
        # convert delivery date to string with format dd-mm-yyyy
        df['delivery_date'] = pd.to_datetime(df['delivery_date'])
        df['delivery_date'] = df['delivery_date'].dt.strftime('%d-%m-%Y')
        
    elif active_tab == 'time-series':
        pass
    
    fig3 = px.bar(data_frame=df,
            x='delivery_date',
            y=['available', 'substituted', 'unavailable'],
            labels={'delivery_date': 'Delivery Date', 
            'value': 'Proportion',
            'variable': 'Item Availability'},
            color_discrete_map={
            "available": 'rgb(85,168,104)',
            "substituted": 'rgb(221,132,82)',
            "unavailable": 'rgb(196,78,82)'
            },
            template=template,            
    )
    fig3.update_xaxes(dtick = "M1", tickformat = "%b\n%Y")
    fig3.update_layout(legend={
        'orientation': 'h',
        'yanchor': 'bottom',
        'y': 1})

    return fig3