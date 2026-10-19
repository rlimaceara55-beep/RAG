from typing import List, Dict, Any

SYSTEM_INSTRUCTION = """Você é um assistente especialista e estritamente baseado nos documentos fiscais fornecidos como contexto.
Siga rigorosamente as seguintes diretrizes anti-alucinação:
1. Responda à pergunta do usuário utilizando EXCLUSIVAMENTE as informações contidas no contexto recuperado abaixo.
2. Se a informação solicitada não estiver explicitamente contida no contexto recuperado, responda exatamente: "Sem dados disponiveis na base".
3. Nunca invente dados, fornecedores, CNPJs, valores, produtos ou notas fiscais.
4. Seja didático, objetivo e cite a Nota Fiscal e o item específico sempre que responder.
"""

class PromptBuilderService:
    def build_augmented_prompt(self, user_query: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Monta o prompt aumentado combinando:
        1. Instruções do Sistema
        2. Contexto Recuperado dos Chunks do PGVECTOR
        3. Pergunta do Usuário
        """
        context_blocks = []
        for c in candidates:
            block = (
                f"[DOCUMENTO: {c.get('numero_nota', 'N/A')} | CHUNK #{c.get('chunk_index', 0)} | SCORE: {c.get('score', 0)}]\n"
                f"{c.get('conteudo', '')}"
            )
            context_blocks.append(block)

        formatted_context = "\n\n".join(context_blocks)

        augmented_prompt = f"""{SYSTEM_INSTRUCTION}

=========================================
CONTEXTO RECUPERADO DA BASE DE DADOS:
=========================================
{formatted_context}

=========================================
PERGUNTA DO USUÁRIO:
=========================================
{user_query}

RESPOSTA BASEADA ESTRITAMENTE NO CONTEXTO:"""

        return {
            "system_instruction": SYSTEM_INSTRUCTION,
            "formatted_context": formatted_context,
            "user_query": user_query,
            "full_augmented_prompt": augmented_prompt,
            "chunks_count": len(candidates)
        }

prompt_builder_service = PromptBuilderService()
