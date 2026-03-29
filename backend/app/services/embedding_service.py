from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss
import numpy as np
from app.services.retrieval.base import BaseRetrievalService

class EmbeddingService(BaseRetrievalService):
    def __init__(self):
        self._model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.model = SentenceTransformer(self._model_name)
        self.reranker_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self.reranker = None  # Carga lazy (solo se instancia si se usa) para ahorrar memoria RAM en el startup
        self.index = None
        self.findings_map = {}  # id -> Finding dict
        self.source_map = {}  # id -> source dict (hybrid)
        self.source_ids: list[str] = []
    
    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_reranker(self):
        """Carga el modelo de reranking bajo demanda."""
        if self.reranker is None:
            self.reranker = CrossEncoder(self.reranker_name)
        return self.reranker

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """Reordena los candidatos usando un modelo Cross-Encoder más profundo."""
        if not candidates:
            return []
        if len(candidates) <= 1:
            return candidates[:top_k]
            
        reranker = self._get_reranker()
        
        # Preparar pares [query, documento] para el modelo
        pairs = [[query, doc.get("text", "")] for doc in candidates]
        scores = reranker.predict(pairs)
        
        # Actualizar scores con la métrica refinada
        for i, score in enumerate(scores):
            candidates[i]["rerank_score"] = float(score)
            
        # Ordenar por el score del reranker de mayor a menor
        candidates.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return candidates[:top_k]

    def index_findings(self, findings: list[dict]) -> None:
        """Vectoriza todos los findings de una sesión"""
        texts = []
        for f in findings:
            # Combinar what + so_what + title para embedding rico
            text = f"{f.get('title', '')}. {f.get('what', '')} {f.get('so_what', '')}"
            texts.append(text)
            self.findings_map[f['finding_id']] = f
        
        if not texts:
            return
        
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        self.index.add(np.array(embeddings, dtype=np.float32))
    
    def serialize_index(self) -> bytes:
        """Serializa el índice FAISS a bytes"""
        if self.index is None:
            return b""
        return faiss.serialize_index(self.index).tobytes()
    
    def deserialize_index(self, data: bytes) -> None:
        """Carga un índice FAISS desde bytes"""
        if not data:
            return
        serialized = np.frombuffer(data, dtype=np.uint8)
        self.index = faiss.deserialize_index(serialized)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Busca findings relevantes para una query"""
        if self.index is None or self.index.ntotal == 0:
            return list(self.findings_map.values())
        
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32), 
            min(top_k, self.index.ntotal)
        )
        
        results = []
        finding_ids = list(self.findings_map.keys())
        for i, idx in enumerate(indices[0]):
            if idx < len(finding_ids):
                finding = dict(self.findings_map[finding_ids[idx]])
                finding['relevance_score'] = float(scores[0][i])
                results.append(finding)
        
        return results

    async def index_hybrid_sources(self, findings: list[dict], chunks: list[dict]) -> None:
        """
        Construye un índice híbrido findings + chunks documentales.
        No reemplaza el comportamiento actual de index_findings.
        """
        self.source_map = {}
        self.source_ids = []
        texts: list[str] = []

        for finding in findings:
            source_id = finding.get("finding_id")
            if not source_id:
                continue
            text = f"{finding.get('title', '')}. {finding.get('what', '')} {finding.get('so_what', '')}"
            self.source_map[source_id] = {
                "source_type": "finding",
                "source_id": source_id,
                "evidence_ref": source_id,
                "text": text,
                "snippet": text[:240],
            }
            self.source_ids.append(source_id)
            texts.append(text)

        for chunk in chunks:
            source_id = chunk.get("chunk_id")
            if not source_id:
                continue
            text = str(chunk.get("text", ""))
            self.source_map[source_id] = {
                "source_type": "chunk",
                "source_id": source_id,
                "evidence_ref": chunk.get("source_id", source_id),
                "text": text,
                "snippet": chunk.get("snippet", text[:240]),
                "provenance": chunk.get("provenance", {}),
            }
            self.source_ids.append(source_id)
            texts.append(text)

        if not texts:
            self.index = None
            return

        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(np.array(embeddings, dtype=np.float32))

    async def search_hybrid_sources(
        self, 
        query: str, 
        top_k: int = 8,
        **filters
    ) -> list[dict]:
        """Busca fuentes híbridas con soporte para post-filtrado por metadatos."""
        if self.index is None or self.index.ntotal == 0:
            return []

        filter_by_source_type = filters.get("filter_by_source_type")
        filter_by_page = filters.get("filter_by_page")
        filter_by_section = filters.get("filter_by_section")

        # Recuperar un pool más grande (ej. 10x) para permitir descartar candidatos en el post-filtrado
        fetch_k = min(max(top_k * 10, 100), self.index.ntotal)
        
        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32),
            fetch_k,
        )

        candidates: list[dict] = []
        for i, idx in enumerate(indices[0]):
            # Recolectar más candidatos (ej. el triple) para darle contexto al reranker
            if len(candidates) >= max(top_k * 3, 20):
                break
                
            if idx < len(self.source_ids):
                source = dict(self.source_map[self.source_ids[idx]])
                
                # Aplicar post-filtros
                if filter_by_source_type and source.get("source_type") != filter_by_source_type:
                    continue
                    
                # Soportar tanto keys legacy ("provenance") como nuevas ("location")
                prov = source.get("location") or source.get("provenance") or {}
                if filter_by_page and prov.get("page") != filter_by_page:
                    continue
                    
                if filter_by_section:
                    heading = str(prov.get("heading", "")).lower()
                    section_path = str(prov.get("section_path", "")).lower()
                    target = filter_by_section.lower()
                    if target not in heading and target not in section_path:
                        continue

                source["score"] = float(scores[0][i])
                candidates.append(source)
                
        # Aplicar el Reranker solo si hay un volumen sustancial de candidatos (Fase 4, Paso 2)
        if len(candidates) > 10:
            return self.rerank(query, candidates, top_k)
            
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]
