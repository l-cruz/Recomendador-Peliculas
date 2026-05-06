import sys
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from bson import ObjectId

# Use Cases
from src.application.get_movie_details import GetMovieDetails
from src.application.save_movie import SaveMovie
from src.application.search_movies import SearchMovies
from src.application.add_favorite import AddFavorite
from src.application.remove_favorite import RemoveFavorite
from src.application.get_stats import GetStats
from src.application.recommend_movies import RecommendMovies
from src.application.recommend_from_favorites import RecommendFromFavorites
from src.infrastructure.mongo_client import MongoDBClient

class SelectorPeliculas(tk.Toplevel):
    def __init__(self, parent, titulo, lista_items, es_login=False):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("400x450")
        self.configure(bg="#1a1a2e")
        self.result = None
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=titulo, font=('Arial', 13, 'bold'), bg="#1a1a2e", fg="#e94560").pack(pady=15)

        frame_lista = tk.Frame(self, bg="#1a1a2e")
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=20)

        self.listbox = tk.Listbox(frame_lista, font=('Arial', 10), bg="#16213e", fg="white",
                                  selectbackground="#e94560", borderwidth=0, highlightthickness=0)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        for item in lista_items:
            nombre = item.get('name') or item.get('title') or "Sin título"
            year = f" ({item['release_date'][:4]})" if item.get('release_date') else ""
            self.listbox.insert(tk.END, f" {nombre}{year}")

        btn_frame = tk.Frame(self, bg="#1a1a2e")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="SELECCIONAR", bg="#0f3460", fg="white", font=('Arial', 10, 'bold'),
                  command=self.confirmar, width=15, pady=8).pack(side=tk.LEFT, padx=5)

        if es_login:
            tk.Button(btn_frame, text="NUEVO USUARIO", bg="#4ecca3", fg="#1a1a2e", font=('Arial', 10, 'bold'),
                      command=self.crear_nuevo, width=15, pady=8).pack(side=tk.LEFT, padx=5)

    def crear_nuevo(self):
        self.result = "NUEVO"
        self.destroy()

    def confirmar(self):
        sel = self.listbox.curselection()
        if sel: self.result = sel[0]
        self.destroy()

class VentanaRecomendador:
    def __init__(self, root, user_repo):
        self.root = root
        self.user_repo = user_repo
        self.usuario_actual = None
        self.db_client = MongoDBClient()

        self.root.title("Cinema Advisor")
        self.root.geometry("800x750")
        self.root.configure(bg="#1a1a2e")

        self.btn_style = {"bg": "#0f3460", "fg": "white", "relief": "flat", "pady": 10, "font": ('Arial', 10, 'bold'), "cursor": "hand2"}

        if not self.login_inicial():
            self.root.destroy()
            return

        self.sidebar = tk.Frame(self.root, bg="#16213e", width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Aquí cambias el texto de la barra lateral
        tk.Label(self.sidebar, text="MI CARTELERA", font=('Arial', 18, 'bold'), bg="#16213e", fg="#e94560").pack(pady=30)

        menu = [
            ("🔍 BUSCAR EN TMDB", self.opcion_tmdb),
            ("📂 MI CATÁLOGO", self.opcion_ver_todo),
            ("🎭 RECOMENDAR GÉNERO", self.opcion_recomendar_genero),
            ("⭐ AÑADIR FAVORITA", self.opcion_add_fav),
            ("❌ QUITAR FAVORITA", self.opcion_remove_fav),
            ("📊 ESTADÍSTICAS", self.opcion_stats),
            ("🚪 CERRAR SESIÓN", self.root.quit)
        ]

        for texto, comando in menu:
            tk.Button(self.sidebar, text=texto, command=comando, **self.btn_style).pack(fill=tk.X, padx=20, pady=5)

        self.txt_output = tk.Text(self.root, bg="#1a1a2e", fg="#4ecca3", font=('Consolas', 11), borderwidth=0, padx=25, pady=25)
        self.txt_output.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        sys.stdout = self
        print(f"¡Hola {self.usuario_actual['name']}! Bienvenida a tu espacio de cine.")

    def write(self, m):
        self.txt_output.insert(tk.END, m)
        self.txt_output.see(tk.END)

    def flush(self): pass

    def login_inicial(self):
        usuarios = self.user_repo.list_users()
        sel = SelectorPeliculas(self.root, "INICIAR SESIÓN", usuarios, es_login=True)
        self.root.wait_window(sel)
        if sel.result == "NUEVO":
            nombre = simpledialog.askstring("Registro", "Dime tu nombre:")
            if nombre:
                self.user_repo.create_user(nombre)
                return self.login_inicial()
            return False
        elif isinstance(sel.result, int):
            self.usuario_actual = usuarios[sel.result]
            return True
        return False

    def imprimir_pelicula(self, p):
        print("-" * 50)
        print(f"🎬 TÍTULO: {p.get('title', 'Sin título').upper()}")
        print(f"📅 AÑO: {p.get('release_date', '????')[:4]}")
        print(f"⭐ NOTA: {p.get('vote_average', 'N/A')} / 10")
        print(f"🎭 GÉNEROS: {', '.join(p.get('genres', []))}")
        if p.get('runtime'): print(f"⏳ DURACIÓN: {p.get('runtime')} min")
        print(f"\n📖 SINOPSIS: {p.get('overview', 'No hay descripción disponible.')}")
        print("-" * 50 + "\n")

    def opcion_tmdb(self):
        query = simpledialog.askstring("TMDB", "Buscar película en internet:")
        if not query: return
        print(f"\nBuscando '{query}' en TMDB...")
        res = SearchMovies().execute(query=query)
        if res.get("results"):
            top = res["results"][:12]
            # Aquí cambiamos el título de la ventana de selección
            sel = SelectorPeliculas(self.root, "PELÍCULAS ENCONTRADAS", top)
            self.root.wait_window(sel)
            if sel.result is not None:
                p = top[sel.result]
                # Recuperamos el menú de acción para poder GUARDAR
                self.mostrar_menu_accion(p)
        else: print("No se encontraron resultados.")

    def mostrar_menu_accion(self, peli):
        win = tk.Toplevel(self.root)
        win.title("Opciones de Película")
        win.geometry("300x350")
        win.configure(bg="#16213e")
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=peli['title'], font=('Arial', 12, 'bold'), bg="#16213e", fg="white").pack(pady=15)

        def ver_detalles():
            det = GetMovieDetails().execute(movie_id=peli["id"])
            self.imprimir_pelicula(det)
            win.destroy()

        def guardar():
            det = GetMovieDetails().execute(movie_id=peli["id"])
            SaveMovie().execute(movie_data=det)
            self.user_repo.add_to_my_catalog(str(self.usuario_actual["_id"]), peli["id"])
            print(f"✅ ¡Guardada en tu catálogo personal!")
            win.destroy()

        def fav():
            det = GetMovieDetails().execute(movie_id=peli["id"])
            SaveMovie().execute(movie_data=det)
            uid = str(self.usuario_actual["_id"])
            self.user_repo.add_to_my_catalog(uid, peli["id"])
            nota = simpledialog.askinteger("Rating", "Nota (1-10):", minvalue=1, maxvalue=10, parent=win)
            if nota:
                res = AddFavorite().execute(user_id=uid, tmdb_id=peli["id"], personal_rating=nota)
                print(f"⭐ {res['mensaje']}")
            win.destroy()

        tk.Button(win, text="Ver Detalles", command=ver_detalles, **self.btn_style).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Guardar en Catálogo", command=guardar, **self.btn_style).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(win, text="Añadir a Favoritos", command=fav, **self.btn_style).pack(fill=tk.X, padx=50, pady=5)

    def opcion_ver_todo(self):
        print("\n--- TU CATÁLOGO PERSONAL ---")
        uid = str(self.usuario_actual["_id"])
        mis_ids = self.user_repo.get_my_catalog_ids(uid)
        if not mis_ids:
            print("Tu catálogo está vacío.")
            return
        mis_pelis = list(self.db_client.collection.find({"tmdb_id": {"$in": mis_ids}}))
        for p in mis_pelis:
            self.imprimir_pelicula(p)
        SelectorPeliculas(self.root, "MI COLECCIÓN PRIVADA", mis_pelis)

    def opcion_recomendar_genero(self):
        gen = simpledialog.askstring("Género", "Género (ej: Terror, Acción):")
        if not gen: return
        print(f"\nBuscando el TOP en {gen}...")
        res = RecommendMovies().execute(genre=gen)
        if res:
            for p in res: self.imprimir_pelicula(p)
            SelectorPeliculas(self.root, f"MEJORES DE {gen.upper()}", res)
        else: print(f"No hay pelis de {gen} guardadas.")

    def opcion_add_fav(self):
        uid = str(self.usuario_actual["_id"])
        ids = self.user_repo.get_my_catalog_ids(uid)
        if not ids: print("Catálogo vacío."); return
        mis_pelis = list(self.db_client.collection.find({"tmdb_id": {"$in": ids}}))
        sel = SelectorPeliculas(self.root, "AÑADIR A FAVORITOS", mis_pelis)
        self.root.wait_window(sel)
        if sel.result is not None:
            p = mis_pelis[sel.result]
            nota = simpledialog.askinteger("Rating", "Tu nota (1-10):", minvalue=1, maxvalue=10)
            if nota:
                AddFavorite().execute(user_id=uid, tmdb_id=p["tmdb_id"], personal_rating=nota)
                print(f"⭐ ¡{p['title']} añadida a favoritas!")

    def opcion_remove_fav(self):
        uid = str(self.usuario_actual["_id"])
        favs = self.user_repo.get_favorites(uid)
        if not favs: print("No tienes favoritas."); return
        sel = SelectorPeliculas(self.root, "QUITAR DE FAVORITOS", favs)
        self.root.wait_window(sel)
        if sel.result is not None:
            p = favs[sel.result]
            RemoveFavorite().execute(user_id=uid, tmdb_id=p["tmdb_id"])
            print(f"🗑️ Eliminada de favoritas.")

    def opcion_stats(self):
        print("\n--- ESTADÍSTICAS ---")
        st = GetStats().execute()
        if st and st.get("nota_media_global"):
            d = st["nota_media_global"][0]
            print(f"Total Películas: {d.get('total_peliculas')}")
            print(f"Nota Media Global: ⭐ {round(d.get('media', 0), 2)}")