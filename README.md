# Recomendador de Películas — TMDB + MongoDB

Aplicación de escritorio en Python que conecta la API de TMDB con MongoDB Atlas para buscar, guardar y recomendar películas de forma personalizada.

El proyecto permite construir un catálogo local de películas, gestionar usuarios, guardar películas favoritas con puntuación personal y generar recomendaciones basadas en los gustos del usuario.

---

## Tecnologías

- Python 3.12
- MongoDB Atlas
- PyMongo
- TMDB API v3
- Tkinter
- python-dotenv
- requests

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/l-cruz/Recomendador-Peliculas.git
cd Recomendador-Peliculas
```

### 2. Crear y activar un entorno virtual

En macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un fichero `.env` en la raíz del proyecto:

```env
MONGO_URI=mongodb+srv://usuario:contraseña@cluster.mongodb.net/
TMDB_ACCESS_TOKEN=tu_token_de_acceso_tmdb
```

---

## Uso

### Poblar la base de datos

Antes de usar la aplicación, conviene descargar un catálogo inicial de películas desde TMDB.

```bash
python fill_db.py
```

Si has dejado `fill_db.py` con argumentos configurables, también puedes usar:

```bash
python fill_db.py --start 1 --end 50
```

### Crear un usuario de prueba

```bash
python create_sample_user.py
```

### Arrancar la aplicación

```bash
python main.py
```

---

## Funcionalidades principales

| Función | Descripción |
|---|---|
| Buscar en TMDB | Busca películas en tiempo real usando la API de TMDB. |
| Buscar en Catálogo | Busca películas ya almacenadas en MongoDB mediante índice de texto. |
| Mi Catálogo | Muestra las películas guardadas por el usuario usando `$lookup`. |
| Mis Favoritas | Muestra favoritas con puntuación personal y datos de película. |
| Recomendar Género | Recomienda películas por género usando valoración, año y número de votos. |
| Recomendaciones IA | Genera recomendaciones basadas en géneros favoritos y notas personales. |
| Añadir Favorita | Añade una película a favoritas con nota personal del 1 al 10. |
| Quitar Favorita | Elimina una película de la lista de favoritas. |
| Editar Mi Nota | Permite actualizar la puntuación personal de una favorita. |
| Mis Estadísticas | Calcula estadísticas personalizadas del usuario con `$lookup` y `$facet`. |
| Stats del Catálogo | Muestra estadísticas globales del catálogo local. |

---

## Arquitectura del proyecto

El proyecto está organizado siguiendo una separación sencilla entre aplicación, infraestructura y presentación.

```text
.
├── main.py
├── gui_app.py
├── fill_db.py
├── create_sample_user.py
├── requirements.txt
├── src
│   ├── application
│   │   ├── add_favorite.py
│   │   ├── get_movie_details.py
│   │   ├── get_user_stats.py
│   │   ├── recommend_from_favorites.py
│   │   ├── recommend_movies.py
│   │   ├── remove_favorite.py
│   │   ├── save_movie.py
│   │   ├── search_movies.py
│   │   └── update_favorite_rating.py
│   └── infrastructure
│       ├── db_connection.py
│       ├── mongo_client.py
│       ├── tmdb_client.py
│       └── user_repository.py
```

---

## Colecciones MongoDB

### `peliculas`

Almacena las películas descargadas desde TMDB.

Campos principales:

- `tmdb_id`
- `title`
- `overview`
- `genres`
- `release_date`
- `release_year`
- `vote_average`
- `vote_count`
- `popularity`
- `runtime`
- `poster_path`

### `usuarios`

Almacena usuarios, catálogo personal y favoritas.

Estructura aproximada:

```json
{
  "_id": "...",
  "name": "Usuario Demo",
  "my_catalog": [550, 155, 13],
  "favorites": [
    {
      "tmdb_id": 550,
      "personal_rating": 9,
      "added_at": "..."
    }
  ]
}
```

### `fill_progress`

Registra el progreso de descarga para poder reanudar la carga de películas sin duplicar trabajo.

---

## Índices MongoDB

### Índices en `peliculas`

| Índice | Campos | Uso |
|---|---|---|
| `idx_tmdb_id` | `tmdb_id` único | Evita duplicados y permite búsquedas rápidas por ID. |
| `idx_fulltext` | `title`, `overview` | Permite búsqueda de texto completo. |
| `idx_genres_year_score` | `genres`, `vote_count`, `release_year`, `vote_average` | Optimiza recomendaciones por género, votos, año y valoración. |
| `idx_popularity` | `popularity` descendente | Ordenación por popularidad. |
| `idx_rating_count` | `vote_average`, `vote_count` descendente | Consultas de películas mejor valoradas. |

### Índices en `usuarios`

| Índice | Campos | Uso |
|---|---|---|
| `idx_favorites_tmdb_id` | `favorites.tmdb_id` | Consulta y gestión de favoritas. |

---

## Recomendaciones personalizadas

El recomendador basado en favoritas construye un perfil del usuario combinando:

1. Frecuencia de aparición de cada género en sus favoritas.
2. Nota media personal del usuario para cada género.
3. Valoración media de TMDB como factor secundario.

De esta forma, si dos géneros aparecen con la misma frecuencia, tendrá más peso aquel que el usuario haya puntuado mejor.

---

## Estadísticas personales

La opción **Mis Estadísticas** calcula información personalizada a partir de las favoritas del usuario:

- Número de películas en catálogo.
- Número de favoritas.
- Nota media personal.
- Comparación con la nota media de TMDB.
- Géneros favoritos.
- Décadas más frecuentes.
- Película mejor puntuada.
- Película peor puntuada.

Estas estadísticas se calculan mediante agregaciones de MongoDB usando `$lookup`, `$group` y `$facet`.

---

## Ejecución recomendada

Flujo típico de uso:

```bash
pip install -r requirements.txt
python fill_db.py
python create_sample_user.py
python main.py
```

---

## Notas

- Es necesario disponer de una cuenta de MongoDB Atlas.
- Es necesario disponer de un token de acceso de TMDB.