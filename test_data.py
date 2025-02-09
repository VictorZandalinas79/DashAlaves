import os
import pandas as pd
import sys

def main():
    # Imprimir información de depuración del entorno
    print("Python ejecutándose desde:", sys.executable)
    print("Directorio de trabajo actual:", os.getcwd())
    
    # Intentar localizar el archivo Parquet
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("Directorio base:", base_dir)
    
    # Posibles rutas para el archivo
    posibles_rutas = [
        os.path.join(base_dir, "data", "archivos_parquet", "eventos_metricas_alaves.parquet"),
        os.path.join(base_dir, "archivos_parquet", "eventos_metricas_alaves.parquet"),
        os.path.join(base_dir, "eventos_metricas_alaves.parquet"),
        os.path.join(os.getcwd(), "data", "archivos_parquet", "eventos_metricas_alaves.parquet"),
        os.path.join(os.getcwd(), "eventos_metricas_alaves.parquet")
    ]
    
    archivo_encontrado = None
    
    for ruta in posibles_rutas:
        print(f"Verificando ruta: {ruta}")
        if os.path.exists(ruta):
            print(f"Archivo encontrado en: {ruta}")
            archivo_encontrado = ruta
            break
    
    if not archivo_encontrado:
        print("ERROR: No se encontró el archivo eventos_metricas_alaves.parquet")
        return
    
    try:
        # Intenta leer el archivo Parquet
        df = pd.read_parquet(archivo_encontrado)
        
        print("\n--- Información del DataFrame ---")
        print("Dimensiones:", df.shape)
        print("\nColumnas:")
        print(df.columns.tolist())
        
        # Mostrar algunas columnas específicas
        columnas_interes = [
            col for col in df.columns 
            if any(palabra in col.lower() for palabra in ['equipo', 'team', 'temporada', 'season'])
        ]
        
        print("\nColumnas de interés:")
        print(columnas_interes)
        
        # Mostrar valores únicos en columnas de interés
        for col in columnas_interes:
            print(f"\nValores únicos en {col}:")
            print(df[col].unique())
    
    except Exception as e:
        print("Error al leer el archivo:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()