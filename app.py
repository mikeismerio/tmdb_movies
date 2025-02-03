import streamlit as st
import os
import sqlalchemy as sa
import pandas as pd

# =================== Configurar Página con Wide Mode ===================
st.set_page_config(page_title="Inicio", page_icon="🏠", layout="wide")

# =================== Configuración de Base de Datos ===================
server = "nwn7f7ze6vtuxen5age454nhca-colrz4odas5unhn7cagatohexq.datawarehouse.fabric.microsoft.com"
database = "TMDB"
driver = "ODBC Driver 17 for SQL Server"  # ✅ Corregido para usar ODBC 17
table = "tmdb_shows_clean"

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
    """Filtra y ordena los 10 mejores shows según el género, título, overview y network"""
    filtered_shows = df.copy()
    
    if genre:
        filtered_shows = filtered_shows[filtered_shows['genres'].str.contains(genre, case=False, na=False)]
    if title:
        filtered_shows = filtered_shows[filtered_shows['name'].str.contains(title, case=False, na=False)]
    if overview:
        filtered_shows = filtered_shows[filtered_shows['overview'].str.contains(overview, case=False, na=False)]
    if network:
        filtered_shows = filtered_shows[filtered_shows['networks'].str.contains(network, case=False, na=False)]
    
    top_shows = filtered_shows.sort_values(by='vote_average', ascending=False).head(10)
    if not top_shows.empty:
        base_url = "https://image.tmdb.org/t/p/w500"
        top_shows['image_url'] = base_url + top_shows['poster_path']
        return top_shows[top_shows['image_url'].notna()]
    return pd.DataFrame()

# =================== Control de Navegación ===================
if "page" not in st.session_state:
    st.session_state.page = "home"
    st.session_state.selected_movie = None
if "search_genre" not in st.session_state:
    st.session_state.search_genre = ""
if "search_title" not in st.session_state:
    st.session_state.search_title = ""
if "search_overview" not in st.session_state:
    st.session_state.search_overview = ""
if "search_network" not in st.session_state:
    st.session_state.search_network = ""
if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False

def navigate(page, movie=None):
    st.session_state.page = page
    st.session_state.selected_movie = movie
    st.rerun()

# =================== Página Principal ===================
if st.session_state.page == "home":
    query = f"SELECT * FROM {table}"
    df = fetch_data(query)

    genre_input = st.text_input("Introduce el Género:", st.session_state.search_genre)
    title_input = st.text_input("Introduce el Título:", st.session_state.search_title)
    overview_input = st.text_input("Introduce el Overview:", st.session_state.search_overview)
    network_input = st.text_input("Introduce la Red (Network):", st.session_state.search_network)

    # Botón para activar la búsqueda
    if st.button("Buscar"):
        st.session_state.search_genre = genre_input
        st.session_state.search_title = title_input
        st.session_state.search_overview = overview_input
        st.session_state.search_network = network_input
        st.session_state.search_triggered = True

    # Solo realizar la búsqueda si se ha presionado el botón "Buscar"
    if st.session_state.search_triggered:
        top_shows = filter_top_shows(df, st.session_state.search_genre, st.session_state.search_title, st.session_state.search_overview, st.session_state.search_network)

        if not top_shows.empty:
            cols_per_row = 5
            cols = st.columns(cols_per_row)

            for index, row in enumerate(top_shows.itertuples()):
                with cols[index % cols_per_row]:
                    st.image(row.image_url, use_container_width=True)
                    
                    # ✅ Corrección: Evitar error si first_air_date es None o no es un string
                    first_air_year = str(row.first_air_date)[:4] if hasattr(row, 'first_air_date') and row.first_air_date else "N/A"
                    
                    button_label = f"{row.name} ({first_air_year})"
                    if st.button(button_label, key=row.Index):
                        navigate("details", row)
        else:
            st.warning("No se encontraron resultados para los criterios ingresados.")
    else:
        st.info("Introduce un género, título, overview o red y presiona 'Buscar' para ver los resultados.")

# =================== Página de Detalles ===================
elif st.session_state.page == "details":
    if st.session_state.selected_movie:
        movie = st.session_state.selected_movie
        base_url = "https://image.tmdb.org/t/p/w500"

        # =================== Mostrar Imagen de Fondo ===================
        if hasattr(movie, 'backdrop_path') and movie.backdrop_path:
            st.image(base_url + movie.backdrop_path, use_column_width=True)

        # =================== Diseño en Dos Columnas ===================
        col1, col2 = st.columns([1, 2])  # La segunda columna es más grande para los detalles

        with col1:
            if hasattr(movie, 'poster_path') and movie.poster_path:
                st.image(base_url + movie.poster_path, width=250)  # Imagen más pequeña
            else:
                st.warning("No hay imagen disponible.")

        with col2:
            st.markdown(f"# {movie.name} ({str(movie.first_air_date)[:4] if hasattr(movie, 'first_air_date') and movie.first_air_date else 'N/A'})")
            st.markdown(f"**Rating:** {movie.vote_average:.2f} ⭐ ({movie.vote_count} votos)")
            st.markdown(f"**Idioma original:** {movie.original_language.upper() if hasattr(movie, 'original_language') else 'N/A'}")
            st.markdown(f"**Número de temporadas:** {movie.number_of_seasons if hasattr(movie, 'number_of_seasons') else 'N/A'}")
            st.markdown(f"**Número de episodios:** {movie.number_of_episodes if hasattr(movie, 'number_of_episodes') else 'N/A'}")
            st.markdown(f"**Popularidad:** {movie.popularity if hasattr(movie, 'popularity') else 'N/A'}")
            st.markdown(f"**Estado:** {movie.status if hasattr(movie, 'status') else 'N/A'}")
            st.markdown(f"**En producción:** {'Sí' if hasattr(movie, 'in_production') and movie.in_production else 'No'}")
            st.markdown(f"**Géneros:** {movie.genres if hasattr(movie, 'genres') else 'No disponible'}")
            st.markdown(f"**Creador(es):** {', '.join(movie.created_by) if hasattr(movie, 'created_by') and movie.created_by else 'No disponible'}")

            # =================== Sinopsis ===================
            st.markdown(f"### Descripción")
            st.markdown(movie.overview if hasattr(movie, 'overview') and movie.overview else "No disponible")

        # =================== Mostrar Información Adicional ===================
        st.markdown("---")  # Línea divisoria para separar el contenido

        # =================== Mostrar el reparto si está disponible ===================
        if hasattr(movie, 'cast') and movie.cast:
            st.markdown("### Reparto Principal")
            for actor in movie.cast[:5]:  # Mostrar solo los primeros 5 actores
                st.write(f"🎭 {actor}")

        # =================== Botón para volver a la lista ===================
        if st.button("Volver a la lista"):
            navigate("home")

    else:
        st.warning("No se ha seleccionado ninguna serie.")
        if st.button("Volver a la lista"):
            navigate("home")
