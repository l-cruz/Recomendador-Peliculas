import os
import requests
from dotenv import load_dotenv
load_dotenv()


class TMDBClient:
    def execute(self, endpoint: str, params: dict = None) -> dict:
        base_url = "https://api.themoviedb.org/3"
        token = os.getenv("TMDB_ACCESS_TOKEN")

        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }

        response = requests.get(f"{base_url}{endpoint}", headers=headers, params=params)
        response.raise_for_status()
        return response.json()