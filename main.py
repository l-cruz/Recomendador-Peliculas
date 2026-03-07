from src.application.search_movies import SearchMovies
from src.application.get_movie_details import GetMovieDetails
from src.application.discover_movies import DiscoverMovies
from src.application.save_movie import SaveMovie
from src.application.recommend_movies import RecommendMovies

def main():

#caso aislado de buscador de películas
    search_use_case = SearchMovies()
    search_result = search_use_case.execute(query="El Señor de los Anillos3")

    if search_result.get("results"):
        top_results = search_result["results"][:5]
        for i, movie in enumerate(top_results, 1):
            date = movie.get('release_date', 'Fecha desconocida')
            print(f"{i}. {movie['title']} ({date})")
        choice = int(input("\nElige el número de la película correcta: "))
        selected_movie = top_results[choice - 1]
        movie_id = selected_movie["id"]
        print(f"\nHas seleccionado: {selected_movie['title']} (ID: {movie_id})")
    else:
        print("No se encontraron resultados.\n")
        return

#conseguir más característica de la película
    print(f"Obteniendo detalles extendidos para el ID {movie_id}")
    details_use_case = GetMovieDetails()
    details_result = details_use_case.execute(movie_id=movie_id)

    print(f"Título original: {details_result.get('original_title')}")
    print(f"Sinopsis: {details_result.get('overview')[:60]}...")
    print(f"Videos encontrados: {len(details_result.get('videos', {}).get('results', []))}")
    print(f"Imágenes encontradas: {len(details_result.get('images', {}).get('backdrops', []))}\n")

#para guardar esa película en concreto
    print("Guardando la película en MongoDB")
    save_use_case = SaveMovie()
    save_use_case.execute(movie_data=details_result)

#caso práctico de uso ejemplo
    recommend_use_case = RecommendMovies()
    target_genre = "Fantasía"
    target_year = "2003"

    print(f"Buscando las mejores películas de {target_genre} del año {target_year} en la base de datos")
    recommendations = recommend_use_case.execute(genre=target_genre, year=target_year)

    if recommendations:
        print(f"\nTOP de {target_genre} en {target_year}")
        for i, movie in enumerate(recommendations, 1):
            date = movie.get('release_date', 'Fecha desconocida')
            print(f"{i}. {movie['title']} ({date}) - Puntuación: {movie['vote_average']}")
    else:
        print(f"\nNo tienes películas de {target_genre} del {target_year} guardadas.")

if __name__ == "__main__":
    main()