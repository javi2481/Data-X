import structlog
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.services.retrieval.base import BaseRetrievalService

try:
    from opensearchpy import AsyncOpenSearch
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False

logger = structlog.get_logger(__name__)

class OpenSearchRetrievalService(BaseRetrievalService):
    """
    Implementación Enterprise del motor de búsqueda utilizando OpenSearch.
    Soporta búsqueda híbrida real (k-NN Vectorial + BM25 Léxico) a gran escala.
    """
    def __init__(self, host: str = "localhost", port: int = 9200, index_name: str = "datax-documents"):
        self._model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.model = SentenceTransformer(self._model_name)
        self.index_name = index_name
        
        if OPENSEARCH_AVAILABLE:
            self.client = AsyncOpenSearch(
                hosts=[{'host': host, 'port': port}],
                http_compress=True,
                # use_ssl=True, verify_certs=True para producción real
            )
        else:
            self.client = None
            logger.warning("opensearch_not_installed", message="pip install opensearch-py required")

    @property
    def model_name(self) -> str:
        return self._model_name

    async def search_hybrid_sources(self, query: str, top_k: int = 8, **filters) -> List[Dict[str, Any]]:
        if not self.client:
            return []
            
        logger.info("opensearch_query_start", query=query, filters=filters)
        query_embedding = self.model.encode([query], normalize_embeddings=True)[0].tolist()

        # Construir pre-filtros nativos (RBAC o metadata) mucho más rápido que FAISS
        must_clauses = []
        if filters.get("filter_by_source_type"):
            must_clauses.append({"term": {"source_type": filters.get("filter_by_source_type")}})
        if filters.get("filter_by_page"):
            must_clauses.append({"term": {"page": filters.get("filter_by_page")}})

        search_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "filter": must_clauses,
                    "should": [
                        {"match": {"text": {"query": query, "boost": 1.0}}},            # BM25 Lexical
                        {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}} # Vectorial
                    ]
                }
            }
        }

        try:
            response = await self.client.search(index=self.index_name, body=search_body)
            hits = response.get("hits", {}).get("hits", [])
            
            results = []
            for hit in hits:
                source = hit["_source"]
                source["score"] = hit["_score"]
                results.append(source)
            return results
        except Exception as e:
            logger.error("opensearch_search_failed", error=str(e))
            return []

    async def index_hybrid_sources(self, findings: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> None:
        # Aquí se implementaría la ingesta en bloque (bulk API) hacia OpenSearch
        logger.info("opensearch_indexing_planned", findings=len(findings), chunks=len(chunks))