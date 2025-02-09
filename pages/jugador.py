# pages/jugador.py
from dash import html, dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    html.H3("Análisis de Jugadores", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Estadísticas de Jugadores"),
                dbc.CardBody([
                    # Aquí tu contenido
                ])
            ])
        ])
    ])
])