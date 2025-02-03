import streamlit as st
import os
import sqlalchemy as sa
import pandas as pd

# =================== Configurar Página con Wide Mode ===================
st.set_page_config(page_title="Inicio", page_icon="🏠", layout="wide")

# =================== Configuración de Base de Datos ===================
server = "nwn7f7ze6vtuxen5age454nhca-colrz4odas5unhn7cagatohexq.datawarehouse.fabric.microsoft.com"
database = "TMDB"
driver = "ODBC Driver 17 for SQL Server"
table = "tmdb_movies_clean"

# Obtener credenciales desde variables de entorno (Streamlit Secrets)
user = os.getenv("DB_USER")
password = os.getenv("DB_PASS")

# Cadena de conexión
connection_string = (
    f"mssql+pyodbc://{user}:{password}@{server}/{database}?"
    f"driver={driver}&Authentication=ActiveDirectoryPassword"
)

@st.cache_data
def fetch_data(query):
    """Ejecuta una consulta SQL y devuelve un DataFrame"""
    try:
        engine = sa.create_engine(
            connection_string,
            echo=False,
            connect_args={"autocommit": True},
        )
        with engine.connect() as conn:
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error al ejecutar la consulta: {e}")
        return pd.DataFrame()

@st.cache_data
def filter_top_shows(df, genre, title, overview, network):
    """Filtra y ordena los 10 mejores shows según los criterios dados"""
    filtered_shows = df.copy()

    if genre:
        filtered_shows = filtered_shows[filtered_shows['genres'].str.contains(genre, case=False, na=False)]
    if title:
        filtered_shows = filtered_shows[filtered_shows['title'].str.contains(title, case=False, na=False)]
    if overview:
        filtered_shows = filtered_shows[filtered_shows['overview'].str.contains(overview, case=False, na=False)]
    if network:
        filtered_shows = filtered_shows[filtered_shows['production_companies'].str.contains(network, case=False, na=False)]

    top_shows = filtered_shows.sort_values(by='vote_average', ascending=False).head(10)
    if not top_shows.empty:
        base_url = "https://image.tmdb.org/t/p/w500"
        top_shows['image_url'] = base_url + top_shows['poster_path'].fillna("")
        return top_shows[top_shows['image_url'].str.len() > len(base_url)]  # Filtrar URLs válidas
    return pd.DataFrame()

# =================== Página Principal ===================
if "page" not in st.session_state:
    st.session_state.page = "home"
if st.session_state.page == "home":
    query = f"SELECT * FROM {table}"
    df = fetch_data(query)

    st.markdown("## Buscar Shows de TV o Películas 🎬")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        genre_input = st.text_input("Género")
    with col2:
        title_input = st.text_input("Título")
    with col3:
        overview_input = st.text_input("Sinopsis/Resumen")
    with col4:
        network_input = st.text_input("Productora")

    if st.button("Buscar"):
        top_shows = filter_top_shows(df, genre_input, title_input, overview_input, network_input)

        if not top_shows.empty:
            st.write("### Resultados:")
            cols_per_row = 4  # Cambiar el número de columnas por fila
            cols = st.columns(cols_per_row)

            for index, row in top_shows.iterrows():
                with cols[index % cols_per_row]:
                    st.image(row['image_url'], use_column_width=True)
                    st.markdown(f"**{row['title']}** ({str(row['release_date'])[:4] if pd.notna(row['release_date']) else 'N/A'})")
                    st.markdown(f"⭐ {row['vote_average']:.1f}")
        else:
            st.warning("No se encontraron resultados para los criterios ingresados.")
    else:
        st.info("Introduce al menos un criterio de búsqueda y presiona 'Buscar' para comenzar.")

