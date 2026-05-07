import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("Falta la variable de entorno MONGO_URI.")
        _client = MongoClient(uri, tlsCAFile=certifi.where())
        _client.admin.command("ping")
    return _client


def get_db():
    return get_client()["recomendador_db"]


def check_env() -> None:
    required = ("MONGO_URI", "TMDB_ACCESS_TOKEN")
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Faltan variables de entorno: {', '.join(missing)}\n"
            f"Crea un archivo .env en la raíz del proyecto con esas claves."
        )
