-- ==============================================================================
-- Script de Configuração do Banco de Dados Supabase (PostgreSQL + PGVECTOR)
-- Projeto: RAG Didático - RAG + Teophilo
-- ==============================================================================

-- 1. Habilitar a extensão PGVECTOR
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabela de Documentos (Notas Fiscais)
CREATE TABLE IF NOT EXISTS documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero_nota TEXT NOT NULL,
    data_emissao TEXT,
    fornecedor TEXT,
    cnpj TEXT,
    cliente TEXT,
    valor_total NUMERIC,
    dados_tabulares JSONB,
    texto_extraido TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Tabela de Chunks e Embeddings
-- FastEmbed bge-small-en-v1.5 gera vetores de dimensão 384
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID REFERENCES documentos(id) ON DELETE CASCADE,
    numero_nota TEXT,
    chunk_index INT NOT NULL,
    conteudo TEXT NOT NULL,
    token_count INT NOT NULL,
    tokens JSONB,
    embedding vector(384) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Índice para busca vetorial rápida por Cosseno (ivfflat ou hnsw)
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx 
ON chunks 
USING hnsw (embedding vector_cosine_ops);

-- 5. Função RPC para busca vetorial por similaridade (retrieval com top_k)
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.0,
    match_count int DEFAULT 5,
    filter_doc_id text DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    documento_id UUID,
    numero_nota TEXT,
    chunk_index INT,
    conteudo TEXT,
    token_count INT,
    metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.documento_id,
        c.numero_nota,
        c.chunk_index,
        c.conteudo,
        c.token_count,
        c.metadata,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE (filter_doc_id IS NULL OR filter_doc_id = '' OR c.documento_id::text = filter_doc_id)
      AND (1 - (c.embedding <=> query_embedding)) >= match_threshold
    ORDER BY c.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;
