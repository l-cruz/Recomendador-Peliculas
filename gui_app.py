import sys
import tkinter as tk
from tkinter import ttk

from src.application.add_favorite import AddFavorite
from src.application.get_user_stats import GetUserStats
from src.application.update_favorite_rating import UpdateFavoriteRating
from src.application.get_movie_details import GetMovieDetails
from src.application.get_stats import GetStats
from src.application.recommend_from_favorites import RecommendFromFavorites
from src.application.recommend_movies import RecommendMovies
from src.application.remove_favorite import RemoveFavorite
from src.application.save_movie import SaveMovie
from src.application.search_in_db import SearchInDB
from src.application.search_movies import SearchMovies
from src.infrastructure.mongo_client import MongoDBClient


class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title_text, message):
        super().__init__(parent)
        self.title(title_text)

        self.geometry("400x200")
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.configure(bg="#16213e")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.attributes("-topmost", True)
        self.focus_force()

        tk.Label(
            self, text=message, font=("Arial", 12, "bold"),
            bg="#16213e", fg="white"
        ).pack(pady=(30, 10))

        self.entry = tk.Entry(
            self, font=("Arial", 14), width=25, justify="center",
            bg="#1a1a2e", fg="white", insertbackground="white", relief="flat"
        )
        self.entry.pack(pady=10, ipady=5)
        self.entry.focus_set()

        self.bind("<Return>", lambda event: self.confirm())

        tk.Button(
            self, text="Aceptar", bg="#e94560", fg="white",
            font=("Arial", 10, "bold"), command=self.confirm,
            cursor="hand2", relief="flat", width=15
        ).pack(pady=(10, 0))

    def confirm(self):
        self.result = self.entry.get()
        self.destroy()


class MovieSelector(tk.Toplevel):
    def __init__(self, parent, title_text, item_list, is_login=False):
        super().__init__(parent)
        self.title(title_text)

        self.geometry("480x500")
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.configure(bg="#1a1a2e")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.attributes("-topmost", True)
        self.focus_force()

        self._names = []
        for item in item_list:
            name = item.get("name") or item.get("title") or "Sin título"
            year = f" ({item['release_date'][:4]})" if item.get("release_date") else ""
            rating = item.get("vote_average")
            rating_str = f" - Nota: {rating}/10" if rating else ""
            self._names.append(f" {name}{year}{rating_str}")

        self._current_indices = list(range(len(self._names)))

        tk.Label(
            self, text=title_text, font=("Arial", 13, "bold"),
            bg="#1a1a2e", fg="#e94560"
        ).pack(pady=(15, 5))

        search_frame = tk.Frame(self, bg="#1a1a2e")
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 5))

        self._search_var = tk.StringVar()
        self._search_var.trace("w", self._filter)

        tk.Entry(
            search_frame, textvariable=self._search_var,
            bg="#16213e", fg="white", insertbackground="white",
            font=("Arial", 10), relief="flat"
        ).pack(fill=tk.X, ipady=5)

        list_frame = tk.Frame(self, bg="#1a1a2e")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        self.listbox = tk.Listbox(
            list_frame, font=("Arial", 10), bg="#16213e", fg="white",
            selectbackground="#e94560", borderwidth=0, highlightthickness=0
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self._populate(self._current_indices)

        button_frame = tk.Frame(self, bg="#1a1a2e")
        button_frame.pack(pady=15)

        tk.Button(
            button_frame, text="Seleccionar", bg="#0f3460", fg="white",
            font=("Arial", 10, "bold"), command=self.confirm,
            width=15, pady=8
        ).pack(side=tk.LEFT, padx=5)

        if is_login:
            tk.Button(
                button_frame, text="Nuevo Usuario", bg="#4ecca3", fg="#1a1a2e",
                font=("Arial", 10, "bold"), command=self.create_new,
                width=15, pady=8
            ).pack(side=tk.LEFT, padx=5)

    def _populate(self, indices: list) -> None:
        self.listbox.delete(0, tk.END)
        self._current_indices = indices
        for i in indices:
            self.listbox.insert(tk.END, self._names[i])

    def _filter(self, *_) -> None:
        q = self._search_var.get().lower()
        if q:
            filtered = [i for i, n in enumerate(self._names) if q in n.lower()]
        else:
            filtered = list(range(len(self._names)))
        self._populate(filtered)

    def create_new(self) -> None:
        self.result = "NUEVO"
        self.destroy()

    def confirm(self) -> None:
        sel = self.listbox.curselection()
        if sel:
            self.result = self._current_indices[sel[0]]
        self.destroy()


class RecommenderWindow:
    def __init__(self, root, user_repo):
        self.root = root
        self.user_repo = user_repo
        self.current_user = None
        self.db_client = MongoDBClient()

        self.root.title("Recomendador de Películas")
        self.root.configure(bg="#1a1a2e")

        w = 800
        h = 750
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.btn_style = {
            "bg": "#0f3460", "fg": "white", "relief": "flat",
            "pady": 10, "font": ("Arial", 10, "bold"), "cursor": "hand2"
        }

        self.sidebar = tk.Frame(self.root, bg="#16213e", width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            self.sidebar, text="Mi Cartelera",
            font=("Arial", 18, "bold"), bg="#16213e", fg="#e94560"
        ).pack(pady=30)

        menu = [
            ("Buscar en TMDB", self.option_tmdb),
            ("Buscar en Catálogo", self.option_local_search),
            ("Mi Catálogo", self.option_view_all),
            ("Mis Favoritas", self.option_view_favorites),
            ("Recomendar Género", self.option_recommend_genre),
            ("Recomendaciones IA", self.option_recommend_favorites),
            ("Añadir Favorita", self.option_add_favorite),
            ("Quitar Favorita", self.option_remove_favorite),
            ("Editar Mi Nota", self.option_edit_rating),
            ("Mis Estadísticas", self.option_user_stats),
            ("Stats del Catálogo", self.option_catalog_stats),
            ("Cerrar Sesión", self._on_close),
        ]

        for text, command in menu:
            tk.Button(
                self.sidebar, text=text, command=command, **self.btn_style
            ).pack(fill=tk.X, padx=20, pady=5)

        self.txt_output = tk.Text(
            self.root, bg="#1a1a2e", fg="#4ecca3",
            font=("Consolas", 11), borderwidth=0, padx=25, pady=25
        )
        self.txt_output.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._original_stdout = sys.stdout
        sys.stdout = self
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.update()

        if not self.initial_login():
            self.root.destroy()
            return

        print(f"¡Hola {self.current_user['name']}! Bienvenido/a a tu espacio de cine.")

    def write(self, m: str) -> None:
        self.txt_output.insert(tk.END, m)
        self.txt_output.see(tk.END)

    def flush(self) -> None:
        pass

    def _on_close(self) -> None:
        if getattr(self, "_original_stdout", None) is not None:
            sys.stdout = self._original_stdout
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def initial_login(self) -> bool:
        users = self.user_repo.list_users()
        selector = MovieSelector(self.root, "Iniciar Sesión", users, is_login=True)
        self.root.wait_window(selector)
        if selector.result == "NUEVO":
            dialog = CustomDialog(self.root, "Registro", "Dime tu nombre:")
            self.root.wait_window(dialog)
            name = dialog.result
            if name:
                self.user_repo.create_user(name)
                return self.initial_login()
            return False
        elif isinstance(selector.result, int):
            self.current_user = users[selector.result]
            return True
        return False

    def print_movie(self, movie: dict) -> None:
        print("-" * 50)
        print(f"Título: {movie.get('title', 'Sin título')}")
        print(f"Año:    {movie.get('release_date', '????')[:4]}")
        print(f"Nota:   {movie.get('vote_average', 'N/A')} / 10", end="")
        if movie.get("vote_count"):
            print(f"  ({movie['vote_count']} votos)")
        else:
            print()

        raw_genres = movie.get('genres', [])
        clean_genres = [g['name'] if isinstance(g, dict) else str(g) for g in raw_genres]
        print(f"Géneros: {', '.join(clean_genres)}")

        if movie.get("runtime"):
            print(f"Duración: {movie.get('runtime')} min")
        print(f"\nSinopsis: {movie.get('overview', 'No hay descripción disponible.')}")
        print("-" * 50 + "\n")

    def show_action_menu(self, movie: dict) -> None:
        win = tk.Toplevel(self.root)
        win.title("Opciones de Película")

        win.geometry("300x380")
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        x = (win.winfo_screenwidth() // 2) - (w // 2)
        y = (win.winfo_screenheight() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

        win.configure(bg="#16213e")
        win.transient(self.root)
        win.grab_set()

        win.attributes("-topmost", True)
        win.focus_force()

        tk.Label(
            win, text=movie.get("title", "Sin título"),
            font=("Arial", 12, "bold"), bg="#16213e", fg="white",
            wraplength=260
        ).pack(pady=15)

        def view_details():
            movie_id = movie.get("id") or movie.get("tmdb_id")
            details = self.db_client.collection.find_one(
                {"tmdb_id": movie_id},
                {"_id": 0}
            )
            if not details:
                try:
                    details = GetMovieDetails().execute(movie_id=movie_id)
                except Exception as e:
                    print(f"Error obteniendo detalles de TMDB: {e}")
                    win.destroy()
                    return
            self.print_movie(details)
            win.destroy()

        def save():
            movie_id = movie.get("id") or movie.get("tmdb_id")
            already_exists = self.db_client.collection.find_one({"tmdb_id": movie_id})
            if not already_exists:
                try:
                    details = GetMovieDetails().execute(movie_id=movie_id)
                    SaveMovie().execute(movie_data=details)
                except Exception as e:
                    print(f"Error guardando la película desde TMDB: {e}")
                    win.destroy()
                    return
            uid = str(self.current_user["_id"])
            self.user_repo.add_to_my_catalog(uid, movie_id)
            print("¡Guardada en tu catálogo personal!")
            win.destroy()

        def fav():
            movie_id = movie.get("id") or movie.get("tmdb_id")
            already_exists = self.db_client.collection.find_one({"tmdb_id": movie_id})
            if not already_exists:
                try:
                    details = GetMovieDetails().execute(movie_id=movie_id)
                    SaveMovie().execute(movie_data=details)
                except Exception as e:
                    print(f"Error guardando la favorita desde TMDB: {e}")
                    win.destroy()
                    return
            uid = str(self.current_user["_id"])
            self.user_repo.add_to_my_catalog(uid, movie_id)
            dialog = CustomDialog(win, "Rating", "Tu nota (1-10):")
            win.wait_window(dialog)
            try:
                nota = int(dialog.result)
                if 1 <= nota <= 10:
                    res = AddFavorite().execute(
                        user_id=uid,
                        tmdb_id=movie_id,
                        personal_rating=nota
                    )
                    print(f"{res['mensaje']}")
                else:
                    print("La nota debe estar entre 1 y 10.")
            except (TypeError, ValueError):
                print("Nota no válida. Introduce un número entre 1 y 10.")
            win.destroy()

        btn_cfg = {**self.btn_style, "relief": "flat", "cursor": "hand2"}

        tk.Button(win, text="Ver Detalles", command=view_details, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Guardar en Catálogo", command=save, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Añadir a Favoritos", command=fav, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)

        tk.Button(
            win, text="Cancelar", command=win.destroy,
            bg="#e94560", fg="white", font=("Arial", 10, "bold"),
            pady=10, relief="flat", cursor="hand2"
        ).pack(fill=tk.X, padx=50, pady=5)

    def option_tmdb(self) -> None:
        dialog = CustomDialog(self.root, "TMDB", "¿Qué película quieres buscar?")
        self.root.wait_window(dialog)
        query = dialog.result
        if not query:
            return
        print(f"\nBuscando '{query}' en TMDB...")
        try:
            res = SearchMovies().execute(query=query)
        except Exception as e:
            print(f"Error de conexión con TMDB: {e}")
            print("Comprueba tu conexión a internet o el estado de la API.")
            return
        if res.get("results"):
            top = res["results"][:12]
            sel = MovieSelector(self.root, "Películas Encontradas", top)
            self.root.wait_window(sel)
            if isinstance(sel.result, int):
                self.show_action_menu(top[sel.result])
        else:
            print("No se encontraron resultados.")

    def option_local_search(self) -> None:
        dialog = CustomDialog(self.root, "Buscar Local", "Término de búsqueda:")
        self.root.wait_window(dialog)
        query = dialog.result
        if not query:
            return
        print(f"\nBuscando '{query}' en tu catálogo local...")
        results = SearchInDB().execute(query=query)
        if not results:
            print("Sin resultados en tu catálogo local.")
            return
        for movie in results:
            self.print_movie(movie)
        sel = MovieSelector(self.root, "Resultados Locales", results)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.show_action_menu(results[sel.result])

    def option_view_all(self) -> None:
        print("\n--- Tu Catálogo Personal ---")
        uid = str(self.current_user["_id"])
        my_movies = self.user_repo.get_my_catalog_with_details(uid)
        if not my_movies:
            print("Tu catálogo está vacío.")
            return
        print(f"Tienes {len(my_movies)} películas en tu catálogo.\n")
        for movie in my_movies:
            self.print_movie(movie)
        sel = MovieSelector(self.root, "Mi Colección Privada", my_movies)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.show_action_menu(my_movies[sel.result])

    def option_view_favorites(self) -> None:
        uid = str(self.current_user["_id"])
        favorites = self.user_repo.get_favorites_with_details(uid)
        if not favorites:
            print("No tienes favoritas todavía.")
            return
        print(f"\n{'=' * 50}")
        print(f"  Tus {len(favorites)} Favoritas")
        print(f"{'=' * 50}")
        for f in favorites:
            personal_rating = f.get("personal_rating", "N/A")
            tmdb_rating = f.get("vote_average", "?")
            year = str(f.get("release_year", ""))
            genres = ", ".join(f.get("genres") or [])
            print(f"  {f.get('title'):<40} {year}")
            print(f"     Tu nota: {personal_rating}/10  |  TMDB: {tmdb_rating}/10  |  {genres}")
        print(f"{'=' * 50}\n")

    def option_recommend_genre(self) -> None:
        dialog = CustomDialog(self.root, "Género", "Género (ej: Terror, Acción):")
        self.root.wait_window(dialog)
        genre = dialog.result
        if not genre:
            return
        print(f"\nBuscando el TOP en {genre}...")
        res = RecommendMovies().execute(genre=genre, limit=20)
        if not res:
            print(f"No hay películas de '{genre}' guardadas o ninguna tiene suficientes votos.")
            return
        for movie in res:
            self.print_movie(movie)
        sel = MovieSelector(self.root, f"Mejores de {genre.title()}", res)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.show_action_menu(res[sel.result])

    def option_recommend_favorites(self) -> None:
        uid = str(self.current_user["_id"])
        print("\n--- Recomendaciones basadas en tus favoritas ---")
        try:
            res = RecommendFromFavorites().execute(user_id=uid, limit=10)
        except Exception as e:
            print(f"Error generando recomendaciones: {e}")
            print("Revisa que tus favoritas existan también en la colección de películas.")
            return
        perfil = res.get("perfil_generos", [])
        recommendations = res.get("recomendaciones", [])
        if not perfil:
            print("Aún no hay suficientes favoritas para construir tu perfil.")
            return
        print("\nTu perfil de géneros:")
        for g in perfil:
            print(
                f"   {g['genero']}: "
                f"frecuencia={g['frecuencia']}, "
                f"nota media={g['nota_media_personal']}/10, "
                f"peso={g['peso']}"
            )
        if not recommendations:
            print("\nNo se encontraron recomendaciones nuevas.")
            return
        print("\nPelículas recomendadas:")
        for movie in recommendations:
            self.print_movie(movie)
        sel = MovieSelector(self.root, "Recomendaciones IA", recommendations)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.show_action_menu(recommendations[sel.result])

    def option_add_favorite(self) -> None:
        uid = str(self.current_user["_id"])
        ids = self.user_repo.get_my_catalog_ids(uid)
        if not ids:
            print("Catálogo vacío.")
            return
        my_movies = list(self.db_client.collection.find({"tmdb_id": {"$in": ids}}))
        sel = MovieSelector(self.root, "Añadir a Favoritos", my_movies)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            movie = my_movies[sel.result]
            dialog = CustomDialog(self.root, "Rating", "Tu nota (1-10):")
            self.root.wait_window(dialog)
            try:
                nota = int(dialog.result)
                if 1 <= nota <= 10:
                    res = AddFavorite().execute(user_id=uid, tmdb_id=movie["tmdb_id"], personal_rating=nota)
                    print(f"{res['mensaje']}")
                else:
                    print("La nota debe estar entre 1 y 10.")
            except (TypeError, ValueError):
                pass

    def option_remove_favorite(self) -> None:
        uid = str(self.current_user["_id"])
        favorites = self.user_repo.get_favorites(uid)
        if not favorites:
            print("No tienes favoritas.")
            return
        sel = MovieSelector(self.root, "Quitar de Favoritos", favorites)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            movie = favorites[sel.result]
            res = RemoveFavorite().execute(user_id=uid, tmdb_id=movie["tmdb_id"])
            print(f"{res['mensaje']}")

    def option_edit_rating(self) -> None:
        uid = str(self.current_user["_id"])
        favorites = self.user_repo.get_favorites(uid)
        if not favorites:
            print("No tienes favoritas.")
            return
        sel = MovieSelector(self.root, "¿Qué nota quieres cambiar?", favorites)
        self.root.wait_window(sel)
        if not isinstance(sel.result, int):
            return
        movie = favorites[sel.result]
        current_rating = movie.get("personal_rating", "sin nota")
        dialog = CustomDialog(
            self.root,
            "Nueva Nota",
            f"Nota actual: {current_rating}/10\nNueva nota (1-10):"
        )
        self.root.wait_window(dialog)
        try:
            new_rating = int(dialog.result)
            res = UpdateFavoriteRating().execute(
                user_id=uid,
                tmdb_id=movie["tmdb_id"],
                new_rating=new_rating
            )
            print(res["mensaje"])
        except (TypeError, ValueError):
            print("Nota no válida. Introduce un número entre 1 y 10.")

    def option_user_stats(self) -> None:
        uid = str(self.current_user["_id"])
        print("\n══════════ Tus Estadísticas Personales ══════════")
        stats = GetUserStats().execute(user_id=uid)
        if not stats:
            print("No hay datos suficientes todavía. Añade películas a favoritas primero.")
            return
        summary = stats.get("resumen", [{}])[0]
        total_favorites = summary.get("total_favoritas", 0)
        catalog_size = summary.get("catalog_size", 0)
        if total_favorites == 0:
            print("Aún no tienes favoritas. ¡Empieza a añadir películas!")
            return
        print(f"\nResumen de {self.current_user['name']}")
        print(f"   Películas en catálogo:   {catalog_size}")
        print(f"   Películas favoritas:     {total_favorites}")
        personal_rating = summary.get("nota_media_personal")
        tmdb_rating = summary.get("nota_media_tmdb")
        if personal_rating:
            print(f"   Tu nota media:          {round(personal_rating, 2)} / 10")
        if tmdb_rating:
            difference = round((personal_rating or 0) - tmdb_rating, 2)
            sign = "+" if difference > 0 else ""
            print(
                f"   Nota media TMDB:        {round(tmdb_rating, 2)} / 10 "
                f"(diferencia: {sign}{difference})"
            )
            if difference > 1:
                print("   → Eres más generoso/a que la media de TMDB.")
            elif difference < -1:
                print("   → Eres más exigente que la media de TMDB.")
            else:
                print("   → Tu criterio está en línea con la media de TMDB.")
        if stats.get("top_generos"):
            print("\nTus Géneros Favoritos")
            for genre in stats["top_generos"]:
                avg = genre.get("avg_personal_rating")
                avg_str = f"  (tu nota media: {round(avg, 1)}/10)" if avg else ""
                print(f"   {genre['_id']:<22} {genre['count']} película/s{avg_str}")
        if stats.get("por_decada"):
            print("\nTus Décadas Favoritas")
            for decade in stats["por_decada"]:
                print(f"   {decade['_id']}s  →  {decade['total']} película/s")
        best = stats.get("mejor_puntuada", [{}])
        worst = stats.get("peor_puntuada", [{}])
        if best and best[0].get("title"):
            movie = best[0]
            print(f"\nTu película favorita:    {movie['title']} ({movie['personal_rating']}/10)")
        if worst and worst[0].get("title"):
            movie = worst[0]
            print(f"Tu película menos fav.:  {movie['title']} ({movie['personal_rating']}/10)")
        print("\n" + "=" * 50 + "\n")

    def option_catalog_stats(self) -> None:
        print("\n══════════ Estadísticas del Catálogo ══════════")
        stats = GetStats().execute()
        if not stats:
            print("No hay datos suficientes aún.")
            return
        if stats.get("nota_media_global"):
            data = stats["nota_media_global"][0]
            print(f"\nResumen Global")
            print(f"   Total películas:  {data.get('total_peliculas')}")
            print(f"   Nota media:       {round(data.get('media', 0), 2)} / 10")
            print(f"   Mejor nota:       {data.get('mejor_nota')} / 10")
            print(f"   Peor nota:        {data.get('peor_nota')} / 10")
        if stats.get("top_generos"):
            print(f"\nTop 10 Géneros")
            for g in stats["top_generos"]:
                print(f"   {g['_id']:<22} {g['total']} películas")
        if stats.get("nota_por_genero"):
            print(f"\nGéneros Mejor Valorados (mín. 5 películas)")
            for g in stats["nota_por_genero"]:
                print(f"   {g['_id']:<22} {round(g['nota_media'], 2):>5} / 10  ({g['total']} pelis)")
        if stats.get("mejor_valoradas"):
            print(f"\nTop 5 Películas Mejor Valoradas")
            for i, movie in enumerate(stats["mejor_valoradas"], 1):
                year = movie.get("release_year") or (movie.get("release_date", "??")[:4])
                print(f"   {i}. {movie['title']:<42} {movie['vote_average']} ({year})")
        if stats.get("por_decada"):
            print(f"\nPelículas por Década")
            for d in stats["por_decada"]:
                bar = "#" * min(int(d["total"] / 10), 30)
                print(f"   {d['_id']}s  {bar} {d['total']} pelis  (media {round(d['nota_media'], 1)})")
        print("\n" + "=" * 46 + "\n")