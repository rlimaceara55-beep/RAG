from typing import Dict, Any
import httpx
from backend.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, is_openrouter_configured

class OpenRouterClient:
    def __init__(self):
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.model = OPENROUTER_MODEL

    def generate_response(self, augmented_prompt: str) -> Dict[str, Any]:
        """
        Envia o prompt aumentado para o LLM via OpenRouter.
        Garante que a chave de API nunca seja exposta em logs ou respostas.
        """
        if not is_openrouter_configured():
            return {
                "success": False,
                "model": self.model,
                "content": "Erro: OPENROUTER_API_KEY não configurada no arquivo .env",
                "error": "Credencial ausente no .env"
            }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "RAG Didatico Teophilo",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": augmented_prompt
                }
            ],
            "temperature": 0.1,  # Temperatura baixa para máxima fidelidade ao contexto
            "max_tokens": 1000
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(self.endpoint, headers=headers, json=payload)
                if res.status_code != 200:
                    return {
                        "success": False,
                        "model": self.model,
                        "content": f"Erro na chamada ao OpenRouter (HTTP {res.status_code})",
                        "error": f"HTTP {res.status_code}"
                    }
                
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                usage = data.get("usage", {})
                return {
                    "success": True,
                    "model": data.get("model", self.model),
                    "content": content,
                    "usage": {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "content": f"Falha na comunicação com o provedor LLM ({type(e).__name__})",
                "error": type(e).__name__
            }

llm_client = OpenRouterClient()
