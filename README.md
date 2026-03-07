# Movie Recommender (TMDB + MongoDB)

Una aplicación interactiva de consola desarrollada en Python. Se conecta a la API de TMDB para buscar y descubrir películas, guarda los detalles estructurados en una base de datos NoSQL (MongoDB Atlas) y cuenta con un motor de recomendación local basado en géneros y años de lanzamiento.

El proyecto está diseñado siguiendo los principios de **Clean Architecture**, separando claramente la infraestructura, la lógica de aplicación (Casos de Uso) y el dominio.

## 🚀 Características Principales

* **Búsqueda Interactiva:** Busca películas por título conectándose a TMDB y permite al usuario elegir la opción correcta entre las coincidencias.
* **Extracción de Detalles:** Obtiene datos enriquecidos (sinopsis, géneros, fechas, puntuación, etc.) usando el parámetro `append_to_response` de la API.
* **Almacenamiento en la Nube:** Guarda las películas seleccionadas en un clúster gratuito de MongoDB Atlas, evitando duplicados mediante operaciones `upsert`.
* **Motor de Recomendación:** Filtra y recomienda las mejores películas de tu base de datos local según el género y el año indicados por el usuario.
* **Población Masiva (Scraping):** Incluye un script (`fill_db.py`) para descargar cientos de películas populares de golpe y crear un catálogo inicial robusto.

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.12
* **Base de Datos:** MongoDB Atlas (con la librería `pymongo`)
* **API Externa:** The Movie Database (TMDB) API v3 (`requests`)
* **Variables de Entorno:** `python-dotenv` para la gestión segura de credenciales.

## ⚙️ Instalación y Configuración

1. **Clona el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/Recomendador-Peliculas.git](https://github.com/tu-usuario/Recomendador-Peliculas.git)
   cd Recomendador-Peliculas
