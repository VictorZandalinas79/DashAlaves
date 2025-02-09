import pandas as pd
import os
from pathlib import Path

class DataManagerTeams:  # Cambiado de DataManager a DataManagerTeams
    BASE_DIR = Path(__file__).parent
    
    @staticmethod
    def load_base_data():
        ruta_archivo = os.path.join(DataManagerTeams.BASE_DIR, "data/archivos_parquet/eventos_metricas_alaves.parquet")  # Actualizada referencia
        try:
            return pd.read_parquet(ruta_archivo)
        except Exception as e:
            print(f"Error cargando datos base: {e}")
            return None
    
    @staticmethod
    def get_filter_data():
        """Método nuevo para obtener datos de filtros"""
        try:
            df = DataManagerTeams.load_base_data()  # Actualizada referencia
            if df is not None:
                # Obtener datos únicos para los filtros
                return df[['equipo', 'temporada']].drop_duplicates()
            return None
        except Exception as e:
            print(f"Error cargando datos de filtros: {e}")
            return None
    
    @staticmethod
    def get_match_ids(equipo_seleccionado, temporada_seleccionada):
        df_filtros = DataManagerTeams.load_base_data()  # Actualizada referencia
        if temporada_seleccionada != 'Todas':
            df_filtros = df_filtros[df_filtros['temporada'] == temporada_seleccionada]
        return df_filtros[df_filtros['equipo'] == equipo_seleccionado]['match_id'].unique()
    
    @staticmethod
    def get_detailed_data(equipo_seleccionado, temporada_seleccionada):
        try:
            match_ids = DataManagerTeams.get_match_ids(equipo_seleccionado, temporada_seleccionada)  # Actualizada referencia
            
            # Cargar datos
            df_equipos = pd.read_parquet(
                os.path.join(DataManagerTeams.BASE_DIR, "data/archivos_parquet/eventos_metricas_alaves.parquet")  # Actualizada referencia
            )
            df_estadisticas = pd.read_parquet(
                os.path.join(DataManagerTeams.BASE_DIR, "data/archivos_parquet/team_stats_league_all.parquet")  # Actualizada referencia
            )
            df_KPI = pd.read_parquet(
                os.path.join(DataManagerTeams.BASE_DIR, "data/archivos_parquet/eventos_datos_acumulados.parquet")  # Actualizada referencia
            )
            
            # Filtrar y combinar
            df_combinado = pd.merge(df_equipos, df_estadisticas, on=['match_id', 'season_id'])
            df_final = pd.merge(df_combinado, df_KPI, on=['match_id', 'season_id', 'equipo'])
            
            return df_final[df_final['match_id'].isin(match_ids)]
            
        except Exception as e:
            print(f"Error cargando datos detallados: {e}")
            return None
    
    @staticmethod
    def get_lineup_data():
        try:
            return pd.read_parquet(os.path.join(DataManagerTeams.BASE_DIR, "data/archivos_parquet/lineups_league_all.parquet"))  # Actualizada referencia
        except Exception as e:
            print(f"Error cargando alineaciones: {e}")
            return None