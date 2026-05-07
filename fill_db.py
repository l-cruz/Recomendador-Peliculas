import time
from datetime import datetime, timezone

from src.application.discover_movies import DiscoverMovies
from src.application.get_movie_details import GetMovieDetails
from src.application.save_movie import SaveMovie
from src.infrastructure.db_connection import get_db

def fill_db(start_page: int = 1, end_page: int = 10):
    discover_use_case = DiscoverMovies()
    details_use_case = GetMovieDetails()
    save_use_case = SaveMovie()
    total_saved = 0

    progress_col = get_db()["fill_progress"]
    for page in range(start_page, end_page + 1):
        if progress_col.find_one({"page": page, "status": "done"}):
            print(f"Página {page} ya descargada, saltando...")
            continue
        print(f"\nDescargando página {page}...")

        try:
            discover_result = discover_use_case.execute(page=page)
            movie_list = discover_result.get("results", [])
            page_errors = 0

            for movie in movie_list:
                try:
                    details = details_use_case.execute(movie_id=movie["id"])
                    save_use_case.execute(movie_data=details)
                    total_saved += 1
                    print(f"{total_saved}. Guardada: {movie['title']}")
                except Exception as e:
                    page_errors += 1
                    print(f"Error con la película {movie.get('title')}: {e}")

            status = "done" if page_errors == 0 else "partial"
            progress_col.update_one(
                {"page": page},
                {
                    "$set": {
                        "status": status,
                        "saved_at": datetime.now(timezone.utc),
                        "movie_errors": page_errors,
                    }
                },
                upsert=True
            )

        except Exception as e:
            print(f"Error descargando la página {page}: {e}")
        time.sleep(3)
    print(f"\nSe han añadido/actualizado {total_saved} películas en tu MongoDB.")


if __name__ == "__main__":
    fill_db(start_page=101, end_page=200)