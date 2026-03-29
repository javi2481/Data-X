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

    @property
    def gold(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["gold"]

    @property
    def embeddings_cache(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["embeddings_cache"]

    @property
    def hybrid_embeddings_cache(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["hybrid_embeddings_cache"]

    @property
    def document_chunks(self):
        if db.db is None:
            raise RuntimeError("Base de datos no inicializada. Llama a connect_to_db primero.")
        return db.db["document_chunks"]

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

    async def save_gold(self, gold_data: dict[str, Any]) -> str:
        result = await self.gold.insert_one(gold_data)
        return str(result.inserted_id)

    async def get_silver(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.silver.find_one({"session_id": session_id})

    async def get_gold(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.gold.find_one({"session_id": session_id})

    async def get_bronze(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.bronze.find_one({"session_id": session_id})

    async def list_sessions(self, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """
        Lista las sesiones ordenadas por fecha descendente.
        """
        cursor = self.sessions.find().sort("created_at", -1).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)

    async def list_sessions_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """
        Lista las sesiones de un usuario específico.
        """
        cursor = self.sessions.find({"user_id": user_id}).sort("created_at", -1).skip(offset).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_sessions_by_user(self, user_id: str) -> int:
        """
        Cuenta el total de sesiones de un usuario específico para la paginación.
        """
        return await self.sessions.count_documents({"user_id": user_id})

    async def save_embeddings_cache(self, cache_data: dict[str, Any]) -> str:
        """
        Guarda o actualiza el caché de embeddings de una sesión.
        """
        session_id = cache_data.get("session_id")
        await self.embeddings_cache.delete_many({"session_id": session_id})
        result = await self.embeddings_cache.insert_one(cache_data)
        return str(result.inserted_id)

    async def get_embeddings_cache(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Recupera el caché de embeddings de una sesión.
        """
        return await self.embeddings_cache.find_one({"session_id": session_id})

    async def save_hybrid_embeddings_cache(self, cache_data: dict[str, Any]) -> str:
        session_id = cache_data.get("session_id")
        await self.hybrid_embeddings_cache.delete_many({"session_id": session_id})
        result = await self.hybrid_embeddings_cache.insert_one(cache_data)
        return str(result.inserted_id)

    async def get_hybrid_embeddings_cache(self, session_id: str) -> Optional[dict[str, Any]]:
        return await self.hybrid_embeddings_cache.find_one({"session_id": session_id})

    async def save_document_chunks(self, session_id: str, chunks: list[dict[str, Any]]) -> int:
        await self.document_chunks.delete_many({"session_id": session_id})
        if not chunks:
            return 0
        result = await self.document_chunks.insert_many(chunks)
        return len(result.inserted_ids)

    async def get_document_chunks(self, session_id: str) -> list[dict[str, Any]]:
        cursor = self.document_chunks.find({"session_id": session_id}).sort("chunk_order", 1)
        return await cursor.to_list(length=10000)

    async def delete_session_data(self, session_id: str) -> bool:
        """
        Borrado seguro (GDPR): Elimina todos los datos asociados a una sesión de todas las colecciones.
        """
        await self.sessions.delete_one({"session_id": session_id})
        await self.bronze.delete_many({"session_id": session_id})
        await self.silver.delete_many({"session_id": session_id})
        await self.gold.delete_many({"session_id": session_id})
        await self.embeddings_cache.delete_many({"session_id": session_id})
        await self.hybrid_embeddings_cache.delete_many({"session_id": session_id})
        await self.document_chunks.delete_many({"session_id": session_id})
        if db.db is not None:
            await db.db["usage_events"].delete_many({"session_id": session_id})
        return True

session_repo = SessionRepository()
