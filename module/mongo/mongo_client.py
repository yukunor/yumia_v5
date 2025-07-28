import os
import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

_mongo_client = None

def get_mongo_client():
    global _mongo_client

    if _mongo_client is not None:
        try:
            _mongo_client.admin.command("ping")
            # MongoClient is connected
            return _mongo_client
        except ConnectionFailure:
            # Existing MongoClient failed, retrying
            pass

    try:
        mongo_uri = os.getenv("MONGODB_URI")
        if not mongo_uri:
            raise ValueError("Environment variable 'MONGODB_URI' is not set")

        _mongo_client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
        _mongo_client.admin.command("ping")
        # New MongoDB connection successful
        return _mongo_client
    except Exception:
        # Connection failed
        return None
