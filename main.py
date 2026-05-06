import tkinter as tk
import sys
from gui_app import VentanaRecomendador  # Importamos la interfaz que creamos
from src.infrastructure.user_repository import UserRepository


def main():
    try:
        user_repo = UserRepository()
        root = tk.Tk()
        app = VentanaRecomendador(root, user_repo)
        print(">>> Sistema de Recomendación iniciado correctamente.")
        root.mainloop()

    except Exception as e:
        print(f"Error crítico al arrancar la aplicación: {e}")
        input("Presiona Enter para cerrar")


if __name__ == "__main__":
    main()