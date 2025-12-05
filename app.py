import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# ------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# ------------------------------------------------------
st.set_page_config(
    page_title="Monitor de Campos Chubut",
    page_icon="🐄",
    layout="wide"
)

# ------------------------------------------------------
# 2. CARGA DE DATOS (BACKEND SIMPLE)
# ------------------------------------------------------
@st.cache_data
def cargar_datos():
    # Leemos el CSV que bajaste de Colab
    df = pd.read_csv("datos_renspa.csv")
    
    # Aseguramos tipos de datos correctos
    df['SUPERFICIE'] = pd.to_numeric(df['SUPERFICIE'], errors='coerce').fillna(0)
    df['PARTIDO'] = df['PARTIDO'].fillna('SIN DETERMINAR').astype(str)
    df['CONDICION'] = df['CONDICION'].fillna('SIN DETERMINAR').astype(str)
    
    return df

try:
    df = cargar_datos()
except FileNotFoundError:
    st.error("⚠️ Error: No se encuentra el archivo 'datos_renspa.csv'. Asegúrate de que esté en la misma carpeta.")
    st.stop()

# ------------------------------------------------------
# 3. BARRA LATERAL (FILTROS)
# ------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2823/2823525.png", width=50) # Icono opcional
st.sidebar.title("Filtros de Búsqueda")

st.sidebar.markdown("---")

# A. BUSCADOR DE TEXTO
busqueda = st.sidebar.text_input("🔍 Buscar Establecimiento o RENSPA:")

# B. FILTRO PARTIDO
lista_partidos = sorted(df['PARTIDO'].unique())
partido_sel = st.sidebar.multiselect("📍 Filtrar por Partido:", lista_partidos)

# C. FILTRO CONDICIÓN
lista_condiciones = sorted(df['CONDICION'].unique())
condicion_sel = st.sidebar.multiselect("📋 Filtrar por Condición:", lista_condiciones)

# D. FILTRO SUPERFICIE (SLIDER)
min_s = int(df['SUPERFICIE'].min())
max_s = int(df['SUPERFICIE'].max())
# Usamos un slider doble para rango
rango_sup = st.sidebar.slider("glif: Superficie (Hectáreas):", min_s, max_s, (0, max_s))

# ------------------------------------------------------
# 4. APLICAR LÓGICA DE FILTRADO
# ------------------------------------------------------
df_filtrado = df.copy()

# 1. Por texto
if busqueda:
    mask_nombre = df_filtrado['NOMBRE_ESTABLECIMIENTO'].str.contains(busqueda, case=False, na=False)
    mask_renspa = df_filtrado['RENSPA'].str.contains(busqueda, case=False, na=False)
    df_filtrado = df_filtrado[mask_nombre | mask_renspa]

# 2. Por Partido
if partido_sel:
    df_filtrado = df_filtrado[df_filtrado['PARTIDO'].isin(partido_sel)]

# 3. Por Condición
if condicion_sel:
    df_filtrado = df_filtrado[df_filtrado['CONDICION'].isin(condicion_sel)]

# 4. Por Superficie
df_filtrado = df_filtrado[
    (df_filtrado['SUPERFICIE'] >= rango_sup[0]) & 
    (df_filtrado['SUPERFICIE'] <= rango_sup[1])
]

# ------------------------------------------------------
# 5. INTERFAZ PRINCIPAL (MAPA Y DATOS)
# ------------------------------------------------------
st.title("🗺️ Mapa Interactivo de Establecimientos")
st.markdown(f"**Registros encontrados:** `{len(df_filtrado)}`")

col_mapa, col_datos = st.columns([2, 1])

with col_mapa:
    # Lógica del mapa
    if not df_filtrado.empty:
        # Centrar mapa en base a los resultados
        lat_promedio = df_filtrado['LATITUD'].mean()
        lon_promedio = df_filtrado['LONGITUD'].mean()
        
        m = folium.Map(location=[lat_promedio, lon_promedio], zoom_start=9)
        
        # Cluster para no saturar
        marker_cluster = MarkerCluster().add_to(m)
        
        for idx, row in df_filtrado.iterrows():
            # Contenido del popup
            html = f"""
            <b>{row['NOMBRE_ESTABLECIMIENTO']}</b><br>
            <i>{row['RAZON_SOCIAL']}</i><br>
            <hr>
            <b>RENSPA:</b> {row['RENSPA']}<br>
            <b>Condición:</b> {row['CONDICION']}<br>
            <b>Superficie:</b> {row['SUPERFICIE']} ha
            """
            
            # Icono diferente según condición (Ejemplo simple)
            color_icono = "red" if row['CONDICION'] == 'FISCALERO' else "blue"
            
            folium.Marker(
                location=[row['LATITUD'], row['LONGITUD']],
                tooltip=row['NOMBRE_ESTABLECIMIENTO'],
                popup=folium.Popup(html, max_width=250),
                icon=folium.Icon(color=color_icono, icon="info-sign")
            ).add_to(marker_cluster)
            
        # Mostrar el mapa en Streamlit
        st_folium(m, width=None, height=600)
    else:
        st.warning("No hay resultados con los filtros seleccionados.")

with col_datos:
    st.subheader("Listado Detallado")
    # Mostramos solo columnas clave
    st.dataframe(
        df_filtrado[['NOMBRE_ESTABLECIMIENTO', 'PARTIDO', 'SUPERFICIE', 'CONDICION']],
        hide_index=True,
        use_container_width=True,
        height=600
    )