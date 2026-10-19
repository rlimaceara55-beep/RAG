from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.tokenizer import tokenizer_service
from backend.services.embedder import get_embedder_service
from backend.services.retriever import retriever_service
from backend.services.prompt_builder import prompt_builder_service
from backend.services.llm_client import llm_client
from backend.database import db_client
from backend.config import is_supabase_configured

router = APIRouter(prefix="/api/query", tags=["Consulta RAG"])

class QueryRequest(BaseModel):
    pergunta: str
    base_id: Optional[str] = None  # None ou "" = todas as notas, ou ID de um documento específico

@router.get("/documents")
def list_available_bases():
    """Retorna os documentos disponíveis para seleção da base na interface."""
    if not is_supabase_configured():
        return {"documents": [], "message": "Supabase não conectado"}
    try:
        docs = db_client.list_documents()
        return {"documents": docs}
    except Exception as e:
        return {"documents": [], "error": str(e)}

@router.post("")
def execute_rag_query(payload: QueryRequest):
    """
    Executa o pipeline RAG de ponta a ponta com didática e observabilidade total.
    """
    pergunta = payload.pergunta.strip()
    if not pergunta:
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")

    # 1. Tokenização da Pergunta
    token_info = tokenizer_service.tokenize(pergunta)

    # 2. Geração de Embedding da Pergunta com FastEmbed
    embedder = get_embedder_service()
    query_vector = embedder.embed_query(pergunta)

    # 3. Retrieval (Busca Vetorial no PGVECTOR com top_k = 5)
    retrieval_res = retriever_service.retrieve(
        query=pergunta,
        query_embedding=query_vector,
        filter_doc_id=payload.base_id
    )

    candidates = retrieval_res.get("candidates", [])
    has_data = retrieval_res.get("has_relevant_data", False)

    # 4. Regra de Ausência de Dados: se não houver candidatos, NÃO chama LLM
    if not has_data or len(candidates) == 0:
        return {
            "resposta_final": "Sem dados disponiveis na base",
            "modo": "REGRA_ESTRITA_SEM_DADOS",
            "pipeline": {
                "pergunta": {
                    "texto": pergunta,
                    "base_selecionada": payload.base_id or "Todas as Notas Fiscais"
                },
                "tokenizacao": {
                    "encoding": token_info["encoding"],
                    "token_count": token_info["token_count"],
                    "preview_tokens": token_info["token_pieces"]
                },
                "embedding": {
                    "modelo": embedder.model_name,
                    "dimensao": embedder.dimension,
                    "preview_vetor": [round(v, 4) for v in query_vector[:8]]
                },
                "retrieval": {
                    "top_k": retriever_service.top_k,
                    "threshold_minimo": retriever_service.threshold,
                    "candidatos_recuperados": [],
                    "total_encontrados": 0,
                    "status": "Nenhum candidato atingiu a relevância mínima necessária"
                },
                "prompt_aumentado": {
                    "status": "Ignorado (regra de segurança: sem candidatos para compor contexto)"
                },
                "llm": {
                    "status": "Não acionado (evitou alucinação)"
                }
            }
        }

    # 5. Construção do Prompt Aumentado
    prompt_data = prompt_builder_service.build_augmented_prompt(
        user_query=pergunta,
        candidates=candidates
    )

    # 6. Comunicação com LLM via OpenRouter
    llm_res = llm_client.generate_response(prompt_data["full_augmented_prompt"])
    resposta_final = llm_res.get("content", "Sem dados disponiveis na base")

    return {
        "resposta_final": resposta_final,
        "modo": "RAG_AUMENTADO",
        "pipeline": {
            "pergunta": {
                "texto": pergunta,
                "base_selecionada": payload.base_id or "Todas as Notas Fiscais"
            },
            "tokenizacao": {
                "encoding": token_info["encoding"],
                "token_count": token_info["token_count"],
                "preview_tokens": token_info["token_pieces"]
            },
            "embedding": {
                "modelo": embedder.model_name,
                "dimensao": embedder.dimension,
                "preview_vetor": [round(v, 4) for v in query_vector[:8]]
            },
            "retrieval": {
                "top_k": retriever_service.top_k,
                "threshold_minimo": retriever_service.threshold,
                "total_encontrados": len(candidates),
                "candidatos_recuperados": candidates
            },
            "prompt_aumentado": {
                "chunks_utilizados": prompt_data["chunks_count"],
                "contexto_formatado": prompt_data["formatted_context"],
                "prompt_completo": prompt_data["full_augmented_prompt"]
            },
            "llm": {
                "modelo": llm_res.get("model"),
                "status": "Executado via OpenRouter" if llm_res.get("success") else "Falha no provedor",
                "tokens_utilizados": llm_res.get("usage", {})
            }
        }
    }
