import os
from dash import Dash, html, dcc, Input, Output, State
import dash_ag_grid as dag
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mplsoccer import Pitch
import numpy as np
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# Constants and data loading
BACKGROUND_COLOR = '#0E1117'
HIGHLIGHT_COLOR = '#4BB3FD'
LINE_COLOR = '#FFFFFF'

# Initialize the Dash app
app = Dash(__name__)

# Load data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, 'data', 'archivos_parquet', 'eventos_metricas_alaves.parquet')

df_jugadores = pq.read_table(PARQUET_PATH).to_pandas()
df_jugadores = df_jugadores[df_jugadores['equipo'].str.contains('Alav', case=False, na=False)]
df_agrupado = df_jugadores.groupby(['jugador', 'equipo', 'player_id']).agg({
    'temporada': lambda x: ', '.join(sorted(x.astype(str).unique())),
    'demarcacion': lambda x: ', '.join(sorted(x.unique())),
    'season_id': lambda x: ', '.join(sorted(x.astype(str).unique()))
}).reset_index()

# Column definitions
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

# Layout
app.layout = html.Div([
    html.H1('Análisis de Jugadores del Alavés', 
            style={'textAlign': 'center', 'marginBottom': '20px', 'color': LINE_COLOR}),
    
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
        className="ag-theme-alpine-dark",
        style={"height": 400}
    ),
    
    # Button
    html.Button('Generar Visualización', 
                id='btn-generar', 
                n_clicks=0, 
                style={
                    'marginTop': '20px',
                    'padding': '10px 20px',
                    'backgroundColor': HIGHLIGHT_COLOR,
                    'color': 'white',
                    'border': 'none',
                    'borderRadius': '5px',
                    'cursor': 'pointer'
                }),
    
    # Info container
    html.Div(id='info-seleccion', 
             style={
                 'marginTop': '20px',
                 'padding': '15px',
                 'backgroundColor': '#1E2127',
                 'borderRadius': '5px',
                 'display': 'none',
                 'color': LINE_COLOR
             }),
    
    # Graphs container
    html.Div(id='contenedor-graficas', 
             style={'marginTop': '20px'})
])

# Callbacks
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
    return info, {
        'display': 'block',
        'marginTop': '20px',
        'padding': '15px',
        'backgroundColor': '#1E2127',
        'borderRadius': '5px',
        'color': LINE_COLOR
    }

@app.callback(
    Output('contenedor-graficas', 'children'),
    [Input('btn-generar', 'n_clicks')],
    [State('grid-jugadores', 'selectedRows')]
)
def generar_visualizacion(n_clicks, selected_rows):
    if n_clicks == 0 or not selected_rows:
        return []
    
    jugador = selected_rows[0]
    player_id = jugador['player_id']
    season_ids = [int(s) for s in jugador['season_id'].split(', ')]
    
    try:
        # Crear figura con subplots
        fig = plt.figure(figsize=(20, 24), facecolor=BACKGROUND_COLOR)
        gs = gridspec.GridSpec(4, 2, figure=fig)
        
        # Create all visualizations
        pitch = Pitch(pitch_type='statsbomb', pitch_color=BACKGROUND_COLOR, line_color='white')
        
        # 1. Pizza Chart
        ax1 = fig.add_subplot(gs[0, 0])
        create_pizza_chart(ax1, df_jugadores, player_id, season_ids)
        
        # 2. KPI Evolution
        ax2 = fig.add_subplot(gs[0, 1])
        create_kpi_evolution_chart(ax2, df_jugadores, player_id, season_ids)
        
        # 3. Pass Flow Map
        ax3 = fig.add_subplot(gs[1, 0])
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
        
        # Convert plot to PNG image
        canvas = FigureCanvas(fig)
        png_output = io.BytesIO()
        canvas.print_png(png_output)
        png_output.seek(0)
        img_data = base64.b64encode(png_output.getvalue()).decode()
        
        plt.close(fig)
        
        return html.Img(
            src=f'data:image/png;base64,{img_data}',
            style={'width': '100%', 'height': 'auto'}
        )
        
    except Exception as e:
        return html.Div(f"Error creando gráficos: {str(e)}", 
                       style={'color': 'red', 'margin': '20px'})

# Funciones de visualización
def create_pizza_chart(ax, df, player_id, season_ids):
    """Pizza chart creation function"""
    # [Mantener el código existente de create_pizza_chart]
    player_data = df[(df['player_id'] == player_id) & 
                     (df['season_id'].isin(map(str, season_ids)))]
    
    if player_data.empty:
        ax.text(0.5, 0.5, 'No hay datos disponibles', 
                ha='center', va='center', color='white')
        return
    
    kpis = [
        'xg',
        'pases_progresivos_inicio',
        'pases_progresivos_creacion',
        'pases_progresivos_finalizacion',
        'recuperaciones_zona_media',
        'recuperaciones_zona_alta'
    ]
    
    values = []
    for kpi in kpis:
        if kpi in player_data.columns:
            value = player_data[kpi].mean()
            values.append(value if value > 0 else 0.1)
        else:
            values.append(0.1)
    
    values_normalized = (values - np.min(values)) / (np.max(values) - np.min(values)) if len(values) > 0 else [0.1] * len(kpis)
    colors = plt.cm.viridis(values_normalized)
    
    ax.set_facecolor(BACKGROUND_COLOR)
    wedges, texts = ax.pie(
        values_normalized, 
        labels=kpis, 
        colors=colors,
        wedgeprops=dict(width=0.3, edgecolor='white'),
        startangle=90
    )
    
    for text in texts:
        text.set_color('white')
    
    ax.set_title('Rendimiento del Jugador', color='white')

[Las funciones create_kpi_evolution_chart, create_pass_flow_map_vertical, create_heatmap, 
draw_combined_passes, y plot_player_metrics_modern permanecen igual que en el código original]

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8000, debug=True)