import dash_bootstrap_components as dbc
def Navbar():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("orders-overview", href="/orders-overview")),
            dbc.NavItem(dbc.NavLink("order-details", href="order-details")),
        ],
        brand="home",
        brand_href="/home",
        sticky="top",
        color='primary',
        dark=True
    )
    return navbar