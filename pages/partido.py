# pages/partido.py
from dash import html, dcc
import dash_bootstrap_components as dbc

layout = html.Div([
    html.H3("Análisis de Partidos", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Estadísticas de Partidos"),
                dbc.CardBody([
                    # Aquí tu contenido
                ])
            ])
        ])
    ])
])