import re
from typing import Dict, Any, List

class TabularStructurerService:
    def structure_invoice_data(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Organiza o texto extraído da Nota Fiscal de forma estruturada e tabular.
        Campos: numero_nota, data_emissao, fornecedor, cnpj, cliente, itens, valor_total.
        """
        raw_text = extraction_result.get("raw_text", "")
        filename = extraction_result.get("filename", "")

        # 1. Número da Nota
        numero_nota = "NF-DESCONHECIDA"
        match_nota = re.search(r"N[ºo\.\s]*:\s*([A-Z0-9\-]+)", raw_text, re.IGNORECASE)
        if match_nota:
            numero_nota = match_nota.group(1).strip()
        elif "NF-" in filename:
            numero_nota = filename.replace(".pdf", "")

        # 2. Data de Emissão
        data_emissao = ""
        match_data = re.search(r"Data de Emiss[aã]o:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", raw_text, re.IGNORECASE)
        if match_data:
            data_emissao = match_data.group(1).strip()

        # 3. Fornecedor e Cliente (Razão Social)
        fornecedor = ""
        cliente = ""
        razoes = re.findall(r"Raz[aã]o Social:\s*([^\n\r]+?)(?:\s+Raz[aã]o Social:|\n|$)", raw_text, re.IGNORECASE)
        if len(razoes) >= 1:
            fornecedor = razoes[0].strip()
        if len(razoes) >= 2:
            cliente = razoes[1].strip()

        # 4. CNPJ Fornecedor e Documento Cliente
        cnpj = ""
        all_cnpjs = re.findall(r"[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}\-[0-9]{2}", raw_text)
        if len(all_cnpjs) >= 1:
            cnpj = all_cnpjs[0].strip()

        # 5. Valor Total da Nota
        valor_total = 0.0
        match_total = re.search(r"VALOR TOTAL DA NOTA:\s*R\$\s*([0-9\.\,]+)", raw_text, re.IGNORECASE)
        if match_total:
            val_str = match_total.group(1).strip()
            # Trata se tiver vírgula ou ponto
            if "," in val_str and "." in val_str:
                val_str = val_str.replace(".", "").replace(",", ".")
            elif "," in val_str:
                val_str = val_str.replace(",", ".")
            try:
                valor_total = float(val_str)
            except ValueError:
                valor_total = 0.0

        # 6. Itens e Produtos
        itens: List[Dict[str, Any]] = []
        tables = extraction_result.get("extracted_tables", [])
        
        for tbl_data in tables:
            rows = tbl_data.get("linhas", [])
            for row in rows:
                if not row or len(row) < 5:
                    continue
                # Ignora cabeçalhos
                if any("Descri" in str(c) or "Item" in str(c) for c in row if c):
                    continue
                
                try:
                    item_num = row[0]
                    desc = row[1]
                    qtd = row[2]
                    unit = row[3] if len(row) > 4 else "UN"
                    v_unit = row[4] if len(row) > 4 else "0"
                    v_tot = row[5] if len(row) > 5 else "0"

                    if desc and qtd:
                        qtd_str = str(qtd).replace(",", ".").strip()
                        qtd_clean = int(float(qtd_str))
                        
                        v_u_str = str(v_unit).strip()
                        if "," in v_u_str and "." in v_u_str:
                            v_u_str = v_u_str.replace(".", "").replace(",", ".")
                        elif "," in v_u_str:
                            v_u_str = v_u_str.replace(",", ".")
                        v_unit_clean = float(v_u_str)

                        v_t_str = str(v_tot).strip()
                        if "," in v_t_str and "." in v_t_str:
                            v_t_str = v_t_str.replace(".", "").replace(",", ".")
                        elif "," in v_t_str:
                            v_t_str = v_t_str.replace(",", ".")
                        v_tot_clean = float(v_t_str)

                        itens.append({
                            "item": str(item_num).strip(),
                            "produto": str(desc).strip(),
                            "quantidade": qtd_clean,
                            "unidade": str(unit).strip(),
                            "valor_unitario": v_unit_clean,
                            "valor_total": v_tot_clean
                        })
                except (ValueError, TypeError, IndexError):
                    continue

        return {
            "numero_nota": numero_nota,
            "data_emissao": data_emissao,
            "fornecedor": fornecedor,
            "cnpj": cnpj,
            "cliente": cliente,
            "itens": itens,
            "valor_total": valor_total,
            "quantidade_itens": len(itens),
            "texto_extraido": raw_text
        }

tabular_service = TabularStructurerService()
