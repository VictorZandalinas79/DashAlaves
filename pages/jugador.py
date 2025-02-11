import os
from dash import Dash, html, dcc, Input, Output, State
import dash_ag_grid as dag
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mplsoccer import Pitch
import numpy as np

# Constants and data loading (same as before)
BACKGROUND_COLOR = '#0E1117'
HIGHLIGHT_COLOR = '#4BB3FD'
LINE_COLOR = '#FFFFFF'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, 'data', 'archivos_parquet', 'eventos_metricas_alaves.parquet')

df_jugadores = pq.read_table(PARQUET_PATH).to_pandas()
df_jugadores = df_jugadores[df_jugadores['equipo'].str.contains('Alav', case=False, na=False)]
df_agrupado = df_jugadores.groupby(['jugador', 'equipo', 'player_id']).agg({
    'temporada': lambda x: ', '.join(sorted(x.astype(str).unique())),
    'demarcacion': lambda x: ', '.join(sorted(x.unique())),
    'season_id': lambda x: ', '.join(sorted(x.astype(str).unique()))
}).reset_index()

# Column definitions and default column definitions (same as before)
columnDefs = [
    {"headerName": "Jugador", "field": "jugador", "filter": "agSetColumnFilter", "checkboxSelection": True, "headerCheckboxSelection": True, "width": 200},
    {"headerName": "Equipo", "field": "equipo", "filter": "agSetColumnFilter", "width": 150},
    {"headerName": "Temporadas", "field": "temporada", "filter": "agSetColumnFilter", "width": 200},
    {"headerName": "Demarcaciones", "field": "demarcacion", "filter": "agSetColumnFilter", "width": 200},
    {"headerName": "Player ID", "field": "player_id", "filter": "agSetColumnFilter", "width": 120},
    {"headerName": "Season IDs", "field": "season_id", "filter": "agSetColumnFilter", "width": 200}
]

defaultColDef = {
    "flex": 1,
    "minWidth": 100,
    "filter": True,
    "sortable": True,
    "resizable": True,
    "floatingFilter": False
}

# Layout for the Dash app
layout = html.Div([
    html.H1('Análisis de Jugadores del Alavés', style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # AG Grid
    dag.AgGrid(
        id="grid-jugadores",
        rowData=df_agrupado.to_dict('records'),
        columnDefs=columnDefs,
        defaultColDef=defaultColDef,
        enableEnterpriseModules=True,
        dashGridOptions={
            "sideBar": {
                "toolPanels": [
                    {
                        "id": "filters",
                        "labelDefault": "Filtros",
                        "labelKey": "filters",
                        "iconKey": "filter",
                        "toolPanel": "agFiltersToolPanel",
                    }
                ],
                "defaultToolPanel": "filters"
            },
            "rowSelection": "single",
            "pagination": True,
            "paginationAutoPageSize": True,
            "suppressRowClickSelection": True,
            "rowHeight": 50,
        },
        className="ag-theme-alpine",
        style={"height": 400}
    ),
    
    # Button to generate visualization
    html.Button('Generar Visualización', id='btn-generar', n_clicks=0, style={
        'marginTop': '20px',
        'padding': '10px 20px',
        'backgroundColor': HIGHLIGHT_COLOR,
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    }),
    
    # Selected player info container
    html.Div(id='info-seleccion', style={
        'marginTop': '20px',
        'padding': '15px',
        'backgroundColor': '#f8f9fa',
        'borderRadius': '5px',
        'display': 'none'
    }),
    
    # Graphs container
    html.Div(id='contenedor-graficas', style={'marginTop': '20px'})
])

def register_callbacks(app):
    @app.callback(
        [Output('info-seleccion', 'children'),
         Output('info-seleccion', 'style')],
        [Input('grid-jugadores', 'selectedRows')]
    )
    def mostrar_info_jugador(selected_rows):
        if not selected_rows:
            return '', {'display': 'none'}
        
        jugador = selected_rows[0]
        info = html.Div([
            html.H4(f'Jugador Seleccionado: {jugador["jugador"]}'),
            html.P(f'Equipo: {jugador["equipo"]}'),
            html.P(f'Temporadas: {jugador["temporada"]}'),
            html.P(f'Demarcaciones: {jugador["demarcacion"]}')
        ])
        return info, {'display': 'block'}

    @app.callback(
    Output('contenedor-graficas', 'children'),
    [Input('btn-generar', 'n_clicks')],
    [State('grid-jugadores', 'selectedRows')]
)
    def generar_visualizacion(n_clicks, selected_rows):
        if n_clicks == 0 or not selected_rows:
            return []
    
        print("Selected Rows:", selected_rows)  # Depuración
        jugador = selected_rows[0]
        print("Jugador seleccionado:", jugador)  # Depuración
        
        jugador = selected_rows[0]
        player_id = jugador['player_id']
        season_ids = [int(s) for s in jugador['season_id'].split(', ')]  # Convertir a lista de enteros
        
        # Crear figura con subplots
        fig = plt.figure(figsize=(20, 24), facecolor=BACKGROUND_COLOR)
        gs = gridspec.GridSpec(4, 2, figure=fig)
        
        try:
            # 1. Pizza Chart
            ax1 = fig.add_subplot(gs[0, 0])
            create_pizza_chart(ax1, df_jugadores, player_id, season_ids)
            
            # 2. KPI Evolution
            ax2 = fig.add_subplot(gs[0, 1])
            create_kpi_evolution_chart(ax2, df_jugadores, player_id, season_ids)
            
            # 3. Pass Flow Map
            ax3 = fig.add_subplot(gs[1, 0])
            pitch = Pitch(pitch_type='statsbomb', pitch_color=BACKGROUND_COLOR, line_color='white')
            create_pass_flow_map_vertical(ax3, df_jugadores, player_id, season_ids, pitch)
            
            # 4. Heatmap
            ax4 = fig.add_subplot(gs[1, 1])
            create_heatmap(ax4, df_jugadores, player_id, season_ids, pitch)
            
            # 5. Combined Passes
            ax5 = fig.add_subplot(gs[2, :])
            draw_combined_passes(ax5, df_jugadores, player_id, season_ids, pitch)
            
            # 6. Player Metrics
            ax6 = fig.add_subplot(gs[3, :])
            plot_player_metrics_modern(ax6, df_jugadores, player_id, season_ids)
            
            plt.tight_layout()
            
            # Convertir la figura a un componente de Dash
            return dcc.Graph(
                figure=fig,
                style={'height': '2000px'}
            )
            
        except Exception as e:
            print(f"Error creando gráficos: {e}")
            return html.Div(f"Error creando gráficos: {str(e)}")

import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch

import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch

def create_pizza_chart(ax, df, player_id, season_ids):
    """
    Crear un gráfico de pizza para mostrar los KPIs principales del jugador.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # KPIs definidos basados en las columnas disponibles
    kpis = [
        'xg',
        'pases_progresivos_inicio',
        'pases_progresivos_creacion',
        'pases_progresivos_finalizacion',
        'recuperaciones_zona_media',
        'recuperaciones_zona_alta'
    ]
    
    # Calcular valores para los KPIs
    values = []
    for kpi in kpis:
        if kpi in player_data.columns:
            # Usar el promedio de la métrica
            value = player_data[kpi].mean()
            values.append(value if value > 0 else 0.1)
        else:
            values.append(0.1)
    
    # Normalizar valores
    values_normalized = (values - np.min(values)) / (np.max(values) - np.min(values)) if len(values) > 0 else [0.1] * len(kpis)
    
    # Configurar colores
    colors = plt.cm.viridis(values_normalized)
    
    # Dibujar el gráfico de pizza
    ax.set_facecolor('#0E1117')  # Fondo oscuro
    wedges, texts = ax.pie(
        values_normalized, 
        labels=kpis, 
        colors=colors,
        wedgeprops=dict(width=0.3, edgecolor='white'),
        startangle=90
    )
    
    # Personalizar texto
    for text in texts:
        text.set_color('white')
    
    ax.set_title('Rendimiento del Jugador', color='white')

def create_kpi_evolution_chart(ax, df, player_id, season_ids):
    """
    Crear un gráfico de evolución de KPIs a lo largo de las temporadas.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # KPIs a visualizar
    kpis = [
        'xg',
        'pases_progresivos_inicio',
        'recuperaciones_zona_media',
        'recuperaciones_zona_alta'
    ]
    
    # Configurar fondo
    ax.set_facecolor('#0E1117')
    ax.set_title('Evolución de KPIs', color='white')
    
    # Graficar la evolución de cada KPI
    for kpi in kpis:
        if kpi in player_data.columns:
            # Agrupar por temporada y calcular promedio
            kpi_por_temporada = player_data.groupby('season_id')[kpi].mean()
            ax.plot(
                kpi_por_temporada.index, 
                kpi_por_temporada.values, 
                marker='o', 
                label=kpi
            )
    
    ax.set_xlabel('Temporada', color='white')
    ax.set_ylabel('Valor', color='white')
    ax.legend(loc='best', facecolor='#0E1117', edgecolor='white', labelcolor='white')
    ax.grid(True, color='gray', linestyle='--', alpha=0.3)
    
    # Colorear ejes
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('white')

def create_pass_flow_map_vertical(ax, df, player_id, season_ids, pitch):
    """
    Crear un mapa de flujo de pases para un jugador.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # Dibujar campo de fútbol
    pitch.draw(ax=ax)
    
    # Calcular métricas de pases
    pases_progresivos = {
        'Inicio': player_data['pases_progresivos_inicio'].mean(),
        'Creación': player_data['pases_progresivos_creacion'].mean(),
        'Finalización': player_data['pases_progresivos_finalizacion'].mean(),
        'Largos Exitosos': player_data['pases_largos_exitosos'].mean(),
        'Cambios Orientación': player_data['cambios_orientacion_exitosos'].mean()
    }
    
    # Añadir texto con métricas de pases
    texto_pases = "\n".join([f"{k}: {v:.2f}" for k, v in pases_progresivos.items()])
    ax.text(0.5, 0.05, texto_pases, 
            horizontalalignment='center', 
            verticalalignment='bottom', 
            color='white', 
            transform=ax.transAxes)
    
    ax.set_title('Análisis de Pases Progresivos', color='white')

def create_heatmap(ax, df, player_id, season_ids, pitch):
    """
    Crear un mapa de calor de la posición del jugador.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # Dibujar campo de fútbol
    pitch.draw(ax=ax)
    
    # Métricas de recuperaciones y zonas
    recuperaciones = {
        'Zona Baja': player_data['recuperaciones_zona_baja'].mean(),
        'Zona Media': player_data['recuperaciones_zona_media'].mean(),
        'Zona Alta': player_data['recuperaciones_zona_alta'].mean()
    }
    
    entradas_ganadas = {
        'Zona Baja': player_data['entradas_ganadas_zona_baja'].mean(),
        'Zona Media': player_data['entradas_ganadas_zona_media'].mean(),
        'Zona Alta': player_data['entradas_ganadas_zona_alta'].mean()
    }
    
    # Añadir texto con métricas de zonas
    texto_recuperaciones = "Recuperaciones:\n" + "\n".join([f"{k}: {v:.2f}" for k, v in recuperaciones.items()])
    texto_entradas = "Entradas Ganadas:\n" + "\n".join([f"{k}: {v:.2f}" for k, v in entradas_ganadas.items()])
    
    ax.text(0.05, 0.05, texto_recuperaciones, 
            color='white', 
            transform=ax.transAxes, 
            verticalalignment='bottom')
    
    ax.text(0.95, 0.05, texto_entradas, 
            color='white', 
            transform=ax.transAxes, 
            horizontalalignment='right', 
            verticalalignment='bottom')
    
    ax.set_title('Recuperaciones y Entradas por Zona', color='white')

def draw_combined_passes(ax, df, player_id, season_ids, pitch):
    """
    Dibujar un resumen combinado de pases del jugador.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # Dibujar campo de fútbol
    pitch.draw(ax=ax)
    
    # Métricas de pases
    metricas_pases = {
        'Pases Progresivos - Inicio': player_data['pases_progresivos_inicio'].mean(),
        'Pases Progresivos - Creación': player_data['pases_progresivos_creacion'].mean(),
        'Pases Progresivos - Finalización': player_data['pases_progresivos_finalizacion'].mean(),
        'Pases Largos Exitosos': player_data['pases_largos_exitosos'].mean(),
        'Cambios de Orientación Exitosos': player_data['cambios_orientacion_exitosos'].mean()
    }
    
    # Crear gráfico de barras horizontal
    y_pos = np.arange(len(metricas_pases))
    valores = list(metricas_pases.values())
    
    ax.barh(y_pos, valores, align='center', color='#4BB3FD')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(metricas_pases.keys()), color='white')
    ax.invert_yaxis()  # Etiquetas de arriba a abajo
    
    # Añadir valores a las barras
    for i, v in enumerate(valores):
        ax.text(v, i, f' {v:.2f}', color='white', va='center')
    
    ax.set_title('Análisis Detallado de Pases', color='white')
    ax.set_xlabel('Valor Promedio', color='white')
    ax.tick_params(colors='white')

def plot_player_metrics_modern(ax, df, player_id, season_ids):
    """
    Crear un gráfico de barras moderno con métricas del jugador.
    """
    # Filtrar datos para el jugador y temporadas específicas
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    # Métricas a visualizar
    metrics = {
        'xG (Goles Esperados)': player_data['xg'].mean(),
        'Duelos Aéreos - Área': player_data['duelos_aereos_ganados_zona_area'].mean(),
        'Duelos Aéreos - Zona Baja': player_data['duelos_aereos_ganados_zona_baja'].mean(),
        'Duelos Aéreos - Zona Media': player_data['duelos_aereos_ganados_zona_media'].mean(),
        'Duelos Aéreos - Zona Alta': player_data['duelos_aereos_ganados_zona_alta'].mean(),
        'Recuperaciones - Zona Baja': player_data['recuperaciones_zona_baja'].mean(),
        'Recuperaciones - Zona Media': player_data['recuperaciones_zona_media'].mean(),
        'Recuperaciones - Zona Alta': player_data['recuperaciones_zona_alta'].mean()
    }
    
    # Configurar fondo y estilo
    ax.set_facecolor('#0E1117')
    ax.set_title('Métricas Principales', color='white')
    
    # Crear gráfico de barras horizontal
    y_pos = np.arange(len(metrics))
    valores = list(metrics.values())
    
    ax.barh(y_pos, valores, align='center', color='#4BB3FD')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(list(metrics.keys()), color='white')
    ax.invert_yaxis()  # Etiquetas de arriba a abajo
    
    # Añadir valores a las barras
    for i, v in enumerate(valores):
        ax.text(v, i, f' {v:.2f}', color='white', va='center')
    
    # Configurar ejes
    ax.set_xlabel('Valor Promedio', color='white')
    ax.tick_params(axis='x', colors='white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)