import pandas as pd
from sqlalchemy import create_engine
import credentials
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import datetime
from dateutil.relativedelta import relativedelta

app = dash.Dash(__name__)

# Import data from database
# Import crednetials to creat URI and then create engine
username = credentials.username
password = credentials.password
database = credentials.database
con_string = 'postgresql+psycopg2://{}:{}@localhost/{}?gssencmode=disable'.format(username, password, database)
print(con_string)
engine = create_engine(con_string)

# Creating dataframes from queries
q1 = "select * from order_details"
q2 = "select * from delivered_items"

df_order_details = pd.read_sql_table('order_details', con=engine)
df_delivered_items = pd.read_sql_table('delivered_items', con=engine)

#------------------Test df manipulations--------------------------------

#  creating period df
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
df_period = pd.DataFrame(list(zip(months_years, start_date, end_date)), columns = ['month', 'start_date', 'end_date'])
df_period.index = pd.IntervalIndex.from_arrays(df_period['start_date'],df_period['end_date'],closed='both')

# App Layout -----------------------------------------------------
app.layout = html.Div([

    html.H1("Groceries Dashboard"),

    html.H2("Total and Subtotal for Each Delivery"),

    dcc.RadioItems(id="select_total",
        options=[
            {'label': 'subtotal', 'value': 'subtotal'},
            {'label': 'total', 'value': 'total'},
            {'label': 'both', 'value': 'both'}
        ],
        value='both'
    ),

    html.Div(id='output_container', children=[]),
    html.Br(),

    dcc.Graph(id='total_per_delivery', figure={}),

    html.H2("By Month"),

    dcc.Graph(id='total_by_month', figure={})
])
# ----------------------------------------------------------------------------------
# Connect Plotly grpahs with dash components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
    Output(component_id='total_per_delivery', component_property='figure'),
    Output(component_id='total_by_month', component_property='figure')
    ],
    [Input(component_id='select_total', component_property='value')]
)

def update_graph(option_selected):
    print(option_selected)
    print(type(option_selected))

    container = "The graph is showing the: {}".format(option_selected)

    # fig1 total and subtotal of all deliveries -------------------------------------
    if option_selected == 'both':
        fig1 = px.bar(data_frame=df_order_details, 
            x='delivery_date',
            y=['total', 'subtotal'],
            barmode='group',
            range_y=[0, 225],
            labels={'delivery_date': 'Delivery Date', 'value': 'Amount / £'}
            )
    else:
            fig1 = px.bar(data_frame=df_order_details, 
            x='delivery_date',
            y=option_selected,
            range_y=[0, 225],
            labels={'delivery_date': 'Delivery Date', 'total': 'Amount / £', 'subtotal': 'Amount / £'}
            )
    

    # fig2 total by pay month -------------------------------------------------------

    #  creating period df
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
    df_period = pd.DataFrame(list(zip(months_years, start_date, end_date)), columns = ['month', 'start_date', 'end_date'])
    df_period.index = pd.IntervalIndex.from_arrays(df_period['start_date'],df_period['end_date'],closed='both')

    # create copy of order details dataframe and join it with the period dataframe
    df_copy = df_order_details.copy()
    df_copy['delivery_date'] = pd.to_datetime(df_copy['delivery_date'])
    df_copy['month'] = df_copy['delivery_date'].apply(lambda x : df_period.iloc[df_period.index.get_loc(x)]['month'])
    df_merged = df_copy.merge(df_period, how='inner', on='month')
    df_adjusted = df_merged.groupby('month').sum()
    df_adjusted = df_adjusted
    # Removing the current incomplete month
    df_adjusted = df_adjusted.iloc[:-1]
    # Creating avg dataframe to add to color
    dff_merged = df_merged = df_merged.drop(columns=['order_number', 'delivery_date', 'start_date', 'end_date'])
    dff_merged['total'] = dff_merged['total'].apply(pd.to_numeric)
    dff_merged['subtotal'] = dff_merged['subtotal'].apply(pd.to_numeric)
    df_monthly_avg = dff_merged.groupby('month').mean()
    df_monthly_avg = df_monthly_avg.rename(columns={'total': 'avg_total', 'subtotal': 'avg_subtotal'})
    df_monthly_avg = df_monthly_avg[:-1]

    #  df_adjusted and df_monthly_avg dataframes
    df_adjusted = pd.concat([df_adjusted, df_monthly_avg], axis=1)
    df_adjusted = df_adjusted.reset_index()

    fig2 = px.bar(data_frame=df_adjusted,
         x='month',
         y='total',
        #color='avg_total',
        labels={'month': 'Month', 'total': 'Amount / £', 'avg_total': 'Average Delivery Cost'}
        )
    return container, fig1, fig2


# Launch Server --------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)

