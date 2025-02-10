import os
import dash
import pandas as pd
import pyarrow.parquet as pq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Obtener la ruta absoluta al archivo Parquet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, 'data', 'archivos_parquet', 'eventos_metricas_alaves.parquet')

# Cargar los datos desde el archivo Parquet
df_jugadores = pq.read_table(PARQUET_PATH).to_pandas()

# Preparar opciones para los filtros
equipos = sorted(df_jugadores['equipo'].unique())
temporadas = sorted(df_jugadores['temporada'].unique())
demarcaciones = sorted(df_jugadores['demarcacion'].unique())

# Diseño de la página
layout = html.Div([
    html.H1('Análisis de Jugadores del Alavés'),
    
    html.Div([
        html.Div([
            html.Label('Equipo:'),
            dcc.Dropdown(
                id='filtro-equipo',
                options=[{'label': equipo, 'value': equipo} for equipo in equipos],
                placeholder='Selecciona un equipo'
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin-right': '2%'}),
        
        html.Div([
            html.Label('Temporada:'),
            dcc.Dropdown(
                id='filtro-temporada',
                options=[{'label': temporada, 'value': temporada} for temporada in temporadas],
                placeholder='Selecciona una temporada'
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin-right': '2%'}),
        
        html.Div([
            html.Label('Demarcación:'),
            dcc.Dropdown(
                id='filtro-demarcacion',
                options=[{'label': demarcacion, 'value': demarcacion} for demarcacion in demarcaciones],
                placeholder='Selecciona una demarcación'
            )
        ], style={'width': '23%', 'display': 'inline-block', 'margin-right': '2%'}),
        
        html.Div([
            html.Label('Jugador:'),
            dcc.Dropdown(
                id='filtro-jugador',
                placeholder='Selecciona un jugador'
            )
        ], style={'width': '23%', 'display': 'inline-block'})
    ]),
    
    # Espacio para mostrar los resultados filtrados
    html.Div(id='resultados-filtrados')
])

# Función para registrar los callbacks
def register_callbacks(app):
    # Callback para actualizar los jugadores basado en los filtros anteriores
    @app.callback(
        Output('filtro-jugador', 'options'),
        [Input('filtro-equipo', 'value'),
         Input('filtro-temporada', 'value'),
         Input('filtro-demarcacion', 'value')]
    )
    def actualizar_jugadores(equipo, temporada, demarcacion):
        # Filtrar el DataFrame base según los filtros seleccionados
        df_filtrado = df_jugadores.copy()
        
        if equipo:
            df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo]
        if temporada:
            df_filtrado = df_filtrado[df_filtrado['temporada'] == temporada]
        if demarcacion:
            df_filtrado = df_filtrado[df_filtrado['demarcacion'] == demarcacion]
        
        # Obtener lista única de jugadores
        jugadores = sorted(df_filtrado['jugador'].unique())
        
        return [{'label': jugador, 'value': jugador} for jugador in jugadores]

    # Callback para mostrar los resultados filtrados
    @app.callback(
        Output('resultados-filtrados', 'children'),
        [Input('filtro-equipo', 'value'),
         Input('filtro-temporada', 'value'),
         Input('filtro-demarcacion', 'value'),
         Input('filtro-jugador', 'value')]
    )
    def mostrar_resultados(equipo, temporada, demarcacion, jugador):
        # Filtrar el DataFrame base según todos los filtros
        df_filtrado = df_jugadores.copy()
        
        if equipo:
            df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo]
        if temporada:
            df_filtrado = df_filtrado[df_filtrado['temporada'] == temporada]
        if demarcacion:
            df_filtrado = df_filtrado[df_filtrado['demarcacion'] == demarcacion]
        if jugador:
            df_filtrado = df_filtrado[df_filtrado['jugador'] == jugador]
        
        # Mostrar un resumen de los datos filtrados
        return html.Div([
            html.H3('Resultados Filtrados'),
            html.Table([
                html.Thead(
                    html.Tr([html.Th(col) for col in df_filtrado.columns])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(df_filtrado.iloc[i][col]) for col in df_filtrado.columns
                    ]) for i in range(min(10, len(df_filtrado)))
                ])
            ])
        ])