import pandas as pd
from sqlalchemy import create_engine
import credentials
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import datetime
from dateutil.relativedelta import relativedelta

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

# Import data from database
# Import credentials to creat URI and then create engine
username = credentials.username
password = credentials.password
database = credentials.database
con_string = 'postgresql+psycopg2://{}:{}@localhost/{}?gssencmode=disable'.format(username, password, database)
print(con_string)
engine = create_engine(con_string)

# Creating dataframes from database tables ------------------------------------------------------------------------
df_order_details = pd.read_sql_table('order_details', con=engine)
df_delivered_items = pd.read_sql_table('delivered_items', con=engine)

# Setting calendar month on the order details dataframe
df_order_details['cal_month'] = df_order_details['delivery_date'].map(lambda x: x.strftime("%m-%Y"))

# Creating Period dataframe to create month column from pay dates --------------------------------------------------
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
years = ['2020', '2021', '2022', '2023', '2024', '2025']
months_years = []
for y in years:
    for m in months:
        months_years.append(m + '-' + y)

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

# Adding pay month to the order details  |----------------------------------------------------------------------------------
df_order_details['delivery_date'] = pd.to_datetime(df_order_details['delivery_date'])
df_order_details['pay_month'] = df_order_details['delivery_date'].apply(lambda x : df_period.iloc[df_period.index.get_loc(x)]['pay_month'])

# Calculating means |-------------------------------------------------------------------------------------------------------
# Average Order cost
mean_cost_per_order = df_order_details['total'].mean().round(decimals=2)

# Average cost per month (either calendar or pay month)
def mean_spend_by_month(month_col):
    """Calculate the mean for either the calendar month or pay month. The arguement should be the type of month"""
    if month_col == 'pay_month':
        df_pay_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
        df_pay_month = df_pay_month.groupby('pay_month').sum()
        # Removing the current incomplete month
        df_pay_month = df_pay_month.iloc[:-1]
        mean_spend_by_pay_month = df_pay_month.total.mean().round(decimals=2)
        return mean_spend_by_pay_month
    elif month_col == 'cal_month':
        df_cal_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'pay_month'])
        df_cal_month = df_cal_month.groupby('cal_month').sum()
        df_cal_month = df_cal_month.iloc[:-1]
        mean_spend_by_cal_month = df_cal_month.total.mean().round(decimals=2)
        return mean_spend_by_cal_month
    else:
        return None

mean_spend_by_pay_month = mean_spend_by_month('pay_month')
mean_spend_by_cal_month = mean_spend_by_month('cal_month')

# # Creating avg dataframe |-----------------------------------------------------------------------------------------------
# df = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
# df['total'] = df['total'].apply(pd.to_numeric)
# df['subtotal'] = df['subtotal'].apply(pd.to_numeric)
# df_monthly_avg = df.groupby('pay_month').mean()
# df_monthly_avg = df_monthly_avg.rename(columns={'total': 'avg_total', 'subtotal': 'avg_subtotal'})
# df_monthly_avg = df_monthly_avg[:-1]

# #  df_adjusted and df_monthly_avg dataframes
# df_pay_month = pd.concat([df_pay_month, df_monthly_avg], axis=1)
# df_pay_month = df_pay_month.reset_index()

# Queries----------------------------------------------------------------------------------------------------------
count_subs_by_date = """select od.delivery_date, count(di.substitution) as "count_subs"
                        from order_Details od
                        inner join delivered_items di
                        on od.order_number = di.order_number
                        where di.substitution = true
                        group by od.delivery_date
                        order by od.delivery_date asc"""
df1 = pd.read_sql_query(count_subs_by_date, con=engine).set_index('delivery_date')

count_ordered_by_date = """select od.delivery_date, count(di.substitution) as "count_ordered"
                            from order_details od
                            inner join delivered_items di
                            on od.order_number = di.order_number
                            where di.substitution = false
                            group by od.delivery_date
                            order by od.delivery_date asc"""
df2 = pd.read_sql_query(count_ordered_by_date, con=engine).set_index('delivery_date')

count_unavail_by_date = """select od.delivery_date, count(ui.id) as "count_unavailable"
                            from order_details od
                            inner join unavailable_items ui
                            on od.order_number = ui.order_number
                            group by od.delivery_date
                            order by od.delivery_date asc"""
df3 = pd.read_sql_query(count_unavail_by_date, con=engine).set_index('delivery_date')

#------------------| Graph 2 function |--------------------------------

# def create_graph_2():
#     """Create figure 2, the total cost of orders by month"""
#     # Group by pay month
#     df_pay_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
#     df_pay_month = df_pay_month.groupby('pay_month').sum()

#     # Removing the current incomplete month
#     df_pay_month = df_pay_month.iloc[:-1]

#     fig2 = px.bar(data_frame=df_pay_month,
#          x='pay_month',
#          y='total',
#          title='Total Spend per Month',
#         labels={'pay_month': 'Month', 'total': 'Amount / £',}
#         )

#     return fig2

# fig2 = create_graph_2()

# fig2.update_layout(clickmode='event+select')

#------------------| Graph 3 functions |------------------------------

def create_graph_3():
    df_combined = pd.concat([df1, df2, df3], axis=1, sort=True)
    df_combined['total_items'] = df_combined.sum(axis=1)
    df_combined = df_combined.reset_index()
    df_combined = df_combined.rename(columns = {'index':'delivery_date'})
    df_combined['substituted'] = df_combined['count_subs']/df_combined['total_items']
    df_combined['ordered'] = df_combined['count_ordered']/df_combined['total_items']
    df_combined['unavailable'] = df_combined['count_unavailable']/df_combined['total_items']
    df_combined = df_combined.drop(columns=['count_subs', 'count_ordered', 'count_unavailable', 'total_items'])
    fig3 = px.bar(data_frame=df_combined,
            x='delivery_date',
            y=['ordered', 'substituted', 'unavailable'],
            labels={'delivery_date': 'Delivery Date', 
            'value': 'Proportion'}
    )
    # Plot xaxis as discrete rather than continuous
    fig3.update_layout(xaxis_type='category')
    return fig3

fig3 = create_graph_3()



# App Layout --------------------------------------------------------------------------------------
app.layout = dbc.Container([

    html.H1("Groceries Dashboard", style={'textAlign': 'center'}),

    dbc.Row(
            dbc.Col(dcc.Graph(id='total_per_delivery', figure={}))
    ),

    dbc.Row([
            dbc.Col([
                    html.H3("Summary Details"),
                    dcc.Markdown("""
                         On average on order costs £{} and we spend £{} per month.
                         """.format(mean_cost_per_order, mean_spend_by_pay_month)),
                        html.Div(id="month_to_date", children=[])
            ]),
            dbc.Col([
                    # dcc.RadioItems(id="select_month_type",
                    # options=[
                    #     {'label': 'Calendar', 'value': 'calendar'},
                    #     {'label': 'Pay Period', 'value': 'pay'}
                    # ], value='pay', labelStyle={'display': 'inline-block'}),
                    
                    dbc.FormGroup([
                        dbc.Label("Month Type"),
                        dcc.RadioItems(id="select_month_type",
                        options=[
                            {'label': 'Calendar', 'value': 'calendar'},
                            {'label': 'Pay Period', 'value': 'pay'}
                        ], value='pay')
                    ]),

                    dcc.Graph(id='total_by_month', figure={}),
            ]),
    ]),

    dbc.Row(
            dbc.Col(dcc.Graph(id='proportion_sub', figure=fig3))
    )

    # html.Div([

    #     html.Div([
    #         html.H3("Summary Details"),
    #         dcc.Markdown("""
    #         On average on order costs £{} and we spend £{} per month.
    #         """.format(mean_cost_per_order, mean_spend_by_pay_month)),
    #         html.Div(id="month_to_date", children=[])
    #     ], style={'width': '40%', 'display': 'inline-block'}),


    #     html.Div([
            
            
    #         dcc.RadioItems(id="select_month_type",
    #         options=[
    #             {'label': 'Calendar', 'value': 'calendar'},
    #             {'label': 'Pay Period', 'value': 'pay'}
    #         ], value='pay', labelStyle={'display': 'inline-block'}), 
    #         dcc.Graph(id='total_by_month', figure={}),

    #     ], style={'width': '60%', 'display': 'inline-block'}),
        
    # ]),
    
    # html.Div(
    #     dcc.Graph(id='proportion_sub', figure=fig3)
    # )
])
# ----------------------------------------------------------------------------------
# Connect Plotly grpahs with dash components
@app.callback(
    Output(component_id='total_per_delivery', component_property='figure'),
    [Input(component_id='total_by_month', component_property='selectedData'),
    Input(component_id='select_month_type', component_property='value')]
)

def update_graph(selected, month_type):

    # If no bar clicked in the total by month graph clicked == None
    df = df_order_details
    
    # Extracting points from selection data
    if selected != None:
        selected_values = selected['points']
        selected_months = []
        i=0
        while i < len(selected_values):
            selected_months.append(selected_values[i]['x'])
            i+=1
    else:
        pass

    # fig1 total and subtotal of all deliveries -------------------------------------
    fig1 = px.bar(data_frame=df, 
            x='delivery_date',
            y='total',
            title='Total for Each Delivery',
            range_y=[0, 225],
            labels={'delivery_date': 'Delivery Date', 'total': 'Amount / £', 'subtotal': 'Amount / £'}
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
    fig1.update_traces(selectedpoints = selectedpoints , #marker= {'color': 'blue'}, 
    unselected={'marker': {'opacity': 0.5}}
        )
    return fig1

@app.callback(
    [Output(component_id='month_to_date', component_property='children'),
    Output(component_id='total_by_month', component_property='figure')],
    [Input(component_id='select_month_type', component_property='value')]
    )

def create_graph_2(month_type):
    """Create figure 2, the total cost of orders by month"""
    if month_type == 'pay':
        # Group by pay month
        df_pay_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'cal_month'])
        df_pay_month = df_pay_month.groupby('pay_month').sum()
        df_pay_month.reset_index(inplace=True)
        # Grab month to date
        month_to_date = df_pay_month['total'].iloc[-1]
        month_to_date_str = f'The month-to-date spend is £{month_to_date} (pay month)'
        # Removing the current incomplete month
        df_pay_month = df_pay_month.iloc[:-1]
        
        fig2 = px.bar(data_frame=df_pay_month,
            x='pay_month',
            y='total',
            title='Total Spend per Pay Month',
            labels={'pay_month': 'Month', 'total': 'Amount / £',}
            )
    else:
        # Group by cal month
        df_cal_month = df_order_details.drop(columns=['order_number', 'delivery_date', 'pay_month'])
        df_cal_month = df_cal_month.groupby('cal_month').sum()
        df_cal_month.reset_index(inplace=True)
        # Calculate month to date value
        month_to_date = df_cal_month['total'].iloc[-1]
        month_to_date_str = f'The month-to-date spend is £{month_to_date} (calendar month)'   
        # remove final incomplete month
        df_cal_month = df_cal_month.iloc[:-1]

        fig2 = px.bar(data_frame=df_cal_month,
        x='cal_month',
        y='total',
        title='Total Spend per Calendar Month',
        labels={'cal_month': 'Month', 'total': 'Amount / £'}
        )

    fig2.update_layout(clickmode='event+select')

    return month_to_date_str, fig2






# Launch Server --------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)

