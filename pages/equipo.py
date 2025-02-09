# Importaciones de bibliotecas estándar
import sys
import os
from pathlib import Path
import traceback

# Importaciones de terceros
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from flask_caching import Cache
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from plotly.subplots import make_subplots

# Importaciones locales
from data_manager_teams import DataManagerTeams

# Configuración de colores y estilos
BACKGROUND_COLOR = '#0E1117'
LINE_COLOR = '#FFFFFF'
TEXT_COLOR = '#FFFFFF'
HIGHLIGHT_COLOR = '#4BB3FD'

# Inicializar la aplicación Dash
app = Dash(__name__, 
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

# Estilos personalizados
custom_styles = {
    'background': {
        'backgroundColor': BACKGROUND_COLOR,
        'color': TEXT_COLOR,
        'padding': '20px'
    },
    'banner': {
        'backgroundImage': "url('/assets/bunner_alaves3.png')",
        'backgroundSize': 'cover',
        'backgroundPosition': 'center',
        'height': '150px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'marginBottom': '2rem',
        'borderRadius': '5px'
    },
    'banner_title': {
        'color': 'white',
        'textAlign': 'center',
        'margin': '0',
        'fontSize': '2.5rem',
        'fontFamily': 'Arial, sans-serif',
        'textShadow': '2px 2px 0 #000',
        'fontWeight': '700',
        'letterSpacing': '2px',
        'WebkitTextStroke': '1px black'
    },
    'metric_card': {
        'backgroundColor': '#262730',
        'padding': '1rem',
        'borderRadius': '5px',
        'textAlign': 'center',
        'color': TEXT_COLOR
    }
}

# Funciones de visualización
def create_heatmap(df_equipos, team_name, season_ids):
    """Crea el mapa de calor usando Plotly"""
    df_acciones = df_equipos[
        (df_equipos['equipo'] == team_name) &
        (df_equipos['season_id'].isin(season_ids))
    ].copy()
    
    for col in ['xstart', 'ystart']:
        df_acciones[col] = pd.to_numeric(df_acciones[col], errors='coerce')
    
    # Crear el campo de fútbol
    fig = create_football_pitch()
    
    if not df_acciones.empty:
        # Crear heatmap
        fig.add_trace(go.Histogram2d(
            x=df_acciones['xstart'],
            y=df_acciones['ystart'],
            colorscale=[[0, BACKGROUND_COLOR], [1, HIGHLIGHT_COLOR]],
            opacity=0.6,
            showscale=False
        ))
    
    fig.update_layout(
        title=f'Mapa de Calor - {team_name}',
        title_x=0.5,
        title_font_color=TEXT_COLOR,
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR
    )
    
    return fig

def create_flow_map(df_equipos, team_name, season_ids):
    """Crea el mapa de flujo de pases usando Plotly"""
    df_pases = df_equipos[
        (df_equipos['equipo'] == team_name) &
        (df_equipos['season_id'].isin(season_ids)) &
        (df_equipos['tipo_evento'] == 'Pase')
    ].copy()
    
    for col in ['xstart', 'ystart', 'xend', 'yend']:
        df_pases[col] = pd.to_numeric(df_pases[col], errors='coerce')
    
    # Crear el campo de fútbol
    fig = create_football_pitch()
    
    if not df_pases.empty:
        # Añadir flechas de pases
        fig.add_trace(go.Scatter(
            x=df_pases['xstart'],
            y=df_pases['ystart'],
            mode='markers+lines',
            line=dict(color=LINE_COLOR, width=1),
            marker=dict(size=2, color=LINE_COLOR),
            opacity=0.6
        ))
    
    fig.update_layout(
        title=f'Mapa de Flujo de Pases - {team_name}',
        title_x=0.5,
        title_font_color=TEXT_COLOR
    )
    
    return fig

def create_lineup_viz(df_lineups, team_name):
    """Crea la visualización de alineaciones usando Plotly"""
    fig = create_football_pitch()
    
    if not df_lineups.empty:
        df_team = df_lineups[df_lineups['team_name'] == team_name].copy()
        
        # Convertir coordenadas
        df_team['position_x'] = pd.to_numeric(df_team['position_x'], errors='coerce') * 100
        df_team['position_y'] = pd.to_numeric(df_team['position_y'], errors='coerce') * 100
        
        # Añadir posiciones promedio
        fig.add_trace(go.Scatter(
            x=df_team['position_x'],
            y=df_team['position_y'],
            mode='markers+text',
            marker=dict(size=15, color='white'),
            text=df_team['position_name'],
            textposition="top center",
            hoverinfo='text',
            hovertext=df_team.apply(lambda x: f"{x['player_name']} {x['player_last_name']}", axis=1)
        ))
    
    fig.update_layout(
        title=f'Alineaciones más utilizadas - {team_name}',
        title_x=0.5,
        title_font_color=TEXT_COLOR
    )
    
    return fig

def create_evolution_plot(df_equipos, team_name, temporada):
    """Crea el gráfico de evolución usando Plotly"""
    df_team = df_equipos[df_equipos['equipo'] == team_name].copy()
    
    # Procesar datos de evolución
    df_team['xg'] = pd.to_numeric(df_team['xg'], errors='coerce')
    df_team['minute'] = pd.to_numeric(df_team['event_time'].str.split(':').str[0], errors='coerce')
    df_team.loc[df_team['periodo'] == '2ª_parte', 'minute'] += 45
    
    # Crear gráfico
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_team['minute'],
        y=df_team['xg'].cumsum(),
        name=team_name,
        line=dict(color=HIGHLIGHT_COLOR)
    ))
    
    fig.update_layout(
        title=f'Evolución xG - {team_name}',
        xaxis_title='Minuto',
        yaxis_title='xG Acumulado',
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font_color=TEXT_COLOR,
        showlegend=True
    )
    
    return fig

def create_kpi_radar(df_KPI, team_name):
    """Crea el gráfico de radar de KPIs usando Plotly"""
    kpi_columns = [
        'Progresion_Ataque',
        'Verticalidad',
        'Ataques_Bandas',
        'Peligro_Generado',
        'Rendimiento_Finalizacion',
        'Eficacia_Defensiva',
        'Estilo_Combinativo_Directo',
        'Zonas_Recuperacion',
        'Altura_Bloque_Defensivo',
        'Posesion_Dominante',
        'KPI_Rendimiento'
    ]
    
    # Calcular valores promedio
    team_data = df_KPI[df_KPI['equipo'] == team_name][kpi_columns].mean()
    
    # Crear gráfico de radar
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=team_data.values,
        theta=kpi_columns,
        fill='toself',
        name=team_name,
        line_color=HIGHLIGHT_COLOR
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=False,
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font_color=TEXT_COLOR,
        title=f'KPIs - {team_name}'
    )
    
    return fig

def create_kpi_evolution(df_KPI, team_name):
    """Crea el gráfico de evolución de KPIs usando Plotly"""
    df_team = df_KPI[df_KPI['equipo'] == team_name].copy()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_team['jornada'],
        y=df_team['KPI_Rendimiento'],
        marker_color=HIGHLIGHT_COLOR,
        name='KPI Rendimiento'
    ))
    
    fig.update_layout(
        title=f'Evolución KPI Rendimiento - {team_name}',
        xaxis_title='Jornada',
        yaxis_title='KPI Rendimiento',
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font_color=TEXT_COLOR,
        showlegend=True
    )
    
    return fig

def create_football_pitch():
    """Crea un campo de fútbol usando Plotly"""
    fig = go.Figure()
    
    # Dimensiones del campo
    field_length = 120
    field_width = 80
    
    # Dibujar el campo
    fig.add_shape(
        type="rect",
        x0=0, y0=0,
        x1=field_length, y1=field_width,
        line=dict(color=LINE_COLOR),
        fillcolor=BACKGROUND_COLOR,
    )
    
    # Añadir líneas y áreas
    # ... (añadir más formas para las líneas del campo)
    
    fig.update_layout(
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )
    
    return fig

# Layout principal
app.layout = html.Div([
    # Banner
    html.Div([
        html.H1("Equipos - Academia Deportivo Alavés",
                style=custom_styles['banner_title'])
    ], style=custom_styles['banner']),
    
    # Contenedor principal
    dbc.Container([
        # Filtros
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='team-select',
                    placeholder="Seleccionar Equipo",
                    style={'backgroundColor': '#262730', 'color': 'black'}
                )
            ], width=6),
            dbc.Col([
                dcc.Dropdown(
                    id='season-select',
                    placeholder="Seleccionar Temporada",
                    style={'backgroundColor': '#262730', 'color': 'black'}
                )
            ], width=6)
        ], className="mb-4"),
        
        # Botón y métricas
        dbc.Row([
            dbc.Col([
                dbc.Button("Generar Visualización", 
                          id="generate-viz", 
                          color="primary",
                          className="me-2")
            ], width=3),
            dbc.Col([
                html.Div(id='team-info', style=custom_styles['metric_card'])
            ], width=3),
            dbc.Col([
                html.Div(id='season-info', style=custom_styles['metric_card'])
            ], width=3),
            dbc.Col([
                html.Div(id='matches-info', style=custom_styles['metric_card'])
            ], width=3)
        ], className="mb-4"),
        
        # Loading spinner
        dbc.Spinner(html.Div(id="loading-output")),
        
        # Visualizaciones
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='heatmap-graph')
            ], width=6),
            dbc.Col([
                dcc.Graph(id='flow-graph')
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='lineup-graph')
            ], width=6),
            dbc.Col([
                dcc.Graph(id='evolution-graph')
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='kpi-radar')
            ], width=6),
            dbc.Col([
                dcc.Graph(id='kpi-evolution')
            ], width=6)
        ])
    ], fluid=True)
], style=custom_styles['background'])

# Callbacks
@app.callback(
    [Output('team-select', 'options'),
     Output('team-select', 'value')],
    Input('_', 'children')
)
def init_teams(_):
    """Inicializa las opciones de equipos"""
    df_filtros = DataManagerTeams.get_filter_data()
    if df_filtros is not None:
        equipos_alaves = [equipo for equipo in df_filtros['equipo'].unique() 
                         if 'Alav' in equipo]
        options = [{'label': equipo, 'value': equipo} for equipo in sorted(equipos_alaves)]
        return options, None
    return [], None

@app.callback(
    Output('season-select', 'options'),
    Input('team-select', 'value')
)
def update_seasons(team):
    """Actualiza las opciones de temporada basado en el equipo seleccionado"""
    if not team:
        return []
    
    df_filtros = DataManagerTeams.get_filter_data()
    if df_filtros is not None:
        temporadas = df_filtros[df_filtros['equipo'] == team]['temporada'].unique()
        return [{'label': t, 'value': t} for t in sorted(temporadas)]
    return []

@app.callback(
    [Output('team-info', 'children'),
     Output('season-info', 'children'),
     Output('matches-info', 'children'),
     Output('heatmap-graph', 'figure'),
     Output('flow-graph', 'figure'),
     Output('lineup-graph', 'figure'),
     Output('evolution-graph', 'figure'),
     Output('kpi-radar', 'figure'),
     Output('kpi-evolution', 'figure'),
     Output('loading-output', 'children')],
    Input('generate-viz', 'n_clicks'),
    [State('team-select', 'value'),
     State('season-select', 'value')]
)
def update_visualizations(n_clicks, team, season):
    """Actualiza todas las visualizaciones cuando se presiona el botón"""
    if not n_clicks or not team or not season:
        return generate_empty_outputs()
    
    try:
        # Cargar datos
        df_detailed = DataManagerTeams.get_detailed_data(team, season)
        df_lineups = DataManagerTeams.get_lineup_data()
        
        if df_detailed is None:
            return generate_empty_outputs()
        
        # Obtener season_ids
        season_ids = df_detailed['season_id'].unique().tolist()
        
        # Generar métricas
        n_matches = len(df_detailed['match_id'].unique())
        team_info = html.Div([
            html.H4("Equipo", className="text-white"),
            html.P(team, className="text-white")
        ])
        season_info = html.Div([
            html.H4("Temporada", className="text-white"),
            html.P(season, className="text-white")
        ])
        matches_info = html.Div([
            html.H4("Partidos", className="text-white"),
            html.P(str(n_matches), className="text-white")
        ])
        
        # Generar visualizaciones
        heatmap_fig = create_heatmap(df_detailed, team, season_ids)
        flow_fig = create_flow_map(df_detailed, team, season_ids)
        lineup_fig = create_lineup_viz(df_lineups, team)
        evolution_fig = create_evolution_plot(df_detailed, team, season)
        kpi_radar_fig = create_kpi_radar(df_detailed, team)
        kpi_evolution_fig = create_kpi_evolution(df_detailed, team)
        
        return (
            team_info, season_info, matches_info,
            heatmap_fig, flow_fig, lineup_fig,
            evolution_fig, kpi_radar_fig, kpi_evolution_fig,
            ""
        )
        
    except Exception as e:
        print(f"Error en update_visualizations: {e}")
        print(traceback.format_exc())
        return generate_empty_outputs()

def generate_empty_outputs():
    """Genera salidas vacías para cuando no hay datos"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        font_color=TEXT_COLOR
    )
    
    empty_div = html.Div([
        html.H4("Sin datos", className="text-white"),
        html.P("Seleccione equipo y temporada", className="text-white")
    ])
    
    return [empty_div] * 3 + [empty_fig] * 6 + [""]

# Función para exportar a PDF (si se necesita)
def generate_pdf_report(team, season):
    """Genera un reporte PDF de las visualizaciones"""
    try:
        # Aquí iría la lógica para generar el PDF
        pass
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None

# Al final del archivo equipo.py, después de definir app.layout, añade:
layout = app.layout

# Mantén el if __name__ == '__main__': después de esto
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)