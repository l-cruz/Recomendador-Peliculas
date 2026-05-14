import sys
import tkinter as tk
from tkinter import ttk, simpledialog

from src.application.add_favorite import AddFavorite
from src.application.get_movie_details import GetMovieDetails
from src.application.get_stats import GetStats
from src.application.recommend_from_favorites import RecommendFromFavorites
from src.application.recommend_movies import RecommendMovies
from src.application.remove_favorite import RemoveFavorite
from src.application.save_movie import SaveMovie
from src.application.search_in_db import SearchInDB
from src.application.search_movies import SearchMovies
from src.infrastructure.mongo_client import MongoDBClient


class DialogoPersonalizado(tk.Toplevel):
    def __init__(self, parent, titulo, mensaje):
        super().__init__(parent)
        self.title(titulo)

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
            self, text=mensaje, font=("Arial", 12, "bold"),
            bg="#16213e", fg="white"
        ).pack(pady=(30, 10))

        self.entry = tk.Entry(
            self, font=("Arial", 14), width=25, justify="center",
            bg="#1a1a2e", fg="white", insertbackground="white", relief="flat"
        )
        self.entry.pack(pady=10, ipady=5)
        self.entry.focus_set()

        self.bind("<Return>", lambda event: self.confirmar())

        tk.Button(
            self, text="Aceptar", bg="#e94560", fg="white",
            font=("Arial", 10, "bold"), command=self.confirmar,
            cursor="hand2", relief="flat", width=15
        ).pack(pady=(10, 0))

    def confirmar(self):
        self.result = self.entry.get()
        self.destroy()


class SelectorPeliculas(tk.Toplevel):
    def __init__(self, parent, titulo, lista_items, es_login=False):
        super().__init__(parent)
        self.title(titulo)

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

        self._nombres = []
        for item in lista_items:
            nombre = item.get("name") or item.get("title") or "Sin título"
            year = f" ({item['release_date'][:4]})" if item.get("release_date") else ""
            nota = item.get("vote_average")
            str_nota = f" - Nota: {nota}/10" if nota else ""
            self._nombres.append(f" {nombre}{year}{str_nota}")

        self._current_indices = list(range(len(self._nombres)))

        tk.Label(
            self, text=titulo, font=("Arial", 13, "bold"),
            bg="#1a1a2e", fg="#e94560"
        ).pack(pady=(15, 5))

        frame_search = tk.Frame(self, bg="#1a1a2e")
        frame_search.pack(fill=tk.X, padx=20, pady=(0, 5))

        self._search_var = tk.StringVar()
        self._search_var.trace("w", self._filtrar)

        tk.Entry(
            frame_search, textvariable=self._search_var,
            bg="#16213e", fg="white", insertbackground="white",
            font=("Arial", 10), relief="flat"
        ).pack(fill=tk.X, ipady=5)

        frame_lista = tk.Frame(self, bg="#1a1a2e")
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=20)

        self.listbox = tk.Listbox(
            frame_lista, font=("Arial", 10), bg="#16213e", fg="white",
            selectbackground="#e94560", borderwidth=0, highlightthickness=0
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self._rellenar(self._current_indices)

        btn_frame = tk.Frame(self, bg="#1a1a2e")
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="Seleccionar", bg="#0f3460", fg="white",
            font=("Arial", 10, "bold"), command=self.confirmar,
            width=15, pady=8
        ).pack(side=tk.LEFT, padx=5)

        if es_login:
            tk.Button(
                btn_frame, text="Nuevo Usuario", bg="#4ecca3", fg="#1a1a2e",
                font=("Arial", 10, "bold"), command=self.crear_nuevo,
                width=15, pady=8
            ).pack(side=tk.LEFT, padx=5)

    def _rellenar(self, indices: list) -> None:
        self.listbox.delete(0, tk.END)
        self._current_indices = indices
        for i in indices:
            self.listbox.insert(tk.END, self._nombres[i])

    def _filtrar(self, *_) -> None:
        q = self._search_var.get().lower()
        if q:
            filtrados = [i for i, n in enumerate(self._nombres) if q in n.lower()]
        else:
            filtrados = list(range(len(self._nombres)))
        self._rellenar(filtrados)

    def crear_nuevo(self) -> None:
        self.result = "NUEVO"
        self.destroy()

    def confirmar(self) -> None:
        sel = self.listbox.curselection()
        if sel:
            self.result = self._current_indices[sel[0]]
        self.destroy()


class VentanaRecomendador:
    def __init__(self, root, user_repo):
        self.root = root
        self.user_repo = user_repo
        self.usuario_actual = None
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
            ("Buscar en TMDB", self.opcion_tmdb),
            ("Buscar en Catálogo", self.opcion_buscar_local),
            ("Mi Catálogo", self.opcion_ver_todo),
            ("Mis Favoritas", self.opcion_ver_favoritas),
            ("Recomendar Género", self.opcion_recomendar_genero),
            ("Recomendaciones IA", self.opcion_recomendar_favoritos),
            ("Añadir Favorita", self.opcion_add_fav),
            ("Quitar Favorita", self.opcion_remove_fav),
            ("Estadísticas", self.opcion_stats),
            ("Cerrar Sesión", self._on_close),
        ]

        for texto, comando in menu:
            tk.Button(
                self.sidebar, text=texto, command=comando, **self.btn_style
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

        if not self.login_inicial():
            self.root.destroy()
            return

        print(f"Hola {self.usuario_actual['name']}! Bienvenido/a a tu espacio de cine.")

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

    def login_inicial(self) -> bool:
        usuarios = self.user_repo.list_users()
        sel = SelectorPeliculas(self.root, "Iniciar Sesión", usuarios, es_login=True)
        self.root.wait_window(sel)
        if sel.result == "NUEVO":
            dialogo = DialogoPersonalizado(self.root, "Registro", "Dime tu nombre:")
            self.root.wait_window(dialogo)
            nombre = dialogo.result
            if nombre:
                self.user_repo.create_user(nombre)
                return self.login_inicial()
            return False
        elif isinstance(sel.result, int):
            self.usuario_actual = usuarios[sel.result]
            return True
        return False

    def imprimir_pelicula(self, p: dict) -> None:
        print("-" * 50)
        print(f"Título: {p.get('title', 'Sin título')}")
        print(f"Año:    {p.get('release_date', '????')[:4]}")
        print(f"Nota:   {p.get('vote_average', 'N/A')} / 10", end="")
        if p.get("vote_count"):
            print(f"  ({p['vote_count']} votos)")
        else:
            print()

        raw_genres = p.get('genres', [])
        clean_genres = [g['name'] if isinstance(g, dict) else str(g) for g in raw_genres]
        print(f"Géneros: {', '.join(clean_genres)}")

        if p.get("runtime"):
            print(f"Duración: {p.get('runtime')} min")
        print(f"\nSinopsis: {p.get('overview', 'No hay descripción disponible.')}")
        print("-" * 50 + "\n")

    def mostrar_menu_accion(self, peli: dict) -> None:
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
            win, text=peli.get("title", "Sin título"),
            font=("Arial", 12, "bold"), bg="#16213e", fg="white",
            wraplength=260
        ).pack(pady=15)

        def ver_detalles():
            movie_id = peli.get("id") or peli.get("tmdb_id")

            det = self.db_client.collection.find_one(
                {"tmdb_id": movie_id},
                {"_id": 0}
            )

            if not det:
                det = GetMovieDetails().execute(movie_id=movie_id)

            self.imprimir_pelicula(det)
            win.destroy()

        def guardar():
            movie_id = peli.get("id") or peli.get("tmdb_id")

            ya_existe = self.db_client.collection.find_one({"tmdb_id": movie_id})

            if not ya_existe:
                det = GetMovieDetails().execute(movie_id=movie_id)
                SaveMovie().execute(movie_data=det)

            uid = str(self.usuario_actual["_id"])
            self.user_repo.add_to_my_catalog(uid, movie_id)

            print("Guardada en tu catálogo personal!")
            win.destroy()

        def fav():
            movie_id = peli.get("id") or peli.get("tmdb_id")

            ya_existe = self.db_client.collection.find_one({"tmdb_id": movie_id})

            if not ya_existe:
                det = GetMovieDetails().execute(movie_id=movie_id)
                SaveMovie().execute(movie_data=det)

            uid = str(self.usuario_actual["_id"])
            self.user_repo.add_to_my_catalog(uid, movie_id)

            dialogo = DialogoPersonalizado(win, "Rating", "Tu nota (1-10):")
            win.wait_window(dialogo)

            try:
                nota = int(dialogo.result)
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

        tk.Button(win, text="Ver Detalles", command=ver_detalles, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Guardar en Catálogo", command=guardar, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Añadir a Favoritos", command=fav, **btn_cfg).pack(fill=tk.X, padx=50, pady=5)

        tk.Button(
            win, text="Cancelar", command=win.destroy,
            bg="#e94560", fg="white", font=("Arial", 10, "bold"),
            pady=10, relief="flat", cursor="hand2"
        ).pack(fill=tk.X, padx=50, pady=5)

    def opcion_tmdb(self) -> None:
        dialogo = DialogoPersonalizado(self.root, "TMDB", "¿Qué película quieres buscar?")
        self.root.wait_window(dialogo)
        query = dialogo.result
        if not query:
            return
        print(f"\nBuscando '{query}' en TMDB...")
        res = SearchMovies().execute(query=query)
        if res.get("results"):
            top = res["results"][:12]
            sel = SelectorPeliculas(self.root, "Películas Encontradas", top)
            self.root.wait_window(sel)
            if isinstance(sel.result, int):
                self.mostrar_menu_accion(top[sel.result])
        else:
            print("No se encontraron resultados.")

    def opcion_buscar_local(self) -> None:
        dialogo = DialogoPersonalizado(self.root, "Buscar Local", "Término de búsqueda:")
        self.root.wait_window(dialogo)
        query = dialogo.result
        if not query:
            return
        print(f"\nBuscando '{query}' en tu catálogo local...")
        resultados = SearchInDB().execute(query=query)
        if not resultados:
            print("Sin resultados en tu catálogo local.")
            return
        for p in resultados:
            self.imprimir_pelicula(p)
        sel = SelectorPeliculas(self.root, "Resultados Locales", resultados)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.mostrar_menu_accion(resultados[sel.result])

    def opcion_ver_todo(self) -> None:
        print("\n--- Tu Catálogo Personal ---")
        uid = str(self.usuario_actual["_id"])

        mis_pelis = self.user_repo.get_my_catalog_with_details(uid)
        if not mis_pelis:
            print("Tu catálogo está vacío.")
            return

        print(f"Tienes {len(mis_pelis)} películas en tu catálogo.\n")

        for p in mis_pelis:
            self.imprimir_pelicula(p)

        sel = SelectorPeliculas(self.root, "Mi Colección Privada", mis_pelis)
        self.root.wait_window(sel)

        if isinstance(sel.result, int):
            self.mostrar_menu_accion(mis_pelis[sel.result])

    def opcion_ver_favoritas(self) -> None:
        uid = str(self.usuario_actual["_id"])
        favs = self.user_repo.get_favorites_with_details(uid)
        if not favs:
            print("No tienes favoritas todavía.")
            return
        print(f"\n{'=' * 50}")
        print(f"  Tus {len(favs)} Favoritas")
        print(f"{'=' * 50}")
        for f in favs:
            nota_personal = f.get("personal_rating", "N/A")
            nota_tmdb = f.get("vote_average", "?")
            year = str(f.get("release_year", ""))
            genres = ", ".join(f.get("genres") or [])
            print(f"  {f.get('title'):<40} {year}")
            print(f"     Tu nota: {nota_personal}/10  |  TMDB: {nota_tmdb}/10  |  {genres}")
        print(f"{'=' * 50}\n")

    def opcion_recomendar_genero(self) -> None:
        dialogo = DialogoPersonalizado(self.root, "Género", "Género (ej: Terror, Acción):")
        self.root.wait_window(dialogo)
        gen = dialogo.result
        if not gen:
            return
        print(f"\nBuscando el TOP en {gen}...")
        res = RecommendMovies().execute(genre=gen, limit=20)
        if not res:
            print(f"No hay películas de '{gen}' guardadas o ninguna tiene suficientes votos.")
            return
        for p in res:
            self.imprimir_pelicula(p)
        sel = SelectorPeliculas(self.root, f"Mejores de {gen.title()}", res)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.mostrar_menu_accion(res[sel.result])

    def opcion_recomendar_favoritos(self) -> None:
        uid = str(self.usuario_actual["_id"])
        print("\nCalculando recomendaciones personalizadas...")

        favs = self.user_repo.get_favorites(uid)
        if not favs:
            print("Necesitas al menos una favorita para recibir recomendaciones personalizadas.")
            return

        res = RecommendFromFavorites().execute(user_id=uid)

        if not res.get("recomendaciones"):
            print("No tengo suficientes películas en tu catálogo local parecidas a tus favoritas.")
            print("Prueba a descargar o guardar más películas de esos géneros para que la IA tenga de dónde elegir!")
            return

        print("\nTu perfil de géneros favoritos:")
        for g in res["perfil_generos"]:
            print(f"  - {g['genero']} ({g['frecuencia']} película/s)")

        print("\n--- Recomendaciones Para Ti ---")
        recomendaciones = res["recomendaciones"]
        for p in recomendaciones:
            self.imprimir_pelicula(p)

        sel = SelectorPeliculas(self.root, "Recomendaciones IA", recomendaciones)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            self.mostrar_menu_accion(recomendaciones[sel.result])

    def opcion_add_fav(self) -> None:
        uid = str(self.usuario_actual["_id"])
        ids = self.user_repo.get_my_catalog_ids(uid)
        if not ids:
            print("Catálogo vacío.")
            return
        mis_pelis = list(self.db_client.collection.find({"tmdb_id": {"$in": ids}}))
        sel = SelectorPeliculas(self.root, "Añadir a Favoritos", mis_pelis)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            p = mis_pelis[sel.result]
            dialogo = DialogoPersonalizado(self.root, "Rating", "Tu nota (1-10):")
            self.root.wait_window(dialogo)
            try:
                nota = int(dialogo.result)
                if 1 <= nota <= 10:
                    res = AddFavorite().execute(user_id=uid, tmdb_id=p["tmdb_id"], personal_rating=nota)
                    print(f"{res['mensaje']}")
                else:
                    print("La nota debe estar entre 1 y 10.")
            except (TypeError, ValueError):
                pass

    def opcion_remove_fav(self) -> None:
        uid = str(self.usuario_actual["_id"])
        favs = self.user_repo.get_favorites(uid)
        if not favs:
            print("No tienes favoritas.")
            return
        sel = SelectorPeliculas(self.root, "Quitar de Favoritos", favs)
        self.root.wait_window(sel)
        if isinstance(sel.result, int):
            p = favs[sel.result]
            res = RemoveFavorite().execute(user_id=uid, tmdb_id=p["tmdb_id"])
            print(f"{res['mensaje']}")

    def opcion_stats(self) -> None:
        print("\n══════════ Estadísticas del Catálogo ══════════")
        st = GetStats().execute()
        if not st:
            print("No hay datos suficientes aún.")
            return

        if st.get("nota_media_global"):
            d = st["nota_media_global"][0]
            print(f"\nResumen Global")
            print(f"   Total películas:  {d.get('total_peliculas')}")
            print(f"   Nota media:       {round(d.get('media', 0), 2)} / 10")
            print(f"   Mejor nota:       {d.get('mejor_nota')} / 10")
            print(f"   Peor nota:        {d.get('peor_nota')} / 10")

        if st.get("top_generos"):
            print(f"\nTop 10 Géneros")
            for g in st["top_generos"]:
                print(f"   {g['_id']:<22} {g['total']} películas")

        if st.get("nota_por_genero"):
            print(f"\nGéneros Mejor Valorados (mín. 5 películas)")
            for g in st["nota_por_genero"]:
                print(f"   {g['_id']:<22} {round(g['nota_media'], 2):>5} / 10  ({g['total']} pelis)")

        if st.get("mejor_valoradas"):
            print(f"\nTop 5 Películas Mejor Valoradas")
            for i, p in enumerate(st["mejor_valoradas"], 1):
                year = p.get("release_year") or (p.get("release_date", "????")[:4])
                print(f"   {i}. {p['title']:<42} {p['vote_average']} ({year})")

        if st.get("por_decada"):
            print(f"\nPelículas por Década")
            for d in st["por_decada"]:
                bar = "#" * min(int(d["total"] / 10), 30)
                print(f"   {d['_id']}s  {bar} {d['total']} pelis  (media {round(d['nota_media'], 1)})")

        print("\n" + "=" * 46 + "\n")