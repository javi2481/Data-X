"""
Tests para SessionRepository - Verificar GDPR compliance y operaciones de base de datos.

Ref: NXT-001 - Tests unitarios del backend con dependency_overrides
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.repositories.mongo import SessionRepository
from app.db.client import db


class TestSessionRepository:
    """Tests para SessionRepository con énfasis en GDPR compliance."""

    @pytest.mark.asyncio
    async def test_delete_session_data_cleans_all_collections(self):
        """
        Test crítico: Verificar que delete_session_data() limpia TODAS las colecciones.
        
        Esto es esencial para GDPR compliance. Si falla, hay una violación de privacidad.
        
        Ref: BUG-002 fix - Usa db.db["usage_events"] en lugar de self.db.usage_events
        """
        # Arrange: Crear repositorio y mockear todas las colecciones
        repo = SessionRepository()
        test_session_id = "test-session-12345"
        
        # Mock de todas las colecciones que deben limpiarse
        repo.sessions = AsyncMock()
        repo.bronze = AsyncMock()
        repo.silver = AsyncMock()
        repo.gold = AsyncMock()
        repo.embeddings_cache = AsyncMock()
        repo.hybrid_embeddings_cache = AsyncMock()
        repo.document_chunks = AsyncMock()
        
        # Mock del cliente global db.db para usage_events
        mock_usage_events = AsyncMock()
        with patch('app.repositories.mongo.db') as mock_db:
            mock_db.db = {
                "usage_events": mock_usage_events
            }
            
            # Act: Ejecutar delete_session_data
            result = await repo.delete_session_data(test_session_id)
        
        # Assert: Verificar que retorna True
        assert result is True, "delete_session_data debe retornar True"
        
        # Assert: Verificar que TODAS las colecciones fueron limpiadas
        repo.sessions.delete_one.assert_called_once_with({"session_id": test_session_id})
        repo.bronze.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.silver.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.gold.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.embeddings_cache.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.hybrid_embeddings_cache.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.document_chunks.delete_many.assert_called_once_with({"session_id": test_session_id})
        mock_usage_events.delete_many.assert_called_once_with({"session_id": test_session_id})

    @pytest.mark.asyncio
    async def test_delete_session_data_handles_missing_db(self):
        """
        Test de resiliencia: Verificar que no falla si db.db es None.
        
        Esto puede ocurrir durante shutdown o en tests donde MongoDB no está disponible.
        """
        # Arrange
        repo = SessionRepository()
        test_session_id = "test-session-67890"
        
        # Mock de colecciones del repositorio
        repo.sessions = AsyncMock()
        repo.bronze = AsyncMock()
        repo.silver = AsyncMock()
        repo.gold = AsyncMock()
        repo.embeddings_cache = AsyncMock()
        repo.hybrid_embeddings_cache = AsyncMock()
        repo.document_chunks = AsyncMock()
        
        # Mock db.db como None (MongoDB no disponible)
        with patch('app.repositories.mongo.db') as mock_db:
            mock_db.db = None
            
            # Act: Debe completarse sin error
            result = await repo.delete_session_data(test_session_id)
        
        # Assert
        assert result is True, "Debe retornar True incluso si db.db es None"
        
        # Verificar que las otras colecciones sí se limpiaron
        repo.sessions.delete_one.assert_called_once()
        repo.bronze.delete_many.assert_called_once()
        repo.silver.delete_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_and_get_hybrid_embeddings_cache(self):
        """
        Test de persistencia del índice FAISS.
        
        Ref: BUG-003 fix - Verificar que el índice FAISS se puede guardar y recuperar.
        """
        # Arrange
        repo = SessionRepository()
        test_session_id = "test-session-faiss"
        
        cache_data = {
            "session_id": test_session_id,
            "index_bytes": b"\x00\x01\x02\x03",  # Mock de índice serializado
            "source_map": {"src-1": {"text": "test"}},
            "source_ids": ["src-1", "src-2"],
            "model_name": "test-model",
            "created_at": "2026-03-29T12:00:00Z"
        }
        
        # Mock de la colección
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "mock-object-id"
        
        repo.hybrid_embeddings_cache = AsyncMock()
        repo.hybrid_embeddings_cache.insert_one.return_value = mock_insert_result
        repo.hybrid_embeddings_cache.find_one.return_value = cache_data
        
        # Act: Guardar
        result_id = await repo.save_hybrid_embeddings_cache(cache_data)
        
        # Assert: Verificar que se guardó
        assert result_id == "mock-object-id"
        repo.hybrid_embeddings_cache.delete_many.assert_called_once_with({"session_id": test_session_id})
        repo.hybrid_embeddings_cache.insert_one.assert_called_once_with(cache_data)
        
        # Act: Recuperar
        retrieved = await repo.get_hybrid_embeddings_cache(test_session_id)
        
        # Assert: Verificar que se recuperó correctamente
        assert retrieved == cache_data
        assert retrieved["index_bytes"] == b"\x00\x01\x02\x03"
        assert len(retrieved["source_ids"]) == 2
