from typing import Dict, Any, List
import tiktoken

class TokenizerService:
    def __init__(self, model_name: str = "cl100k_base"):
        self.encoding_name = model_name
        try:
            self.encoding = tiktoken.get_encoding(model_name)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def tokenize(self, text: str, max_preview: int = 50) -> Dict[str, Any]:
        """
        Tokeniza explicitamente um texto, retornando os IDs numéricos e os fragmentos de texto (tokens).
        Didático: permite ao aluno visualizar a divisão exata em subwords.
        """
        if not text:
            return {
                "encoding": self.encoding_name,
                "token_count": 0,
                "token_ids": [],
                "token_pieces": [],
                "preview_tokens": []
            }

        token_ids = self.encoding.encode(text)
        token_count = len(token_ids)
        
        # Gera os fragmentos textuais dos primeiros N tokens para exibição na UI didática
        preview_ids = token_ids[:max_preview]
        token_pieces = []
        for tid in preview_ids:
            try:
                piece = self.encoding.decode([tid])
                token_pieces.append({"id": tid, "text": piece})
            except Exception:
                token_pieces.append({"id": tid, "text": "<bytes>"})

        return {
            "encoding": self.encoding_name,
            "token_count": token_count,
            "token_ids": token_ids,
            "token_pieces": token_pieces,
            "is_truncated": token_count > max_preview
        }

tokenizer_service = TokenizerService()
