from typing import List, Dict, Any

class ChunkerService:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_invoice(self, tabular_data: Dict[str, Any], documento_id: str = None) -> List[Dict[str, Any]]:
        """
        Divide os dados estruturados e o texto da Nota Fiscal em chunks semânticos rastreáveis.
        Cada chunk preserva metadados essenciais de rastreabilidade:
        - documento_id
        - numero_nota
        - chunk_index
        - secao
        """
        numero_nota = tabular_data.get("numero_nota", "NF-S/N")
        data_emissao = tabular_data.get("data_emissao", "")
        fornecedor = tabular_data.get("fornecedor", "")
        cnpj = tabular_data.get("cnpj", "")
        cliente = tabular_data.get("cliente", "")
        valor_total = tabular_data.get("valor_total", 0.0)
        itens = tabular_data.get("itens", [])
        
        chunks = []
        chunk_idx = 0

        # Chunk 1: Cabeçalho e Identificação das Partes
        header_text = (
            f"NOTA FISCAL: {numero_nota} | DATA DE EMISSÃO: {data_emissao}\n"
            f"FORNECEDOR/EMITENTE: {fornecedor} | CNPJ: {cnpj}\n"
            f"CLIENTE/DESTINATÁRIO: {cliente}\n"
            f"VALOR TOTAL DA NOTA: R$ {valor_total:.2f}"
        )
        chunks.append({
            "documento_id": documento_id,
            "numero_nota": numero_nota,
            "chunk_index": chunk_idx,
            "secao": "CABEÇALHO_E_PARTES",
            "conteudo": header_text.strip(),
            "metadata": {
                "numero_nota": numero_nota,
                "data_emissao": data_emissao,
                "fornecedor": fornecedor,
                "cnpj": cnpj,
                "cliente": cliente,
                "tipo_chunk": "identificacao"
            }
        })
        chunk_idx += 1

        # Chunks 2+: Itens de Produtos e Serviços
        if itens:
            for item in itens:
                item_text = (
                    f"NOTA FISCAL: {numero_nota} | ITEM {item.get('item', '1')}\n"
                    f"PRODUTO/SERVIÇO: {item.get('produto', '')}\n"
                    f"QUANTIDADE: {item.get('quantidade', 1)} {item.get('unidade', 'UN')}\n"
                    f"VALOR UNITÁRIO: R$ {item.get('valor_unitario', 0.0):.2f}\n"
                    f"VALOR TOTAL DO ITEM: R$ {item.get('valor_total', 0.0):.2f}\n"
                    f"FORNECEDOR: {fornecedor} | CLIENTE: {cliente}"
                )
                chunks.append({
                    "documento_id": documento_id,
                    "numero_nota": numero_nota,
                    "chunk_index": chunk_idx,
                    "secao": f"PRODUTO_ITEM_{item.get('item', chunk_idx)}",
                    "conteudo": item_text.strip(),
                    "metadata": {
                        "numero_nota": numero_nota,
                        "produto": item.get("produto", ""),
                        "quantidade": item.get("quantidade", 1),
                        "valor_unitario": item.get("valor_unitario", 0.0),
                        "valor_total_item": item.get("valor_total", 0.0),
                        "tipo_chunk": "item_fiscal"
                    }
                })
                chunk_idx += 1
        else:
            # Fallback se não detectou itens tabulares isolados: divide por texto bruto
            raw_text = tabular_data.get("texto_extraido", "")
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            for p in paragraphs:
                if len(p) > 20:
                    chunks.append({
                        "documento_id": documento_id,
                        "numero_nota": numero_nota,
                        "chunk_index": chunk_idx,
                        "secao": f"PARAGRAFO_{chunk_idx}",
                        "conteudo": f"NF: {numero_nota} - {p}",
                        "metadata": {
                            "numero_nota": numero_nota,
                            "tipo_chunk": "texto_corrido"
                        }
                    })
                    chunk_idx += 1

        # Chunk Final: Resumo Financeiro & Totais
        summary_text = (
            f"RESUMO FINANCEIRO DA NOTA FISCAL {numero_nota}\n"
            f"EMITENTE: {fornecedor} (CNPJ: {cnpj})\n"
            f"DESTINATÁRIO: {cliente}\n"
            f"QUANTIDADE DE ITENS FATURADOS: {len(itens)}\n"
            f"VALOR TOTAL CONSOLIDADO: R$ {valor_total:.2f}"
        )
        chunks.append({
            "documento_id": documento_id,
            "numero_nota": numero_nota,
            "chunk_index": chunk_idx,
            "secao": "RESUMO_FINANCEIRO",
            "conteudo": summary_text.strip(),
            "metadata": {
                "numero_nota": numero_nota,
                "valor_total": valor_total,
                "quantidade_itens": len(itens),
                "tipo_chunk": "total_financeiro"
            }
        })

        return chunks

chunker_service = ChunkerService()
