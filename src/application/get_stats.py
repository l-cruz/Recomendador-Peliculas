from src.infrastructure.mongo_client import MongoDBClient


class GetStats:
    def __init__(self):
        self.db_client = MongoDBClient()

    def execute(self) -> dict:
        pipeline = [
            {
                "$facet": {
                    "top_generos": [
                        {"$unwind": "$genres"},
                        {"$group": {"_id": "$genres", "total": {"$sum": 1}}},
                        {"$sort": {"total": -1}},
                        {"$limit": 10}
                    ],
                    "nota_media_global": [
                        {
                            "$group": {
                                "_id": None,
                                "media": {"$avg": "$vote_average"},
                                "total_peliculas": {"$sum": 1},
                                "mejor_nota": {"$max": "$vote_average"},
                                "peor_nota": {"$min": "$vote_average"}
                            }
                        }
                    ],
                    "por_decada": [
                        {
                            "$addFields": {
                                "year_for_stats": {
                                    "$ifNull": [
                                        "$release_year",
                                        {
                                            "$convert": {
                                                "input": {"$substr": ["$release_date", 0, 4]},
                                                "to": "int",
                                                "onError": None,
                                                "onNull": None
                                            }
                                        }
                                    ]
                                }
                            }
                        },
                        {"$match": {"year_for_stats": {"$ne": None}}},
                        {
                            "$group": {
                                "_id": {
                                    "$subtract": [
                                        "$year_for_stats",
                                        {"$mod": ["$year_for_stats", 10]}
                                    ]
                                },
                                "total": {"$sum": 1},
                                "nota_media": {"$avg": "$vote_average"}
                            }
                        },
                        {"$sort": {"_id": 1}}
                    ],
                    "mejor_valoradas": [
                        {"$match": {"vote_average": {"$gt": 0}}},
                        {"$sort": {"vote_average": -1}},
                        {"$limit": 5},
                        {
                            "$project": {
                                "_id": 0,
                                "title": 1,
                                "vote_average": 1,
                                "release_date": 1,
                                "release_year": 1,
                                "genres": 1
                            }
                        }
                    ],
                    "nota_por_genero": [
                        {"$unwind": "$genres"},
                        {
                            "$group": {
                                "_id": "$genres",
                                "nota_media": {"$avg": "$vote_average"},
                                "total": {"$sum": 1}
                            }
                        },
                        {"$match": {"total": {"$gte": 5}}},
                        {"$sort": {"nota_media": -1}},
                        {"$limit": 8}
                    ]
                }
            }
        ]

        result = list(self.db_client.collection.aggregate(pipeline))
        return result[0] if result else {}