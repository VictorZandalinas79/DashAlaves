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



# Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)