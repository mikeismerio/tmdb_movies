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
def fetch_filtered_data(genre, title, overview, production_company, filter_adults):
    """Construye una consulta SQL dinámica y devuelve un DataFrame filtrado."""
    filters = []

    if genre:
        filters.append(f"LOWER(genres) LIKE '%{genre.lower()}%'")
    if title:
        filters.append(f"LOWER(title) LIKE '%{title.lower()}%'")
    if overview:
        filters.append(f"LOWER(overview) LIKE '%{overview.lower()}%'")
    if production_company:
        filters.append(f"LOWER(production_companies) LIKE '%{production_company.lower()}%'")
    if filter_adults:
        filters.append("adult = 1")

    query = f"SELECT TOP 10 * FROM {table}"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY vote_average DESC"

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

# =================== Control de Navegación ===================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None

def navigate(page, movie=None):
    st.session_state.page = page
    st.session_state.selected_movie = movie

# =================== Página Principal ===================
if st.session_state.page == "home":
    genre_input = st.text_input("Introduce el Género:")
    title_input = st.text_input("Introduce el Título:")
    overview_input = st.text_input("Introduce la Sinopsis/Resumen:")
    production_company_input = st.text_input("Introduce la Productora:")
    filter_adults = st.checkbox("Incluir contenido para adultos")

    # Botón para activar la búsqueda
    if st.button("Buscar"):
        # Ejecutar la consulta SQL solo cuando se presione el botón
        df = fetch_filtered_data(genre_input, title_input, overview_input, production_company_input, filter_adults)

        # Mostrar los resultados
        if not df.empty:
            st.markdown("### Resultados de la Búsqueda:")
            cols_per_row = 5
            cols = st.columns(cols_per_row)

            for index, row in df.iterrows():
                with cols[index % cols_per_row]:
                    image_url = f"https://image.tmdb.org/t/p/w500{row['poster_path']}" if pd.notna(row['poster_path']) else None
                    if image_url:
                        st.image(image_url, use_container_width=True)
                    release_year = str(row['release_date'])[:4] if pd.notna(row['release_date']) else "N/A"
                    
                    button_label = f"{row['title']} ({release_year})"
                    
                    # Convertimos la fila a un diccionario para evitar problemas al pasarla a session_state
                    movie_data = row.to_dict()
                    
                    if st.button(button_label, key=f"details_{index}"):
                        navigate("details", movie_data)
        else:
            st.warning("No se encontraron resultados para los criterios ingresados.")

# =================== Página de Detalles ===================
elif st.session_state.page == "details":
    movie = st.session_state.selected_movie

    if movie:
        base_url = "https://image.tmdb.org/t/p/w500"
        
        # =================== Mostrar Imagen de Fondo ===================
        backdrop_path = movie.get('backdrop_path')
        if backdrop_path:
            st.image(base_url + backdrop_path, use_column_width=True)

        # =================== Diseño en Dos Columnas ===================
        col1, col2 = st.columns([1, 2])  # La segunda columna es más grande para los detalles

        with col1:
            poster_path = movie.get('poster_path')
            if poster_path:
                st.image(base_url + poster_path, width=250)  # Imagen más pequeña
            else:
                st.warning("No hay imagen disponible.")

        with col2:
            st.markdown(f"# {movie['title']} ({str(movie['release_date'])[:4] if movie.get('release_date') else 'N/A'})")
            st.markdown(f"**Rating:** {movie['vote_average']:.2f} ⭐ ({movie['vote_count']} votos)")
            st.markdown(f"**Idioma original:** {movie['original_language'].upper() if movie.get('original_language') else 'N/A'}")
            st.markdown(f"**Duración:** {movie['runtime'] if movie.get('runtime') else 'N/A'} minutos")
            st.markdown(f"**Popularidad:** {movie['popularity'] if movie.get('popularity') else 'N/A'}")
            st.markdown(f"**Estado:** {movie['status'] if movie.get('status') else 'N/A'}")
            st.markdown(f"**Presupuesto:** ${movie['budget']:,.0f}" if movie.get('budget') else "No disponible")
            st.markdown(f"**Géneros:** {movie['genres'] if movie.get('genres') else 'No disponible'}")

            # =================== Sinopsis ===================
            st.markdown(f"### Descripción")
            st.markdown(movie['overview'] if movie.get('overview') else "No disponible")

        # =================== Botón para volver a la lista ===================
        if st.button("Volver a la lista"):
            navigate("home")
