from src.infrastructure.mongo_client import MongoDBClient


class RecommendMovies:
    def __init__(self):
        self.db_client = MongoDBClient()

    def execute(self, genre: str, year: str = None, limit: int = 5) -> list:
        query = {"genres": genre}

        if year:
            if str(year).isdigit():
                query["$or"] = [
                    {"release_year": int(year)},
                    {"release_date": {"$regex": f"^{year}"}}
                ]
            else:
                query["release_date"] = {"$regex": f"^{year}"}

        cursor = self.db_client.collection.find(query).sort("vote_average", -1).limit(limit)
        return list(cursor)