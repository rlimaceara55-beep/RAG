from typing import List, Dict, Any, Optional
from backend.database import db_client
from backend.services.embedder import get_embedder_service

SIMILARITY_THRESHOLD = 0.45  # Limiar mínimo de relevância semântica

class RetrieverService:
    def __init__(self, top_k: int = 5, threshold: float = SIMILARITY_THRESHOLD):
        self.top_k = top_k
        self.threshold = threshold

    def retrieve(self, query: str, query_embedding: List[float], filter_doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa busca vetorial no Supabase através da RPC match_chunks.
        Retorna os top_k candidatos e avalia a regra de ausência de dados.
        """
        try:
            raw_candidates = db_client.match_chunks(
                query_embedding=query_embedding,
                match_threshold=self.threshold,
                match_count=self.top_k,
                filter_doc_id=filter_doc_id
            )
        except Exception as e:
            print(f"[Retriever] Erro ao consultar PGVECTOR: {str(e)}")
            raw_candidates = []

        # Formatação didática dos candidatos com ranking
        ranked_candidates = []
        for idx, item in enumerate(raw_candidates, start=1):
            ranked_candidates.append({
                "rank": idx,
                "chunk_id": item.get("id"),
                "documento_id": item.get("documento_id"),
                "numero_nota": item.get("numero_nota", "N/A"),
                "chunk_index": item.get("chunk_index"),
                "conteudo": item.get("conteudo", ""),
                "score": round(float(item.get("similarity", 0.0)), 4),
                "metadata": item.get("metadata", {})
            })

        has_relevant_data = len(ranked_candidates) > 0

        return {
            "query": query,
            "filter_doc_id": filter_doc_id,
            "top_k": self.top_k,
            "threshold": self.threshold,
            "total_found": len(ranked_candidates),
            "candidates": ranked_candidates,
            "has_relevant_data": has_relevant_data
        }

retriever_service = RetrieverService()
