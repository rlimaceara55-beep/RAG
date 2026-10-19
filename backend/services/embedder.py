from typing import List, Dict, Any
from fastembed import TextEmbedding
from backend.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION

class FastEmbedService:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.dimension = EMBEDDING_DIMENSION
        # Inicialização do FastEmbed (faz download/carregamento otimizado com ONNX Runtime)
        print(f"[FastEmbed] Carregando modelo de embeddings: {self.model_name}...")
        self.embedding_model = TextEmbedding(model_name=self.model_name)
        print(f"[FastEmbed] Modelo carregado com sucesso. Dimensão: {self.dimension}")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings vetoriais para uma lista de textos/chunks."""
        if not texts:
            return []
        embeddings_generator = self.embedding_model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]

    def embed_query(self, query: str) -> List[float]:
        """Gera o embedding vetorial da pergunta do usuário."""
        embeddings = self.embed_texts([query])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    def get_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "provider": "FastEmbed (FlagEmbedding ONNX)",
            "device": "CPU / Otimizado"
        }

# Lazy instance ou instância sob demanda para evitar carregar caso só importe config
_embedder_instance = None

def get_embedder_service() -> FastEmbedService:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = FastEmbedService()
    return _embedder_instance
