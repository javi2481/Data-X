"""
OpenSearchRetrievalService - Motor vectorial k-NN para tiers Enterprise y Professional.

Ref: NXT-003 - Implementar OpenSearch como alternativa escalable a FAISS in-memory.

Configuración:
- Índices dinámicos por sesión: datax-{tier}-{session_id}
- Cleanup automático cuando se borra la sesión
- Fallback a FAISS si OpenSearch no está disponible
"""

import structlog
from typing import List, Dict, Any, Optional
from app.services.retrieval.base import BaseRetrievalService
from app.core.config import settings
import numpy as np

logger = structlog.get_logger(__name__)

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from sentence_transformers import SentenceTransformer
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    logger.warning("opensearch_not_installed", msg="Install opensearch-py to enable OpenSearch retrieval")


class OpenSearchRetrievalService(BaseRetrievalService):
    """
    Implementación de retrieval usando OpenSearch k-NN.
    
    Ventajas sobre FAISS:
    - Persistencia nativa (no requiere MongoDB para guardar índices)
    - Escalabilidad horizontal
    - Filtrado eficiente con queries DSL
    - Soporte para actualizaciones incrementales
    
    Estrategia de indexación:
    - Índice dinámico por sesión: datax-{tier}-{session_id}
    - Cada documento tiene: vector embedding + metadatos (source_type, text, snippet, etc.)
    - Dimension: 384 (paraphrase-multilingual-MiniLM-L12-v2)
    """
    
    def __init__(self, session_id: str, tier: str = "enterprise"):
        self.session_id = session_id
        self.tier = tier
        self._model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.index_name = f"datax-{tier}-{session_id}"
        
        # Cargar modelo de embeddings (mismo que EmbeddingService para consistencia)
        try:
            self.model = SentenceTransformer(self._model_name)
        except Exception as e:
            logger.error("embedding_model_load_failed", error=str(e))
            self.model = None
        
        # Cliente OpenSearch (configuración mock si no está disponible)
        self.client: Optional[OpenSearch] = None
        self._init_client()
        
        # Cache local para source_map (evita queries innecesarias)
        self.source_map: Dict[str, Any] = {}
        self.source_ids: List[str] = []
    
    def _init_client(self):
        """Inicializa el cliente de OpenSearch con la configuración de settings."""
        if not OPENSEARCH_AVAILABLE:
            logger.warning(
                "opensearch_unavailable",
                msg="OpenSearch library not installed. Service will operate in mock mode."
            )
            return
        
        if not settings.opensearch_enabled:
            logger.info(
                "opensearch_disabled",
                msg="OpenSearch disabled in settings. Use OPENSEARCH_ENABLED=true to activate."
            )
            return
        
        try:
            # Configuración para AWS OpenSearch Serverless vs standalone
            auth_config = {}
            if settings.opensearch_use_aws_auth:
                # AWS IAM Auth (requiere boto3 y requests-aws4auth)
                try:
                    from requests_aws4auth import AWS4Auth
                    import boto3
                    
                    credentials = boto3.Session().get_credentials()
                    auth_config["http_auth"] = AWS4Auth(
                        credentials.access_key,
                        credentials.secret_key,
                        settings.opensearch_region,
                        "aoss" if settings.opensearch_serverless else "es",
                        session_token=credentials.token,
                    )
                    auth_config["connection_class"] = RequestsHttpConnection
                except ImportError:
                    logger.error(
                        "aws_auth_dependencies_missing",
                        msg="Install boto3 and requests-aws4auth for AWS authentication"
                    )
                    return
            else:
                # Basic Auth para OpenSearch standalone
                if settings.opensearch_username and settings.opensearch_password:
                    auth_config["http_auth"] = (
                        settings.opensearch_username,
                        settings.opensearch_password
                    )
            
            self.client = OpenSearch(
                hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
                use_ssl=settings.opensearch_use_ssl,
                verify_certs=settings.opensearch_verify_certs,
                ssl_show_warn=False,
                **auth_config
            )
            
            # Verificar conectividad
            info = self.client.info()
            logger.info(
                "opensearch_connected",
                cluster=info.get("cluster_name"),
                version=info.get("version", {}).get("number")
            )
        except Exception as e:
            logger.error("opensearch_connection_failed", error=str(e))
            self.client = None
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    def _create_index_if_not_exists(self):
        """Crea el índice con configuración k-NN si no existe."""
        if not self.client:
            return False
        
        try:
            if self.client.indices.exists(index=self.index_name):
                return True
            
            # Configuración del índice con k-NN
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,  # Habilitar k-NN
                        "number_of_shards": 1,
                        "number_of_replicas": 0 if settings.env == "development" else 1
                    }
                },
                "mappings": {
                    "properties": {
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 384,  # MiniLM-L12
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {
                                    "ef_construction": 128,
                                    "m": 16
                                }
                            }
                        },
                        "source_id": {"type": "keyword"},
                        "source_type": {"type": "keyword"},
                        "text": {"type": "text"},
                        "snippet": {"type": "text"},
                        "evidence_ref": {"type": "keyword"},
                        "provenance": {
                            "properties": {
                                "page": {"type": "integer"},
                                "heading": {"type": "text"},
                                "section_path": {"type": "text"}
                            }
                        },
                        "session_id": {"type": "keyword"},
                        "created_at": {"type": "date"}
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=index_body)
            logger.info("opensearch_index_created", index=self.index_name)
            return True
        except Exception as e:
            logger.error("opensearch_index_creation_failed", error=str(e), index=self.index_name)
            return False
    
    def index_findings(self, findings: List[dict]) -> None:
        """No implementado para OpenSearch (se usa index_hybrid_sources)."""
        logger.warning(
            "index_findings_deprecated",
            msg="Use index_hybrid_sources() for OpenSearch indexing"
        )
    
    async def index_hybrid_sources(self, findings: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> None:
        """Indexa findings y chunks en OpenSearch con embeddings."""
        if not self.client or not self.model:
            logger.warning("opensearch_indexing_skipped", reason="client or model not available")
            return
        
        if not self._create_index_if_not_exists():
            logger.error("opensearch_indexing_failed", reason="index creation failed")
            return
        
        # Preparar documentos para indexación
        documents = []
        texts = []
        
        # Indexar findings
        for finding in findings:
            source_id = finding.get("finding_id")
            if not source_id:
                continue
            
            text = f"{finding.get('title', '')}. {finding.get('what', '')} {finding.get('so_what', '')}"
            doc = {
                "source_id": source_id,
                "source_type": "finding",
                "evidence_ref": source_id,
                "text": text,
                "snippet": text[:240],
                "session_id": self.session_id
            }
            documents.append(doc)
            texts.append(text)
            self.source_map[source_id] = doc
            self.source_ids.append(source_id)
        
        # Indexar chunks
        for chunk in chunks:
            source_id = chunk.get("chunk_id")
            if not source_id:
                continue
            
            text = str(chunk.get("text", ""))
            doc = {
                "source_id": source_id,
                "source_type": "chunk",
                "evidence_ref": chunk.get("source_id", source_id),
                "text": text,
                "snippet": chunk.get("snippet", text[:240]),
                "provenance": chunk.get("provenance", {}),
                "session_id": self.session_id
            }
            documents.append(doc)
            texts.append(text)
            self.source_map[source_id] = doc
            self.source_ids.append(source_id)
        
        if not texts:
            logger.warning("opensearch_no_documents_to_index")
            return
        
        # Generar embeddings
        try:
            embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        except Exception as e:
            logger.error("opensearch_embedding_failed", error=str(e))
            return
        
        # Bulk indexing
        bulk_body = []
        for i, doc in enumerate(documents):
            doc["embedding"] = embeddings[i].tolist()
            bulk_body.append({"index": {"_index": self.index_name, "_id": doc["source_id"]}})
            bulk_body.append(doc)
        
        try:
            response = self.client.bulk(body=bulk_body)
            if response.get("errors"):
                logger.error("opensearch_bulk_indexing_errors", response=response)
            else:
                logger.info(
                    "opensearch_indexing_complete",
                    index=self.index_name,
                    documents=len(documents)
                )
        except Exception as e:
            logger.error("opensearch_bulk_indexing_failed", error=str(e))
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Búsqueda básica de findings (legacy, usa search_hybrid_sources)."""
        logger.warning(
            "search_deprecated",
            msg="Use search_hybrid_sources() for OpenSearch queries"
        )
        return []
    
    async def search_hybrid_sources(
        self,
        query: str,
        top_k: int = 8,
        **filters
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica con k-NN y filtros opcionales."""
        if not self.client or not self.model:
            logger.warning("opensearch_search_skipped", reason="client or model not available")
            return []
        
        # Generar embedding de la query
        try:
            query_embedding = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        except Exception as e:
            logger.error("opensearch_query_embedding_failed", error=str(e))
            return []
        
        # Construir query DSL con filtros opcionales
        query_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding.tolist(),
                                    "k": top_k
                                }
                            }
                        }
                    ],
                    "filter": [{"term": {"session_id": self.session_id}}]
                }
            }
        }
        
        # Aplicar filtros opcionales
        filter_by_source_type = filters.get("filter_by_source_type")
        if filter_by_source_type:
            query_body["query"]["bool"]["filter"].append(
                {"term": {"source_type": filter_by_source_type}}
            )
        
        filter_by_page = filters.get("filter_by_page")
        if filter_by_page:
            query_body["query"]["bool"]["filter"].append(
                {"term": {"provenance.page": filter_by_page}}
            )
        
        # Ejecutar búsqueda
        try:
            response = self.client.search(index=self.index_name, body=query_body)
            
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                source["score"] = hit["_score"]
                # Remover el embedding del resultado (es muy grande)
                source.pop("embedding", None)
                results.append(source)
            
            logger.info(
                "opensearch_search_complete",
                query=query[:50],
                results=len(results),
                top_score=results[0]["score"] if results else 0
            )
            return results
        except Exception as e:
            logger.error("opensearch_search_failed", error=str(e))
            return []
    
    async def delete_index(self):
        """Borra el índice (llamar al hacer cleanup de sesión)."""
        if not self.client:
            return
        
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info("opensearch_index_deleted", index=self.index_name)
        except Exception as e:
            logger.error("opensearch_index_deletion_failed", error=str(e))
