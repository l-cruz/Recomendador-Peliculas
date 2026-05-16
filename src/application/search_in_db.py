from src.infrastructure.mongo_client import MongoDBClient


class SearchInDB:
    def __init__(self):
        self.db_client = MongoDBClient()

    def execute(self, query: str, limit: int = 10) -> list:
        if not query.strip():
            return []

        cursor = self.db_client.collection.find(
            {"$text": {"$search": query}},
            {
                "_id": 0,
                "tmdb_id": 1,
                "title": 1,
                "genres": 1,
                "vote_average": 1,
                "release_date": 1,
                "release_year": 1,
                "overview": 1,
                "score": {"$meta": "textScore"}
            }
        ).sort([
            ("score", {"$meta": "textScore"})
        ]).limit(limit)

        return list(cursor)