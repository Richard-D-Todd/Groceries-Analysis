import dash_core_components as dcc
import dash_html_components as html 
from dash.dependencies import Input, Output
import configparser

from app import app
from apps import app1
from apps import app2
import homepage

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)

def display_page(pathname):
    if pathname == '/orders-overview':
        return app1.layout
    elif pathname == '/order-details':
        return app2.layout
    else:
        return homepage.layout

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('host_details.ini')
    port=config['details']['port']
    host=config['details']['host_ip']
    app.run_server(debug=False, port=port, host=host)