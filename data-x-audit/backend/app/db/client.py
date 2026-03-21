from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect_to_db(self):
        """
        Inicia la conexión con MongoDB usando Motor.
        """
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.mongodb_db]
        print(f"✅ Conectado a MongoDB: {settings.mongodb_db}")

    async def close_db_connection(self):
        """
        Cierra la conexión con MongoDB.
        """
        if self.client:
            self.client.close()
            print("❌ Conexión a MongoDB cerrada.")

db = Database()
