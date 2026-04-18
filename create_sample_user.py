from src.infrastructure.user_repository import UserRepository


def main() -> None:
    user_repo = UserRepository()
    user_id = user_repo.create_user("Usuario Demo")
    print(f"Usuario listo con id: {user_id}")
    print("Ahora puedes añadir favoritas desde el menú principal.")


if __name__ == "__main__":
    main()