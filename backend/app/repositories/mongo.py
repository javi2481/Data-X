from typing import Any, Optional
from app.db.client import db

class SessionRepository:
    @property
    def sessions(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["sessions"]

    @property
    def bronze(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["bronze"]

    @property
    def silver(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["silver"]

    async def create_session(self, session_data: dict[str, Any]) -> str:
        """
        Guarda una nueva sesión en MongoDB.
        """
        result = await self.sessions.insert_one(session_data)
        return str(result.inserted_id)

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Recupera una sesión por su ID.
        """
        return await self.sessions.find_one({"session_id": session_id})

    async def update_session(self, session_id: str, update_data: dict[str, Any]) -> bool:
        """
        Actualiza los datos de una sesión.
        """
        result = await self.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def save_bronze(self, bronze_data: dict[str, Any]) -> str:
        result = await self.bronze.insert_one(bronze_data)
        return str(result.inserted_id)

    async def save_silver(self, silver_data: dict[str, Any]) -> str:
        result = await self.silver.insert_one(silver_data)
        return str(result.inserted_id)

    async def get_silver(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.silver.find_one({"session_id": session_id})

    async def get_bronze(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.bronze.find_one({"session_id": session_id})

session_repo = SessionRepository()
