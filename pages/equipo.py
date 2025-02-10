# Importaciones de bibliotecas estándar
import sys
import os
from pathlib import Path
import traceback
import io

# Importaciones de terceros
from dash import Dash, html, dcc, callback
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Usar backend sin interfaz gráfica
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mplsoccer import Pitch, VerticalPitch
from scipy.ndimage import gaussian_filter
from scipy.spatial import ConvexHull
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from PIL import Image

# Configuración de colores y estilos
BACKGROUND_COLOR = '#f8f9fa'
PRIMARY_COLOR = '#007bff'
TEXT_COLOR = '#000000'
HIGHLIGHT_COLOR = '#4BB3FD'
LINE_COLOR = '#007bff'

# Clase para manejar la carga y gestión de datos
class DataManager:
    @staticmethod
    def load_parquet_data(file_path):
        try:
            df = pd.read_parquet(file_path, engine='fastparquet')
            df['equipo'] = df['equipo'].astype('category') 
            df['temporada'] = df['temporada'].astype('category')
            df['season_id'] = df['season_id'].astype('category')
            return df
        except Exception as e:
            print(f"Error cargando archivo {file_path}: {e}")
            return None

    @staticmethod
    def get_filter_data(df):
        """Obtiene datos de filtro"""
        # Filtrar solo equipos de Alavés
        equipos_alaves = [equipo for equipo in df['equipo'].unique() if 'Alavés' in str(equipo)]
        
        # Crear DataFrame de filtros solo con equipos de Alavés
        df_filtros = df[df['equipo'].isin(equipos_alaves)][['equipo', 'temporada']].drop_duplicates()
        
        return df_filtros

    @staticmethod
    def filter_data(df, team, season):
        """Filtra datos por equipo y temporada"""
        df_filtered = df[
            (df['equipo'] == team) & 
            (df['temporada'] == season)
        ]
        return df_filtered

# Cargar datos globales
BASE_DIR = Path(__file__).parent.parent
PARQUET_PATH = os.path.join(BASE_DIR, "data", "archivos_parquet", "eventos_metricas_alaves.parquet")

try:
    GLOBAL_DATA = DataManager.load_parquet_data(PARQUET_PATH)
    FILTER_DATA = DataManager.get_filter_data(GLOBAL_DATA)
except Exception as e:
    print(f"Error cargando datos globales: {e}")
    GLOBAL_DATA = None
    FILTER_DATA = None

# Funciones de visualización
def create_team_advanced_metrics(df_combined, team_name, season_ids):
    """
    Crea un gráfico de métricas avanzadas para un equipo.
    
    Parámetros:
    - df_combined: DataFrame con los datos combinados
    - team_name: Nombre del equipo
    - season_ids: Lista de IDs de temporadas
    """
    # Crear figura y eje
    plt.figure(figsize=(12, 8), facecolor=BACKGROUND_COLOR)
    
    # Filtrar datos para el equipo y temporadas
    df_team = df_combined[
        (df_combined['equipo'] == team_name) & 
        (df_combined['season_id'].isin(season_ids))
    ].copy()
    
    # Definir métricas avanzadas de interés a nivel de equipo
    metricas_avanzadas = [
        ('Duelos Aéreos Ganados', 
         ['duelos_aereos_ganados_zona_area', 'duelos_aereos_ganados_zona_baja', 
          'duelos_aereos_ganados_zona_media', 'duelos_aereos_ganados_zona_alta']),
        
        ('Recuperaciones', 
         ['recuperaciones_zona_baja', 'recuperaciones_zona_media', 'recuperaciones_zona_alta']),
        
        ('Entradas Ganadas', 
         ['entradas_ganadas_zona_area', 'entradas_ganadas_zona_baja', 
          'entradas_ganadas_zona_media', 'entradas_ganadas_zona_alta']),
        
        ('Pases Largos Exitosos', 
         ['pases_largos_exitosos', 'cambios_orientacion_exitosos']),
        
        ('Pases Adelante', 
         ['pases_adelante_inicio', 'pases_adelante_creacion']),
        
        ('Pases Horizontales', 
         ['pases_horizontal_inicio', 'pases_horizontal_creacion'])
    ]
    
    # Preparar datos para el gráfico
    nombres_metricas = []
    valores_metricas = []
    
    for nombre, columnas in metricas_avanzadas:
        # Sumar valores de las columnas, convirtiendo a numérico
        valores = []
        for col in columnas:
            # Convertir a numérico, reemplazando valores no numéricos con 0
            df_team[col] = pd.to_numeric(df_team[col], errors='coerce').fillna(0)
            valores.append(df_team[col].sum())
        
        # Sumar total de la métrica
        total = sum(valores)
        
        nombres_metricas.append(nombre)
        valores_metricas.append(total)
    
    # Crear gráfico de barras horizontal
    colors = [PRIMARY_COLOR, '#50C878', '#FFD700', '#FF6B6B', '#9370DB', '#FF4500']
    
    y_pos = range(len(nombres_metricas))
    plt.barh(y_pos, valores_metricas, align='center', color=colors)
    
    # Personalizar ejes
    plt.yticks(y_pos, nombres_metricas, color=TEXT_COLOR)
    plt.xlabel('Número de Acciones', color=TEXT_COLOR)
    plt.title(f'Métricas Avanzadas: {team_name}', color=TEXT_COLOR, fontsize=14, pad=20)
    
    # Color de texto y ejes
    plt.tick_params(colors=TEXT_COLOR)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_color(TEXT_COLOR)
    plt.gca().spines['bottom'].set_color(TEXT_COLOR)
    
    # Añadir valores en las barras
    for i, v in enumerate(valores_metricas):
        plt.text(v, i, f' {v:.0f}', color=TEXT_COLOR, va='center')
    
    # Estilo general
    plt.gca().set_facecolor(BACKGROUND_COLOR)
    plt.tight_layout()
    
    return plt.gcf()

def create_team_pass_flow_map(df_equipos, team_name, season_ids):
    """Crea el mapa de flujo de pases usando matplotlib y mplsoccer"""
    # Configurar el pitch
    pitch = Pitch(pitch_type='wyscout', pitch_color=BACKGROUND_COLOR, line_color=PRIMARY_COLOR)
    
    # Crear figura y eje
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=BACKGROUND_COLOR)
    
    # Filtrar pases
    df_pases = df_equipos[
        (df_equipos['equipo'] == team_name) &
        (df_equipos['season_id'].isin(season_ids)) &
        (df_equipos['tipo_evento'] == 'Pase')
    ].copy()
    
    # Convertir columnas numéricas
    for col in ['xstart', 'ystart', 'xend', 'yend']:
        df_pases[col] = pd.to_numeric(df_pases[col], errors='coerce')
    
    # Filtrar pases con coordenadas válidas
    df_pases_flujo = df_pases[
        df_pases['xstart'].notna() &
        df_pases['ystart'].notna() &
        df_pases['xend'].notna() &
        df_pases['yend'].notna()
    ]
    
    # Dibujar el campo
    pitch.draw(ax=ax)
    
    if not df_pases_flujo.empty:
        # Configurar bins para el heatmap
        bins = (6, 4)
        
        # Calcular estadísticas de los pases
        heatmap = pitch.bin_statistic(
            df_pases_flujo.ystart.astype(float),
            df_pases_flujo.xstart.astype(float),
            statistic='count',
            bins=bins
        )
        
        # Crear mapa de color personalizado
        heatmap_cmap = LinearSegmentedColormap.from_list(
            "custom_heatmap",
            [BACKGROUND_COLOR, PRIMARY_COLOR]
        )
        
        # Dibujar heatmap
        pitch.heatmap(
            heatmap,
            ax=ax,
            cmap=heatmap_cmap,
            alpha=0.6
        )
        
        # Intentar dibujar flujo de pases
        try:
            pitch.flow(
                df_pases_flujo.ystart.astype(float),
                df_pases_flujo.xstart.astype(float),
                df_pases_flujo.yend.astype(float),
                df_pases_flujo.xend.astype(float),
                color=LINE_COLOR,
                arrow_type='scale',
                arrow_length=15,
                bins=bins,
                ax=ax,
                zorder=2,
                alpha=0.6
            )
        except Exception as e:
            print(f"Error en pitch.flow: {e}")
    
    # Título del gráfico
    ax.set_title(f'Mapa de Flujo de Pases - {team_name}', color=TEXT_COLOR)
    
    return fig
def create_team_heatmap(df_equipos, team_name, season_ids):
    """Crea el mapa de calor de acciones del equipo"""
    pitch = Pitch(pitch_type='wyscout', pitch_color=BACKGROUND_COLOR, line_color=PRIMARY_COLOR)
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=BACKGROUND_COLOR)
    
    df_acciones = df_equipos[
        (df_equipos['equipo'] == team_name) &
        (df_equipos['season_id'].isin(season_ids))
    ].copy()
    
    for col in ['xstart', 'ystart']:
        df_acciones[col] = pd.to_numeric(df_acciones[col], errors='coerce')
    
    pitch.draw(ax=ax)
    
    bin_statistic = pitch.bin_statistic(
        df_acciones['ystart'], 
        df_acciones['xstart'], 
        statistic='count', 
        bins=(20, 20)
    )
    
    # Suavizar el heatmap
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    
    # Crear un mapa de color personalizado
    cmap = LinearSegmentedColormap.from_list('custom', [BACKGROUND_COLOR, PRIMARY_COLOR])
    
    pitch.heatmap(bin_statistic, ax=ax, cmap=cmap, edgecolors=BACKGROUND_COLOR)
    
    ax.set_title(f'Mapa de Calor - {team_name}', color=TEXT_COLOR)
    return fig

def create_lineup_visualization(df_lineups, team_name):
    """Crea la visualización de alineaciones"""
    pitch = Pitch(pitch_type='wyscout', pitch_color=BACKGROUND_COLOR, line_color=PRIMARY_COLOR)
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=BACKGROUND_COLOR)
    
    df_team = df_lineups[df_lineups['team_name'] == team_name].copy()
    
    # Convertir coordenadas
    df_team['position_x'] = pd.to_numeric(df_team['position_x'], errors='coerce') * 100
    df_team['position_y'] = pd.to_numeric(df_team['position_y'], errors='coerce') * 100
    
    pitch.draw(ax=ax)
    
    # Añadir posiciones promedio
    ax.scatter(
        df_team['position_x'], 
        df_team['position_y'], 
        color=PRIMARY_COLOR, 
        s=100, 
        alpha=0.7
    )
    
    for _, row in df_team.iterrows():
        ax.annotate(
            row['player_name'], 
            (row['position_x'], row['position_y']), 
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            color=TEXT_COLOR
        )
    
    ax.set_title(f'Alineaciones - {team_name}', color=TEXT_COLOR)
    return fig

# Layout de la página
layout = dbc.Container([
    # Navbar
    html.Div("Equipos - Academia Deportivo Alavés", className='navbar'),
    
    # Contenedor principal
    dbc.Container([
        # Mensaje de error si no se cargan los datos
        html.Div(id='error-message', style={'color': 'red', 'textAlign': 'center'}),
        
        # Filtros
        dbc.Row([
            dbc.Col([
                html.Label("Seleccionar Equipo"),
                dcc.Dropdown(
                    id='team-select',
                    placeholder="Seleccionar Equipo",
                    className='form-control'
                )
            ], width=6),
            dbc.Col([
                html.Label("Seleccionar Temporada"),
                dcc.Dropdown(
                    id='season-select',
                    placeholder="Seleccionar Temporada",
                    className='form-control'
                )
            ], width=6)
        ], className="mb-4"),
        
        # Botón y métricas
        dbc.Row([
            dbc.Col([
                dbc.Button("Generar Visualización", 
                          id="generate-viz", 
                          color="primary",
                          className="w-100")
            ], width=3),
            dbc.Col([
                html.Div(id='team-info', className='login-container')
            ], width=3),
            dbc.Col([
                html.Div(id='season-info', className='login-container')
            ], width=3),
            dbc.Col([
                html.Div(id='matches-info', className='login-container')
            ], width=3)
        ], className="mb-4"),
        
        # Contenedor para visualizaciones
        html.Div(id='visualizations-container', className='row')
    ], fluid=True)
], style={'backgroundColor': BACKGROUND_COLOR})

# Callbacks
@callback(
    [Output('team-select', 'options'),
     Output('team-select', 'value'),
     Output('error-message', 'children')],
    Input('generate-viz', 'id')
)
def init_teams(_):
    if GLOBAL_DATA is None or FILTER_DATA is None:
        return [], None, "Error: No se pudieron cargar los datos"
    
    try:
        equipos = [str(equipo) for equipo in sorted(FILTER_DATA['equipo'].unique())]
        options = [{'label': equipo, 'value': equipo} for equipo in equipos]
        
        return options, options[0]['value'], ""
    except Exception as e:
        return [], None, f"Error: {e}"

@callback(
    Output('season-select', 'options'),
    Input('team-select', 'value')
)
def update_seasons(team):
    if not team or GLOBAL_DATA is None:
        return []
    
    try:
        temporadas = sorted(GLOBAL_DATA[GLOBAL_DATA['equipo'] == team]['temporada'].unique())
        return [{'label': temporada, 'value': temporada} for temporada in temporadas]
    except Exception as e:
        print(f"Error en update_seasons: {e}")
        return []

@callback(
    Output('visualizations-container', 'children'),
    Input('generate-viz', 'n_clicks'),
    [State('team-select', 'value'),
     State('season-select', 'value')]
)
def update_visualizations(n_clicks, team, season):
    if not n_clicks or not team or not season:
        return []
    
    try:
        # Filtrar datos
        df_detailed = DataManager.filter_data(GLOBAL_DATA, team, season)
        
        # Obtener season_ids
        season_ids = df_detailed['season_id'].unique().tolist()
        
        # Generar visualizaciones
        metrics_fig = create_team_advanced_metrics(df_detailed, team, season_ids)  # Pasar team y season_ids
        pass_flow_fig = create_team_pass_flow_map(df_detailed, team, season_ids)
        heatmap_fig = create_team_heatmap(df_detailed, team, season_ids)
        
        # Convertir figuras de matplotlib a imágenes base64
        from io import BytesIO
        import base64
        
        def fig_to_base64(fig):
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)  # Cerrar la figura después de guardarla
            buf.seek(0)
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        
        visualizations = [
            dbc.Col([
                html.H4("Métricas del Equipo", className="text-center"),
                html.Img(
                    src=f'data:image/png;base64,{fig_to_base64(metrics_fig)}',
                    className='img-fluid'
                )
            ], width=6),
            dbc.Col([
                html.H4("Mapa de Flujo de Pases", className="text-center"),
                html.Img(
                    src=f'data:image/png;base64,{fig_to_base64(pass_flow_fig)}',
                    className='img-fluid'
                )
            ], width=6),
            dbc.Col([
                html.H4("Mapa de Calor", className="text-center"),
                html.Img(
                    src=f'data:image/png;base64,{fig_to_base64(heatmap_fig)}',
                    className='img-fluid'
                )
            ], width=12)
        ]
        
        return visualizations
    
    except Exception as e:
        print(f"Error en update_visualizations: {e}")
        import traceback
        traceback.print_exc()
        return [html.Div(f"Error: {e}", className="alert alert-danger")]

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)