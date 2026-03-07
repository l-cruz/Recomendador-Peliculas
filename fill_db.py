import time
from src.application.discover_movies import DiscoverMovies
from src.application.get_movie_details import GetMovieDetails
from src.application.save_movie import SaveMovie


def fill_db(pages_to_download: int = 10):
    discover_use_case = DiscoverMovies()
    details_use_case = GetMovieDetails()
    save_use_case = SaveMovie()
    total_saved = 0

    for page in range(1, pages_to_download + 1):
        print(f"\nDescargando página {page}...")

        discover_result = discover_use_case.execute(page=page)
        movie_list = discover_result.get('results', [])

        for movie in movie_list:
            try:
                details = details_use_case.execute(movie_id=movie["id"])
                save_use_case.execute(movie_data=details)

                total_saved += 1
                print(f"{total_saved}. Guardada: {movie['title']}")

            except Exception as e:
                print(f"Error con la película {movie.get('title')}: {e}")

        time.sleep(3)

    print(f"\nSe han añadido {total_saved} películas a tu MongoDB.")


if __name__ == "__main__":
    fill_db(pages_to_download=50)