from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.findings_map = {}  # id -> Finding dict
        self.source_map = {}  # id -> source dict (hybrid)
        self.source_ids: list[str] = []
    
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

    def index_hybrid_sources(self, findings: list[dict], chunks: list[dict]) -> None:
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

    def search_hybrid_sources(self, query: str, top_k: int = 8) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32),
            min(top_k, self.index.ntotal),
        )

        results: list[dict] = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.source_ids):
                source = dict(self.source_map[self.source_ids[idx]])
                source["score"] = float(scores[0][i])
                results.append(source)
        return results
