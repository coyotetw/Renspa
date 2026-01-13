import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# ------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------
st.set_page_config(
    page_title="Monitor Comarca Andina",
    page_icon="🏔️",
    layout="wide"
)

# ------------------------------------------------------
# 2. CARGA DE DATOS
# ------------------------------------------------------
@st.cache_data
def cargar_datos():
    # Leemos el CSV
    df = pd.read_csv("datos_renspa.csv")
    
    # Aseguramos tipos de datos correctos
    df['SUPERFICIE'] = pd.to_numeric(df['SUPERFICIE'], errors='coerce').fillna(0)
    df['PARTIDO'] = df['PARTIDO'].fillna('SIN DETERMINAR').astype(str)
    df['CONDICION'] = df['CONDICION'].fillna('SIN DETERMINAR').astype(str)
    
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ Error: No se encuentra el archivo 'datos_renspa.csv'.")
    st.stop()

# ------------------------------------------------------
# 3. BARRA LATERAL (FILTROS)
# ------------------------------------------------------
st.sidebar.header("🏔️ Filtros Comarca Andina")
st.sidebar.markdown("---")

# A. BUSCADOR DE TEXTO
busqueda = st.sidebar.text_input("🔍 Buscar por Nombre o RENSPA:")

# B. FILTRO PARTIDO (Configurado para Comarca Andina por defecto)
lista_partidos = sorted(df['PARTIDO'].unique())

# Definimos CUSHAMEN como predeterminado (El Hoyo, Epuyén, Puelo, etc.)
# Verificamos si 'CUSHAMEN' está en la lista para evitar errores
default_zona = ['CUSHAMEN'] if 'CUSHAMEN' in lista_partidos else []

partido_sel = st.sidebar.multiselect(
    "📍 Filtrar por Partido:", 
    lista_partidos,
    default=default_zona # <--- ESTO HACE QUE ARRANQUE FILTRADO
)

# C. FILTRO SUPERFICIE
min_s = int(df['SUPERFICIE'].min())
max_s = int(df['SUPERFICIE'].max())
rango_sup = st.sidebar.slider("📏 Superficie (Hectáreas):", min_s, max_s, (0, max_s))

# ------------------------------------------------------
# 4. APLICAR LÓGICA DE FILTRADO
# ------------------------------------------------------
df_filtrado = df.copy()

# 1. Por texto
if busqueda:
    mask_nombre = df_filtrado['NOMBRE_ESTABLECIMIENTO'].str.contains(busqueda, case=False, na=False)
    mask_renspa = df_filtrado['RENSPA'].str.contains(busqueda, case=False, na=False)
    df_filtrado = df_filtrado[mask_nombre | mask_renspa]

# 2. Por Partido (Si el usuario borra todo, muestra todo. Si no, muestra lo seleccionado)
if partido_sel:
    df_filtrado = df_filtrado[df_filtrado['PARTIDO'].isin(partido_sel)]

# 3. Por Superficie
df_filtrado = df_filtrado[
    (df_filtrado['SUPERFICIE'] >= rango_sup[0]) & 
    (df_filtrado['SUPERFICIE'] <= rango_sup[1])
]

# ------------------------------------------------------
# 5. INTERFAZ PRINCIPAL
# ------------------------------------------------------
st.title("🏔️ Mapa de Establecimientos - Zona Comarca Andina")

# Métricas rápidas
col_kpi1, col_kpi2 = st.columns(2)
col_kpi1.metric("Establecimientos en Zona", len(df_filtrado))
col_kpi2.metric("Superficie Total (ha)", f"{df_filtrado['SUPERFICIE'].sum():,.0f}")

col_mapa, col_datos = st.columns([2, 1])

with col_mapa:
    if not df_filtrado.empty:
        # Centrar mapa en base a los resultados filtrados
        lat_promedio = df_filtrado['LATITUD'].mean()
        lon_promedio = df_filtrado['LONGITUD'].mean()
        
        m = folium.Map(location=[lat_promedio, lon_promedio], zoom_start=10)
        
        marker_cluster = MarkerCluster().add_to(m)
        
        for idx, row in df_filtrado.iterrows():
            html = f"""
            <div style='font-family:sans-serif; width:200px'>
                <b>{row['NOMBRE_ESTABLECIMIENTO']}</b><br>
                RENSPA: {row['RENSPA']}<br>
                <hr>
                📍 {row['PARTIDO']}<br>
                📏 {row['SUPERFICIE']} ha<br>
                📋 {row['CONDICION']}
            </div>
            """
            
            folium.Marker(
                location=[row['LATITUD'], row['LONGITUD']],
                tooltip=row['NOMBRE_ESTABLECIMIENTO'],
                popup=folium.Popup(html, max_width=250),
                icon=folium.Icon(color="green", icon="leaf")
            ).add_to(marker_cluster)
            
        st_folium(m, width=None, height=600)
    else:
        st.warning("No se encontraron establecimientos en esta zona con los filtros actuales.")

with col_datos:
    st.subheader("Listado")
    st.dataframe(
        df_filtrado[['NOMBRE_ESTABLECIMIENTO', 'RENSPA', 'SUPERFICIE']],
        hide_index=True,
        use_container_width=True,
        height=600
    )
