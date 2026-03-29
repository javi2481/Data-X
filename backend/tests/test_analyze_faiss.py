"""
Tests para el endpoint /api/analyze - Verificar carga de índice FAISS y RAG.

Ref: NXT-001 - Tests unitarios del backend
Ref: BUG-003 fix - Índice FAISS debe cargarse desde MongoDB
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_current_user
from app.repositories.mongo import session_repo
from app.services.embedding_service import EmbeddingService


class TestAnalyzeEndpointFAISSLoad:
    """Tests para verificar que el endpoint /api/analyze carga el índice FAISS correctamente."""

    @pytest.fixture
    def mock_user(self):
        """Usuario de prueba."""
        return {
            "sub": "test-user-123",
            "email": "test@example.com",
            "tier": "lite"
        }

    @pytest.fixture
    def mock_session_data(self):
        """Datos de sesión de prueba."""
        return {
            "session_id": "test-session-faiss-load",
            "user_id": "test-user-123",
            "status": "ready",
            "dataset_overview": {
                "row_count": 100,
                "column_count": 5
            }
        }

    @pytest.fixture
    def mock_silver_data(self):
        """Datos Silver de prueba."""
        return {
            "session_id": "test-session-faiss-load",
            "findings": [
                {
                    "finding_id": "f1",
                    "title": "Test Finding",
                    "severity": "high",
                    "what": "Test data",
                    "so_what": "Impact test",
                    "now_what": "Action test"
                }
            ]
        }

    @pytest.fixture
    def mock_bronze_data(self):
        """Datos Bronze de prueba."""
        return {
            "session_id": "test-session-faiss-load",
            "original_filename": "test.csv"
        }

    @pytest.fixture
    def mock_faiss_cache(self):
        """Cache del índice FAISS de prueba."""
        return {
            "session_id": "test-session-faiss-load",
            "index_bytes": b"\x00\x01\x02\x03\x04\x05",  # Mock de índice serializado
            "source_map": {
                "src-1": {
                    "source_type": "finding",
                    "source_id": "f1",
                    "text": "Test finding text",
                    "snippet": "Test snippet"
                }
            },
            "source_ids": ["src-1"],
            "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
            "created_at": "2026-03-29T12:00:00Z"
        }

    @pytest.mark.asyncio
    async def test_analyze_loads_faiss_index_from_cache(
        self, 
        mock_user, 
        mock_session_data, 
        mock_silver_data, 
        mock_bronze_data,
        mock_faiss_cache
    ):
        """
        Test CRÍTICO: Verificar que el índice FAISS se carga desde MongoDB.
        
        Este test verifica el fix de BUG-003:
        - El índice debe cargarse desde hybrid_embeddings_cache
        - deserialize_index() debe ser llamado con los bytes del cache
        - source_map y source_ids deben restaurarse
        
        Si este test falla, el RAG está roto en producción.
        """
        # Arrange: Mock de dependencias
        with TestClient(app) as client:
            # Override de autenticación
            app.dependency_overrides[get_current_user] = lambda: mock_user
            
            # Mock del repositorio
            with patch('app.api.routes.analyze.session_repo') as mock_repo:
                mock_repo.get_session = AsyncMock(return_value=mock_session_data)
                mock_repo.get_silver = AsyncMock(return_value=mock_silver_data)
                mock_repo.get_bronze = AsyncMock(return_value=mock_bronze_data)
                mock_repo.get_hybrid_embeddings_cache = AsyncMock(return_value=mock_faiss_cache)
                
                # Mock del EmbeddingService
                with patch('app.api.routes.analyze.EmbeddingService') as MockEmbeddingService:
                    mock_embedding_instance = MagicMock()
                    mock_embedding_instance.deserialize_index = MagicMock()
                    mock_embedding_instance.source_map = {}
                    mock_embedding_instance.source_ids = []
                    MockEmbeddingService.return_value = mock_embedding_instance
                    
                    # Mock del analysis_agent para evitar llamadas LLM reales
                    with patch('app.api.routes.analyze.analysis_agent') as mock_agent:
                        mock_result = MagicMock()
                        mock_result.data = {
                            "answer": "Test answer",
                            "sources": [],
                            "confidence": "high"
                        }
                        mock_agent.run = AsyncMock(return_value=mock_result)
                        
                        # Act: Hacer request al endpoint
                        response = client.post(
                            "/api/analyze",
                            json={
                                "session_id": "test-session-faiss-load",
                                "query": "Test query"
                            }
                        )
            
            # Assert: Verificar respuesta exitosa
            assert response.status_code == 200
            
            # Assert: Verificar que get_hybrid_embeddings_cache fue llamado
            mock_repo.get_hybrid_embeddings_cache.assert_called_once_with("test-session-faiss-load")
            
            # Assert CRÍTICO: Verificar que deserialize_index fue llamado con los bytes correctos
            mock_embedding_instance.deserialize_index.assert_called_once()
            call_args = mock_embedding_instance.deserialize_index.call_args[0][0]
            assert call_args == b"\x00\x01\x02\x03\x04\x05", "deserialize_index debe recibir los bytes del cache"
            
            # Assert: Verificar que source_map y source_ids se restauraron
            assert mock_embedding_instance.source_map == mock_faiss_cache["source_map"]
            assert mock_embedding_instance.source_ids == mock_faiss_cache["source_ids"]
            
            # Clean up
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyze_handles_missing_faiss_cache(
        self,
        mock_user,
        mock_session_data,
        mock_silver_data,
        mock_bronze_data
    ):
        """
        Test de resiliencia: El endpoint debe funcionar incluso sin cache FAISS.
        
        Escenario: Sesión vieja donde el índice nunca se persistió (pre-BUG-003 fix).
        El endpoint no debe fallar, pero el RAG retornará resultados vacíos.
        """
        # Arrange
        with TestClient(app) as client:
            app.dependency_overrides[get_current_user] = lambda: mock_user
            
            with patch('app.api.routes.analyze.session_repo') as mock_repo:
                mock_repo.get_session = AsyncMock(return_value=mock_session_data)
                mock_repo.get_silver = AsyncMock(return_value=mock_silver_data)
                mock_repo.get_bronze = AsyncMock(return_value=mock_bronze_data)
                mock_repo.get_hybrid_embeddings_cache = AsyncMock(return_value=None)  # ← Sin cache
                
                with patch('app.api.routes.analyze.EmbeddingService') as MockEmbeddingService:
                    mock_embedding_instance = MagicMock()
                    mock_embedding_instance.deserialize_index = MagicMock()
                    MockEmbeddingService.return_value = mock_embedding_instance
                    
                    with patch('app.api.routes.analyze.analysis_agent') as mock_agent:
                        mock_result = MagicMock()
                        mock_result.data = {"answer": "No context available", "sources": []}
                        mock_agent.run = AsyncMock(return_value=mock_result)
                        
                        # Act
                        response = client.post(
                            "/api/analyze",
                            json={
                                "session_id": "test-session-faiss-load",
                                "query": "Test query"
                            }
                        )
            
            # Assert: Debe completarse sin error
            assert response.status_code == 200
            
            # Assert: deserialize_index NO debe ser llamado (no hay cache)
            mock_embedding_instance.deserialize_index.assert_not_called()
            
            # Clean up
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_analyze_handles_empty_index_bytes(
        self,
        mock_user,
        mock_session_data,
        mock_silver_data,
        mock_bronze_data
    ):
        """
        Test de edge case: Cache existe pero index_bytes está vacío.
        
        Esto puede ocurrir si el pipeline falló durante la serialización.
        """
        # Arrange
        empty_cache = {
            "session_id": "test-session-faiss-load",
            "index_bytes": b"",  # ← Vacío
            "source_map": {},
            "source_ids": []
        }
        
        with TestClient(app) as client:
            app.dependency_overrides[get_current_user] = lambda: mock_user
            
            with patch('app.api.routes.analyze.session_repo') as mock_repo:
                mock_repo.get_session = AsyncMock(return_value=mock_session_data)
                mock_repo.get_silver = AsyncMock(return_value=mock_silver_data)
                mock_repo.get_bronze = AsyncMock(return_value=mock_bronze_data)
                mock_repo.get_hybrid_embeddings_cache = AsyncMock(return_value=empty_cache)
                
                with patch('app.api.routes.analyze.EmbeddingService') as MockEmbeddingService:
                    mock_embedding_instance = MagicMock()
                    mock_embedding_instance.deserialize_index = MagicMock()
                    MockEmbeddingService.return_value = mock_embedding_instance
                    
                    with patch('app.api.routes.analyze.analysis_agent') as mock_agent:
                        mock_result = MagicMock()
                        mock_result.data = {"answer": "Test", "sources": []}
                        mock_agent.run = AsyncMock(return_value=mock_result)
                        
                        # Act
                        response = client.post(
                            "/api/analyze",
                            json={
                                "session_id": "test-session-faiss-load",
                                "query": "Test query"
                            }
                        )
            
            # Assert
            assert response.status_code == 200
            
            # Assert: deserialize_index NO debe llamarse con bytes vacíos
            mock_embedding_instance.deserialize_index.assert_not_called()
            
            # Clean up
            app.dependency_overrides.clear()
