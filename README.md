# RAG + Teophilo — Pipeline Didático de RAG

Sistema completo, funcional e visualmente observável de **RAG (Retrieval-Augmented Generation)** focado no aprendizado prático e didático de Engenharia de Dados, OCR, Tokenização, Embeddings, Busca Vetorial no Supabase (PGVECTOR) e LLM com regras estritas anti-alucinação.

---

## 🎯 Objetivo Educacional

Permitir que o aluno visualize com clareza **o que acontece em cada etapa do pipeline RAG**:
1. **Documento de Entrada**: Notas Fiscais em PDF (dados brutos);
2. **Extração & OCR**: Leitura nativa e extração tabular com `pdfplumber` e `pypdf`;
3. **Estruturação Tabular**: Organização dos campos da NF-e (número, data, fornecedor, CNPJ, cliente, produtos, valores);
4. **Chunking**: Divisão em blocos semânticos rastreáveis com metadados de origem;
5. **Tokenização Explícita**: Decomposição em tokens e subwords via `tiktoken` (`cl100k_base`);
6. **Embeddings Locais**: Geração de vetores de 384 dimensões utilizando **FastEmbed** (`BAAI/bge-small-en-v1.5`);
7. **Persistência Vetorial**: Armazenamento no **Supabase** via PostgreSQL + extensão **PGVECTOR**;
8. **Busca Semântica & Retrieval**: Similaridade de cosseno com ranking dos **top_k = 5** melhores candidatos;
9. **Regra Estrita Anti-Alucinação**: Ausência de candidatos relevantes retorna exatamente `"Sem dados disponiveis na base"` sem acionar o LLM;
10. **Prompt Aumentado**: Injeção do contexto recuperado com instruções de fidelidade absoluta;
11. **Geração com LLM**: Chamada segura ao **OpenRouter** para produção da resposta explicativa.

---

## 🏗️ Estrutura do Projeto

```
rag/
├── .env                              # Credenciais sensíveis (SUPABASE e OPENROUTER)
├── .env.example                      # Template de variáveis de ambiente
├── rag.txt                           # Especificação técnica e arquitetural
├── prompt.txt                        # Especificação do Prompt Mestre
├── requirements.txt                  # Dependências Python
├── scripts/
│   ├── test_supabase.py              # Teste seguro de conectividade com Supabase
│   ├── generate_sample_invoices.py   # Gerador dos 4 PDFs fictícios de Notas Fiscais
│   ├── setup_database.sql           # Schema SQL e função match_chunks para o Supabase
│   └── run_all_tests.py              # Suíte unificada dos 15 testes obrigatórios
├── backend/
│   ├── main.py                       # Servidor FastAPI com rotas e arquivos estáticos
│   ├── config.py                     # Configurações e variáveis de ambiente
│   ├── database.py                   # Cliente de comunicação com o Supabase REST/PGVECTOR
│   ├── services/
│   │   ├── ocr_extractor.py          # Leitura e extração de texto em PDF/OCR
│   │   ├── tabular_structurer.py     # Estruturação dos dados fiscais
│   │   ├── chunker.py                # Chunking semântico com rastreabilidade
│   │   ├── tokenizer.py              # Tokenização explícita com tiktoken
│   │   ├── embedder.py               # FastEmbed (384 dimensões)
│   │   ├── retriever.py              # Busca vetorial top_k=5 no PGVECTOR
│   │   ├── prompt_builder.py         # Montagem do prompt aumentado
│   │   └── llm_client.py             # Cliente OpenRouter
│   └── routers/
│       ├── health.py                 # Status dos serviços
│       ├── ingestion.py              # Upload e ingestão passo a passo
│       └── query.py                  # Consulta RAG e observabilidade
├── frontend/
│   ├── index.html                    # Interface Web com Chat e Painel Didático
│   ├── styles.css                    # Design escuro, moderno, glassmorphism e responsivo
│   └── app.js                        # Lógica reativa de chat e renderização dos pipelines
└── data/
    ├── samples/                      # 4 Notas Fiscais fictícias (NF-1001 a NF-1004)
    └── uploads/                      # Uploads de novos PDFs
```

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
- Python 3.10+ (utilizado Python 3.13)
- Ambiente virtual configurado (`.venv`)

### 2. Ativação do Ambiente e Instalação
```bash
# Criar e ativar o ambiente virtual (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração do `.env`
Crie o arquivo `.env` na raiz do projeto baseado no `.env.example`:
```env
SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOi...
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.0-flash-001
```

### 4. Configuração do Banco de Dados no Supabase
Execute o script [`scripts/setup_database.sql`](file:///c:/Users/jacksonlima6006/Documents/rag/scripts/setup_database.sql) no **SQL Editor** do seu painel do Supabase para criar as tabelas `documentos`, `chunks` e a função RPC `match_chunks`.

### 5. Execução dos Testes
Para verificar todos os 15 estágios do projeto:
```bash
.\.venv\Scripts\python scripts/run_all_tests.py
```

### 6. Inicialização do Servidor e Interface Web
```bash
.\.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Acesse a aplicação no seu navegador: **`http://127.0.0.1:8000`**

---

## 🔒 Princípios de Segurança e Boas Práticas

- As chaves de API nunca são exibidas no frontend, no console ou em logs;
- Variáveis são carregadas exclusivamente via `.env`;
- O frontend é desacoplado do banco e consome apenas a API estruturada do FastAPI;
- Ausência de correspondência semântica impede alucinações e não consome tokens de LLM desnecessariamente.
