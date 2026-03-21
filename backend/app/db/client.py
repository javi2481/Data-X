"""
Database client for MongoDB using PyMongo Async API.

Sprint 3: Migrated from Motor (deprecated May 2025) to PyMongo AsyncMongoClient.
Motor EOL: May 2026. PyMongo Async provides better latency and throughput.
"""
from pymongo import AsyncMongoClient
from app.core.config import settings


class Database:
    client: AsyncMongoClient = None
    db = None

    async def connect_to_db(self):
        """
        Inicia la conexión con MongoDB usando PyMongo Async API.
        """
        self.client = AsyncMongoClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db]
        print(f"✅ Conectado a MongoDB (PyMongo Async): {settings.mongodb_db}")

    async def close_db_connection(self):
        """
        Cierra la conexión con MongoDB.
        """
        if self.client:
            await self.client.close()
            print("❌ Conexión a MongoDB cerrada.")


db = Database()
