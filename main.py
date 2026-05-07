import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.db_connection import check_env
from src.infrastructure.user_repository import UserRepository
from gui_app import VentanaRecomendador


def main():
    try:
        check_env()

        user_repo = UserRepository()
        root = tk.Tk()
        app = VentanaRecomendador(root, user_repo)
        root.mainloop()

    except EnvironmentError as e:
        print(f"\n  Error de configuración:\n{e}")
        input("Presiona Enter para cerrar")
    except Exception as e:
        print(f"\n Error crítico al arrancar la aplicación: {e}")
        input("Presiona Enter para cerrar")


if __name__ == "__main__":
    main()
