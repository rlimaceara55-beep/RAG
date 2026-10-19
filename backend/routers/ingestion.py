import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.services.ocr_extractor import ocr_service
from backend.services.tabular_structurer import tabular_service
from backend.services.chunker import chunker_service
from backend.services.tokenizer import tokenizer_service
from backend.services.embedder import get_embedder_service
from backend.database import db_client
from backend.config import BASE_DIR, is_supabase_configured

router = APIRouter(prefix="/api/ingest", tags=["Ingestão"])

SAMPLES_DIR = BASE_DIR / "data" / "samples"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class SampleIngestRequest(BaseModel):
    sample_filename: str

def run_ingestion_pipeline(file_path: str) -> dict:
    # 1. OCR & Extração de Texto
    extraction = ocr_service.extract_from_pdf(str(file_path))
    
    # 2. Estruturação Tabular
    tabular_data = tabular_service.structure_invoice_data(extraction)
    
    # 3. Geração de ID único do documento
    doc_id = str(uuid.uuid4())
    
    # 4. Chunking
    raw_chunks = chunker_service.chunk_invoice(tabular_data, documento_id=doc_id)
    
    # 5. Tokenização explícita de cada chunk
    tokenized_chunks = []
    chunk_texts = []
    for chunk in raw_chunks:
        text = chunk["conteudo"]
        chunk_texts.append(text)
        token_info = tokenizer_service.tokenize(text, max_preview=30)
        chunk["token_count"] = token_info["token_count"]
        chunk["tokens"] = token_info["token_pieces"]
        tokenized_chunks.append({
            **chunk,
            "token_info": token_info
        })
        
    # 6. Geração de Embeddings com FastEmbed
    embedder = get_embedder_service()
    embeddings = embedder.embed_texts(chunk_texts)
    
    # Adiciona os embeddings aos chunks
    db_chunks = []
    for idx, (chunk, emb) in enumerate(zip(tokenized_chunks, embeddings)):
        chunk["embedding"] = emb
        chunk["embedding_preview"] = [round(v, 4) for v in emb[:8]]  # Prévia para didática
        db_chunks.append({
            "id": str(uuid.uuid4()),
            "documento_id": doc_id,
            "numero_nota": chunk["numero_nota"],
            "chunk_index": chunk["chunk_index"],
            "conteudo": chunk["conteudo"],
            "token_count": chunk["token_count"],
            "tokens": chunk["tokens"],
            "embedding": emb,
            "metadata": chunk["metadata"]
        })
        
    # 7. Persistência no Supabase (se configurado)
    db_status = "Supabase não configurado (.env pendente) - Processamento concluído em memória"
    if is_supabase_configured():
        try:
            doc_record = {
                "id": doc_id,
                "numero_nota": tabular_data["numero_nota"],
                "data_emissao": tabular_data["data_emissao"],
                "fornecedor": tabular_data["fornecedor"],
                "cnpj": tabular_data["cnpj"],
                "cliente": tabular_data["cliente"],
                "valor_total": tabular_data["valor_total"],
                "dados_tabulares": {
                    "itens": tabular_data["itens"],
                    "quantidade_itens": tabular_data["quantidade_itens"]
                },
                "texto_extraido": tabular_data["texto_extraido"]
            }
            db_client.insert_document(doc_record)
            db_client.insert_chunks(db_chunks)
            db_status = "Persistido com sucesso no Supabase PostgreSQL + PGVECTOR"
        except Exception as e:
            db_status = f"Erro na gravação no Supabase: {str(e)}"
            
    # Retorno completo de observabilidade didática
    return {
        "success": True,
        "documento_id": doc_id,
        "arquivo": os.path.basename(file_path),
        "db_status": db_status,
        "pipeline": {
            "extracao_ocr": {
                "status": "concluída",
                "metodo": extraction["method_used"],
                "paginas": extraction["page_count"],
                "caracteres_extraidos": len(extraction["raw_text"]),
                "raw_text_preview": extraction["raw_text"][:600] + ("..." if len(extraction["raw_text"]) > 600 else "")
            },
            "estruturacao_tabular": {
                "status": "concluída",
                "dados": {
                    "numero_nota": tabular_data["numero_nota"],
                    "data_emissao": tabular_data["data_emissao"],
                    "fornecedor": tabular_data["fornecedor"],
                    "cnpj": tabular_data["cnpj"],
                    "cliente": tabular_data["cliente"],
                    "valor_total": tabular_data["valor_total"],
                    "itens": tabular_data["itens"]
                }
            },
            "chunking": {
                "status": "concluída",
                "total_chunks": len(raw_chunks),
                "chunks": [
                    {
                        "chunk_index": c["chunk_index"],
                        "secao": c["secao"],
                        "conteudo": c["conteudo"],
                        "metadata": c["metadata"]
                    }
                    for c in raw_chunks
                ]
            },
            "tokenizacao": {
                "status": "concluída",
                "encoding": "cl100k_base",
                "total_tokens_documento": sum(c["token_count"] for c in tokenized_chunks),
                "detalhes": [
                    {
                        "chunk_index": c["chunk_index"],
                        "token_count": c["token_count"],
                        "preview_tokens": c["token_info"]["token_pieces"][:12]
                    }
                    for c in tokenized_chunks
                ]
            },
            "embedding": {
                "status": "concluída",
                "modelo": embedder.model_name,
                "dimensao": embedder.dimension,
                "vetores_gerados": len(embeddings),
                "amostras": [
                    {
                        "chunk_index": c["chunk_index"],
                        "dimensao": len(c["embedding"]),
                        "preview_vetor": c["embedding_preview"]
                    }
                    for c in tokenized_chunks
                ]
            },
            "indice_vetorial": {
                "status": "concluída" if "sucesso" in db_status.lower() else "aviso",
                "mensagem": db_status
            }
        }
    }

@router.get("/samples")
def list_sample_invoices():
    """Lista as notas fiscais de teste disponíveis."""
    if not SAMPLES_DIR.exists():
        return {"samples": []}
    files = [f.name for f in SAMPLES_DIR.glob("*.pdf")]
    return {"samples": sorted(files)}

@router.post("/process-sample")
def process_sample_invoice(payload: SampleIngestRequest):
    """Processa uma das 4 notas fiscais fictícias."""
    sample_file = SAMPLES_DIR / payload.sample_filename
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="Arquivo de teste não encontrado.")
    return run_ingestion_pipeline(str(sample_file))

@router.post("/upload")
async def upload_and_process_invoice(file: UploadFile = File(...)):
    """Faz upload de uma Nota Fiscal e executa o pipeline RAG completo."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
        
    save_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return run_ingestion_pipeline(str(save_path))
