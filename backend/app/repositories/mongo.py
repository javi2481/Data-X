from typing import Any, Optional
from app.db.client import db

class SessionRepository:
    @property
    def collection(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["sessions"]

    async def create_session(self, session_data: dict[str, Any]) -> str:
        """
        Guarda una nueva sesión en MongoDB.
        """
        # Nota: El DataFrame no se guarda en MongoDB.
        # Se asume que session_data contiene metadatos y resultados procesados.
        result = await self.collection.insert_one(session_data)
        return str(result.inserted_id)

    async def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Recupera una sesión por su ID.
        """
        return await self.collection.find_one({"session_id": session_id})

    async def update_session(self, session_id: str, update_data: dict[str, Any]) -> bool:
        """
        Actualiza los datos de una sesión.
        """
        result = await self.collection.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

session_repo = SessionRepository()
