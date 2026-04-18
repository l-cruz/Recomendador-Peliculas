from typing import Optional

from src.application.add_favorite import AddFavorite
from src.application.get_movie_details import GetMovieDetails
from src.application.get_stats import GetStats
from src.application.recommend_from_favorites import RecommendFromFavorites
from src.application.recommend_movies import RecommendMovies
from src.application.remove_favorite import RemoveFavorite
from src.application.save_movie import SaveMovie
from src.application.search_in_db import SearchInDB
from src.application.search_movies import SearchMovies
from src.infrastructure.user_repository import UserRepository


def separador(titulo: str = "") -> None:
    ancho = 60
    if titulo:
        print(f"\n{'─' * 3} {titulo} {'─' * max(ancho - len(titulo) - 5, 0)}")
    else:
        print("─" * ancho)


def obtener_ano(movie: dict) -> str:
    if movie.get("release_year"):
        return str(movie["release_year"])

    release_date = movie.get("release_date") or "?"
    if isinstance(release_date, str) and len(release_date) >= 4:
        return release_date[:4]
    return "?"


def seleccionar_usuario(user_repo: UserRepository) -> Optional[str]:
    usuarios = user_repo.list_users()
    if not usuarios:
        print("\nNo hay usuarios. Crea uno primero (opción 7).")
        return None

    print("\nUsuarios disponibles:")
    for i, usuario in enumerate(usuarios, 1):
        print(f"  {i}. {usuario['name']} (id: {usuario['_id']})")

    try:
        idx = int(input("Elige un usuario: ").strip()) - 1
        return str(usuarios[idx]["_id"])
    except (ValueError, IndexError):
        print("Selección inválida.")
        return None


# -------------------------------------------------
# TU FLUJO ORIGINAL, CONSERVADO COMO DEMO BASE
# -------------------------------------------------
def opcion_demo_original() -> None:
    separador("DEMO ORIGINAL DEL PROYECTO")

    # caso aislado de buscador de películas
    query = input("Introduce el título a buscar: ").strip()
    if not query:
        print("Debes introducir un título.")
        return

    search_use_case = SearchMovies()
    search_result = search_use_case.execute(query=query)

    if search_result.get("results"):
        top_results = search_result["results"][:5]
        for i, movie in enumerate(top_results, 1):
            date = movie.get("release_date", "Fecha desconocida")
            print(f"{i}. {movie['title']} ({date})")

        try:
            choice = int(input("\nElige el número de la película correcta: ").strip())
            selected_movie = top_results[choice - 1]
        except (ValueError, IndexError):
            print("Selección inválida.")
            return

        movie_id = selected_movie["id"]
        print(f"\nHas seleccionado: {selected_movie['title']} (ID: {movie_id})")
    else:
        print("No se encontraron resultados.\n")
        return

    # conseguir más características de la película
    print(f"\nObteniendo detalles extendidos para el ID {movie_id}")
    details_use_case = GetMovieDetails()
    details_result = details_use_case.execute(movie_id=movie_id)

    print(f"Título original: {details_result.get('original_title')}")
    overview = details_result.get("overview") or ""
    print(f"Sinopsis: {overview[:60]}..." if overview else "Sinopsis: No disponible")
    print(f"Videos encontrados: {len(details_result.get('videos', {}).get('results', []))}")
    print(f"Imágenes encontradas: {len(details_result.get('images', {}).get('backdrops', []))}")

    # guardar esa película en concreto
    guardar = input("\n¿Quieres guardar esta película en MongoDB? (s/n): ").strip().lower()
    if guardar == "s":
        print("Guardando la película en MongoDB...")
        save_use_case = SaveMovie()
        save_use_case.execute(movie_data=details_result)
        print("Película guardada correctamente.")

    # caso práctico de uso ejemplo
    recommend_use_case = RecommendMovies()
    target_genre = input("\nIntroduce un género para recomendar (ej: Fantasía): ").strip()
    target_year = input("Introduce un año (ej: 2003): ").strip()

    if not target_genre:
        print("Debes indicar al menos un género.")
        return

    print(f"\nBuscando las mejores películas de {target_genre} del año {target_year} en la base de datos...")
    recommendations = recommend_use_case.execute(
        genre=target_genre,
        year=target_year if target_year else None
    )

    if recommendations:
        print(f"\nTOP de {target_genre}" + (f" en {target_year}" if target_year else ""))
        for i, movie in enumerate(recommendations, 1):
            date = movie.get("release_date", "Fecha desconocida")
            print(f"{i}. {movie['title']} ({date}) - Puntuación: {movie['vote_average']}")
    else:
        print(f"\nNo tienes películas de {target_genre}" + (f" del {target_year}" if target_year else "") + " guardadas.")


# -------------------------------------------------
# NUEVAS OPCIONES V2
# -------------------------------------------------
def opcion_buscar_local() -> list:
    separador("BUSCAR EN CATÁLOGO LOCAL")
    query = input("Buscar: ").strip()
    if not query:
        return []

    search_uc = SearchInDB()
    resultados = search_uc.execute(query=query)

    if not resultados:
        print("No se encontraron resultados en tu catálogo local.")
        return []

    print(f"\n{len(resultados)} resultados encontrados:\n")
    for i, movie in enumerate(resultados, 1):
        ano = obtener_ano(movie)
        nota = movie.get("vote_average", 0)
        relevancia = round(movie.get("relevancia", 0), 2)
        generos = ", ".join(movie.get("genres", []))
        print(f"  {i}. {movie['title']} ({ano}) - {generos} | ⭐{nota}")
        print(f"     Relevancia: {relevancia} | tmdb_id: {movie['tmdb_id']}")

    return resultados


def opcion_añadir_favorita(user_repo: UserRepository) -> None:
    separador("AÑADIR A FAVORITAS")
    user_id = seleccionar_usuario(user_repo)
    if not user_id:
        return

    print("\nBusca primero la película en el catálogo local:")
    resultados = opcion_buscar_local()
    if not resultados:
        return

    try:
        idx = int(input("\nElige la película a añadir: ").strip()) - 1
        pelicula = resultados[idx]
    except (ValueError, IndexError):
        print("Selección inválida.")
        return

    puntuacion_str = input(
        f"Tu puntuación personal para '{pelicula['title']}' (1-10, Enter para omitir): "
    ).strip()

    if puntuacion_str:
        if not puntuacion_str.isdigit() or not (1 <= int(puntuacion_str) <= 10):
            print("La puntuación debe estar entre 1 y 10.")
            return
        personal_rating = int(puntuacion_str)
    else:
        personal_rating = None

    add_uc = AddFavorite()
    resultado = add_uc.execute(
        user_id=user_id,
        tmdb_id=pelicula["tmdb_id"],
        personal_rating=personal_rating
    )
    print(resultado["mensaje"])


def opcion_quitar_favorita(user_repo: UserRepository) -> None:
    separador("QUITAR DE FAVORITAS")
    user_id = seleccionar_usuario(user_repo)
    if not user_id:
        return

    favoritas = user_repo.get_favorites(user_id)
    if not favoritas:
        print("No tienes películas en favoritas.")
        return

    print("\nTus favoritas actuales:")
    for i, favorite in enumerate(favoritas, 1):
        rating = favorite.get("personal_rating")
        rating_str = f" [{rating}/10]" if rating else ""
        print(f"  {i}. {favorite['title']}{rating_str} (tmdb_id: {favorite['tmdb_id']})")

    try:
        idx = int(input("\nElige la película a quitar: ").strip()) - 1
        tmdb_id = favoritas[idx]["tmdb_id"]
    except (ValueError, IndexError):
        print("Selección inválida.")
        return

    remove_uc = RemoveFavorite()
    resultado = remove_uc.execute(user_id=user_id, tmdb_id=tmdb_id)
    print(resultado["mensaje"])


def opcion_recomendar_desde_favoritas(user_repo: UserRepository) -> None:
    separador("RECOMENDACIONES PERSONALIZADAS")
    user_id = seleccionar_usuario(user_repo)
    if not user_id:
        return

    favoritas = user_repo.get_favorites(user_id)
    if not favoritas:
        print("\nNo tienes películas en favoritas. Añade algunas primero (opción 3).")
        return

    recommend_uc = RecommendFromFavorites()
    resultado = recommend_uc.execute(user_id=user_id, limit=10)

    print("\nTU PERFIL DE GUSTOS:")
    for genre in resultado["perfil_generos"]:
        barra = "█" * genre["frecuencia"]
        print(f"  {genre['genero']:<15} {barra} ({genre['frecuencia']})")

    print("\nRECOMENDACIONES PARA TI:")
    recomendaciones = resultado["recomendaciones"]
    if recomendaciones:
        for i, movie in enumerate(recomendaciones, 1):
            generos = ", ".join(movie.get("genres", []))
            ano = obtener_ano(movie)
            nota = movie.get("vote_average", 0)
            coincidencias = movie.get("generos_coincidentes", 0)
            print(f"  {i}. {movie['title']} ({ano})")
            print(f"     ⭐{nota} | {generos} | {coincidencias} géneros coinciden")
    else:
        print("No hay suficientes películas en el catálogo.")
        print("Ejecuta fill_db.py para ampliar el catálogo.")

    genres = [genre["genero"] for genre in resultado["perfil_generos"]]
    tmdb_ids = [movie["tmdb_id"] for movie in recomendaciones]
    user_repo.save_recommendation_history(user_id, genres, tmdb_ids)
    print("\nRecomendación guardada en el historial del usuario.")


def opcion_estadisticas() -> None:
    separador("ESTADÍSTICAS DEL CATÁLOGO")
    stats_uc = GetStats()
    stats = stats_uc.execute()

    if not stats:
        print("No hay datos en el catálogo. Ejecuta fill_db.py primero.")
        return

    global_data = stats.get("nota_media_global", [{}])[0]
    total = global_data.get("total_peliculas", 0)
    media = round(global_data.get("media", 0), 2)
    mejor = global_data.get("mejor_nota", 0)
    print(f"\nCATÁLOGO: {total} películas | Nota media: ⭐{media} | Mejor: ⭐{mejor}")

    print("\nTOP GÉNEROS:")
    for genre in stats.get("top_generos", []):
        barra = "█" * min(genre["total"], 30)
        print(f"  {genre['_id']:<18} {barra} {genre['total']}")

    print("\nPOR DÉCADA:")
    for decade in stats.get("por_decada", []):
        nota = round(decade.get("nota_media", 0), 1)
        print(f"  {decade['_id']}s -> {decade['total']} películas | Nota media: ⭐{nota}")

    print("\nMEJOR VALORADAS:")
    for i, movie in enumerate(stats.get("mejor_valoradas", []), 1):
        print(f"  {i}. {movie['title']} ({obtener_ano(movie)}) - ⭐{movie['vote_average']}")

    print("\nNOTA MEDIA POR GÉNERO (mín. 5 películas):")
    for genre in stats.get("nota_por_genero", []):
        nota = round(genre["nota_media"], 2)
        print(f"  {genre['_id']:<18} ⭐{nota} ({genre['total']} películas)")


def opcion_gestionar_usuarios(user_repo: UserRepository) -> None:
    separador("GESTIONAR USUARIOS")
    print("  1. Crear nuevo usuario")
    print("  2. Listar usuarios")
    print("  3. Ver favoritas de un usuario")

    opcion = input("\nElige: ").strip()

    if opcion == "1":
        name = input("Nombre del usuario: ").strip()
        if not name:
            print("El nombre no puede estar vacío.")
            return

        user_id = user_repo.create_user(name)
        print(f"Usuario '{name}' disponible con id: {user_id}")

    elif opcion == "2":
        usuarios = user_repo.list_users()
        if usuarios:
            for usuario in usuarios:
                print(f"  - {usuario['name']} — {usuario['_id']}")
        else:
            print("No hay usuarios todavía.")

    elif opcion == "3":
        user_id = seleccionar_usuario(user_repo)
        if not user_id:
            return

        favoritas = user_repo.get_favorites(user_id)
        if favoritas:
            print(f"\n{len(favoritas)} favoritas:")
            for favorite in favoritas:
                rating = favorite.get("personal_rating")
                rating_str = f" [{rating}/10]" if rating else ""
                fecha = str(favorite.get("added_at", ""))[:10]
                print(f"  - {favorite['title']}{rating_str} (añadida: {fecha})")
        else:
            print("No tiene favoritas todavía.")

    else:
        print("Opción no válida.")


def main() -> None:
    user_repo = UserRepository()

    while True:
        print("\n" + "═" * 60)
        print("           RECOMENDADOR DE PELÍCULAS")
        print("═" * 60)
        print("  1. Demo original del proyecto")
        print("  2. Buscar en mi catálogo local (full-text)")
        print("  3. Añadir película a mis favoritas")
        print("  4. Quitar película de mis favoritas")
        print("  5. Recomendaciones basadas en mis favoritas")
        print("  6. Estadísticas del catálogo")
        print("  7. Gestionar usuarios")
        print("  0. Salir")
        print("─" * 60)

        opcion = input("Elige una opción: ").strip()

        if opcion == "1":
            opcion_demo_original()
        elif opcion == "2":
            opcion_buscar_local()
        elif opcion == "3":
            opcion_añadir_favorita(user_repo)
        elif opcion == "4":
            opcion_quitar_favorita(user_repo)
        elif opcion == "5":
            opcion_recomendar_desde_favoritas(user_repo)
        elif opcion == "6":
            opcion_estadisticas()
        elif opcion == "7":
            opcion_gestionar_usuarios(user_repo)
        elif opcion == "0":
            print("\nHasta luego.\n")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    main()