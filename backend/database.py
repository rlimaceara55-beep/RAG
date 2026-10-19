from typing import List, Dict, Any, Optional
import httpx
from backend.config import SUPABASE_URL, SUPABASE_KEY, is_supabase_configured

class SupabaseClient:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def check_connection(self) -> Dict[str, Any]:
        if not is_supabase_configured():
            return {"success": False, "message": "SUPABASE: falha na conexão (credenciais ausentes no .env)"}
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{self.base_url}/", headers=self.headers)
                if res.status_code in (200, 204):
                    return {"success": True, "message": "SUPABASE: conexão estabelecida com sucesso"}
                else:
                    return {"success": False, "message": f"SUPABASE: falha na conexão (HTTP {res.status_code})"}
        except Exception as e:
            return {"success": False, "message": f"SUPABASE: falha na conexão ({type(e).__name__})"}

    def insert_document(self, doc_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insere o documento fiscal estruturado na tabela documentos."""
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                f"{self.base_url}/documentos",
                headers=self.headers,
                json=doc_data
            )
            res.raise_for_status()
            data = res.json()
            return data[0] if isinstance(data, list) and data else data

    def insert_chunks(self, chunks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Insere a lista de chunks com embeddings na tabela chunks."""
        if not chunks_data:
            return []
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                f"{self.base_url}/chunks",
                headers=self.headers,
                json=chunks_data
            )
            res.raise_for_status()
            return res.json()

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lista os documentos ingeridos para seleção de base."""
        with httpx.Client(timeout=10.0) as client:
            res = client.get(
                f"{self.base_url}/documentos?select=id,numero_nota,data_emissao,fornecedor,cnpj,cliente,valor_total,created_at&order=created_at.desc",
                headers=self.headers
            )
            res.raise_for_status()
            return res.json()

    def match_chunks(self, query_embedding: List[float], match_threshold: float = 0.3, match_count: int = 5, filter_doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Executa a RPC match_chunks no Supabase para busca vetorial por similaridade de cosseno."""
        payload = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
            "filter_doc_id": filter_doc_id if filter_doc_id else None
        }
        with httpx.Client(timeout=15.0) as client:
            res = client.post(
                f"{self.base_url}/rpc/match_chunks",
                headers=self.headers,
                json=payload
            )
            res.raise_for_status()
            return res.json()

db_client = SupabaseClient()
