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
def filter_top_movies(df, genre, title, overview, company):
    """Filtra y ordena las 10 mejores películas según el género, título, overview y compañía de producción"""
    filtered_movies = df.copy()

    if genre:
        filtered_movies = filtered_movies[filtered_movies['genres'].str.contains(genre, case=False, na=False)]
    if title:
        filtered_movies = filtered_movies[filtered_movies['title'].str.contains(title, case=False, na=False)]
    if overview:
        filtered_movies = filtered_movies[filtered_movies['overview'].str.contains(overview, case=False, na=False)]
    if company:
        filtered_movies = filtered_movies[filtered_movies['production_companies'].str.contains(company, case=False, na=False)]

    top_movies = filtered_movies.sort_values(by='vote_average', ascending=False).head(10)
    if not top_movies.empty:
        base_url = "https://image.tmdb.org/t/p/w500"
        top_movies['image_url'] = base_url + top_movies['poster_path']
        return top_movies[top_movies['image_url'].notna()]
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
if "search_company" not in st.session_state:
    st.session_state.search_company = ""
if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False

def navigate(page, movie=None):
    st.session_state.page = page
    st.session_state.selected_movie = movie
    st.rerun()

# =================== Página Principal ===================
if st.session_state.page == "home":
    genre_input = st.text_input("Introduce el Género:", st.session_state.search_genre)
    title_input = st.text_input("Introduce el Título:", st.session_state.search_title)
    overview_input = st.text_input("Introduce el Overview:", st.session_state.search_overview)
    company_input = st.text_input("Introduce la Compañía de Producción:", st.session_state.search_company)

    # Botón para activar la búsqueda
    if st.button("Buscar"):
        st.session_state.search_genre = genre_input
        st.session_state.search_title = title_input
        st.session_state.search_overview = overview_input
        st.session_state.search_company = company_input
        st.session_state.search_triggered = True

    # Solo realizar la búsqueda si se ha presionado el botón "Buscar"
    if st.session_state.search_triggered:
        query = f"SELECT * FROM {table}"
        df = fetch_data(query)
        top_movies = filter_top_movies(df, st.session_state.search_genre, st.session_state.search_title, st.session_state.search_overview, st.session_state.search_company)

        if not top_movies.empty:
            cols_per_row = 5
            cols = st.columns(cols_per_row)

            for index, row in enumerate(top_movies.itertuples()):
                with cols[index % cols_per_row]:
                    st.image(row.image_url, use_container_width=True)
                    
                    # ✅ Corrección: Evitar error si release_date es None o no es un string
                    release_year = str(row.release_date)[:4] if row.release_date else "N/A"
                    
                    button_label = f"{row.title} ({release_year})"
                    if st.button(button_label, key=row.Index):
                        navigate("details", row)
        else:
            st.warning("No se encontraron resultados para los criterios ingresados.")
    else:
        st.info("Introduce un género, título, overview o compañía y presiona 'Buscar' para ver los resultados.")

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
            st.markdown(f"# {movie.title} ({str(movie.release_date)[:4] if movie.release_date else 'N/A'})")
            st.markdown(f"**Rating:** {movie.vote_average:.2f} ⭐ ({movie.vote_count} votos)")
            st.markdown(f"**Idioma original:** {movie.original_language.upper() if movie.original_language else 'N/A'}")
            st.markdown(f"**Duración:** {movie.runtime if movie.runtime else 'N/A'} minutos")
            st.markdown(f"**Presupuesto:** ${movie.budget:,}")
            st.markdown(f"**Ingresos:** ${movie.revenue:,}")
            st.markdown(f"**Estado:** {movie.status if movie.status else 'N/A'}")
            st.markdown(f"**Para adultos:** {'Sí' if movie.adult else 'No'}")
            st.markdown(f"**Géneros:** {movie.genres if movie.genres else 'No disponible'}")
            st.markdown(f"**Compañías de producción:** {movie.production_companies if movie.production_companies else 'No disponible'}")

            # =================== Sinopsis ===================
            st.markdown(f"### Descripción")
            st.markdown(movie.overview if movie.overview else "No disponible")

        # =================== Mostrar Información Adicional ===================
        st.markdown("---")  # Línea divisoria para separar el contenido

        # =================== Mostrar el tagline si está disponible ===================
        if movie.tagline:
            st.markdown(f"**Tagline:** *{movie.tagline}*")

        # =================== Botón para volver a la lista ===================
        if st.button("Volver a la lista"):
            navigate("home")
    else:
        st.warning("No se ha seleccionado ninguna película.")
        if st.button("Volver a la lista"):
            navigate("home")
