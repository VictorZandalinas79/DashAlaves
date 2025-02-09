from dash import dcc, html, Input, Output, State
import dash
import pandas as pd
import dash_bootstrap_components as dbc
from pages import equipo, jugador, partido
from dash.dependencies import Input, Output

# Cargar datos de usuarios
df_users = pd.read_csv("data/usuarios.csv")

# Layouts
login_layout = html.Div([
   html.Div("BePro - Análisis Deportivo", className="navbar"),
   html.Div([
       html.H2("Iniciar Sesión"),
       dcc.Input(id="username", type="text", placeholder="Usuario"),
       dcc.Input(id="password", type="password", placeholder="Contraseña"),
       html.Button("Login", id="login-button"),
       html.Div(id="login-output", style={"color": "red", "marginTop": "10px"})
   ], className="login-container"),
])

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
   dcc.Location(id="url", refresh=False),
   html.Div(id="page-content")
])

@app.callback(
   Output("url", "pathname"),
   Input("login-button", "n_clicks"),
   [State("username", "value"),
    State("password", "value")],
   prevent_initial_call=True
)
def login_callback(n_clicks, username, password):
   if not n_clicks:
       return dash.no_update
   if username and password:
       user = df_users[(df_users["username"] == username) & 
                      (df_users["password"] == password)]
       if not user.empty:
           return "/home"
   return "/"

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page(pathname):
    if pathname == "/home":
        return generate_main_layout()
    elif pathname == "/equipo":
        return equipo.layout
    elif pathname == "/jugador":
        return jugador.layout
    elif pathname == "/partido":
        return partido.layout
    return login_layout

def generate_main_layout():
   return html.Div([
       html.Div("BePro - Análisis Deportivo", className="navbar"),
       html.H3("Panel Principal"),
       html.Div([
           html.Div([
               dbc.Button("Equipo", id="nav-equipo", className="m-2"),
               dbc.Button("Jugador", id="nav-jugador", className="m-2"),
               dbc.Button("Partidos", id="nav-partidos", className="m-2"),
           ], className="d-flex justify-content-center"),
           html.Button("Cerrar Sesión", id="logout-button", className="mt-3")
       ])
   ])

@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    [Input("nav-equipo", "n_clicks"),
     Input("nav-jugador", "n_clicks"),
     Input("nav-partidos", "n_clicks"),
     Input("logout-button", "n_clicks")],
    prevent_initial_call=True
)
def navigate(nav_equipo, nav_jugador, nav_partidos, logout):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
        
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id.startswith("nav-"):
        return f"/{button_id.split('-')[1]}"
    elif button_id == "logout-button":
        return "/"
    
    return dash.no_update

if __name__ == '__main__':
   app.run_server(debug=True)