import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_invoice(file_path, invoice_data):
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'InvoiceSection',
        parent=styles['Heading3'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    
    elements = []
    
    # Cabeçalho
    elements.append(Paragraph(f"<b>DANFE - DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRÔNICA</b>", title_style))
    elements.append(Paragraph(f"Nº: <b>{invoice_data['numero_nota']}</b> | Série: 001 | Data de Emissão: <b>{invoice_data['data_emissao']}</b>", subtitle_style))
    elements.append(Spacer(1, 10))
    
    # Dados do Emitente e Destinatário
    party_data = [
        [
            Paragraph(f"<b>EMITENTE / FORNECEDOR</b><br/>"
                      f"Razão Social: {invoice_data['fornecedor']}<br/>"
                      f"CNPJ: {invoice_data['cnpj']}<br/>"
                      f"Endereço: {invoice_data['endereco_fornecedor']}<br/>"
                      f"Município/UF: {invoice_data['cidade_fornecedor']}", body_style),
            Paragraph(f"<b>DESTINATÁRIO / CLIENTE</b><br/>"
                      f"Razão Social: {invoice_data['cliente']}<br/>"
                      f"CNPJ/CPF: {invoice_data['cliente_doc']}<br/>"
                      f"Endereço: {invoice_data['endereco_cliente']}<br/>"
                      f"Município/UF: {invoice_data['cidade_cliente']}", body_style)
        ]
    ]
    
    party_table = Table(party_data, colWidths=[260, 260])
    party_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(party_table)
    elements.append(Spacer(1, 15))
    
    # Itens / Produtos
    elements.append(Paragraph("<b>DADOS DOS PRODUTOS / SERVIÇOS</b>", section_style))
    
    item_header = ['Item', 'Descrição do Produto / Serviço', 'Qtd', 'Un', 'Valor Unit (R$)', 'Valor Total (R$)']
    table_rows = [item_header]
    
    for idx, item in enumerate(invoice_data['itens'], start=1):
        table_rows.append([
            str(idx),
            item['descricao'],
            str(item['quantidade']),
            item.get('unidade', 'UN'),
            f"{item['valor_unitario']:.2f}",
            f"{item['valor_total']:.2f}"
        ])
        
    items_table = Table(table_rows, colWidths=[30, 240, 40, 35, 85, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))
    
    # Totais e Observações
    total_data = [
        [
            Paragraph(f"<b>Informações Complementares:</b><br/>{invoice_data['observacoes']}", body_style),
            Paragraph(f"<b>Base de Cálculo ICMS:</b> R$ {invoice_data['valor_total']:.2f}<br/>"
                      f"<b>Valor do Frete:</b> R$ 0,00<br/>"
                      f"<b>VALOR TOTAL DA NOTA:</b> <font size=12 color='#0F172A'><b>R$ {invoice_data['valor_total']:.2f}</b></font>", body_style)
        ]
    ]
    total_table = Table(total_data, colWidths=[320, 200])
    total_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(total_table)
    
    doc.build(elements)
    print(f"[OK] Gerada: {file_path}")

def generate_all_samples():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")
    os.makedirs(output_dir, exist_ok=True)
    
    # Documento 1: Tecnologia e Servidores
    doc1 = {
        "numero_nota": "NF-1001",
        "data_emissao": "10/01/2026",
        "fornecedor": "TechCloud Soluções em Servidores Ltda",
        "cnpj": "12.345.678/0001-90",
        "endereco_fornecedor": "Av. Paulista, 1500 - Bela Vista",
        "cidade_fornecedor": "São Paulo/SP",
        "cliente": "Empresa Alpha Logística S.A.",
        "cliente_doc": "98.765.432/0001-10",
        "endereco_cliente": "Rua das Flores, 300 - Centro",
        "cidade_cliente": "Campinas/SP",
        "itens": [
            {"descricao": "Servidor Dell PowerEdge R750 32GB RAM", "quantidade": 2, "unidade": "UN", "valor_unitario": 14500.00, "valor_total": 29000.00},
            {"descricao": "Switch Gerenciável 24 Portas Gigabit Cisco", "quantidade": 3, "unidade": "UN", "valor_unitario": 2800.00, "valor_total": 8400.00},
            {"descricao": "Nobreak Senoidal Rack 3000VA APC", "quantidade": 1, "unidade": "UN", "valor_unitario": 4200.00, "valor_total": 4200.00}
        ],
        "valor_total": 41600.00,
        "observacoes": "Equipamentos de infraestrutura destinados ao datacenter primário. Garantia on-site de 36 meses."
    }
    
    # Documento 2: Licenças de Software e Nuvem
    doc2 = {
        "numero_nota": "NF-1002",
        "data_emissao": "15/01/2026",
        "fornecedor": "Nexus Inteligência de Dados e Software S.A.",
        "cnpj": "23.456.789/0001-01",
        "endereco_fornecedor": "Rua Funchal, 418 - Vila Olímpia",
        "cidade_fornecedor": "São Paulo/SP",
        "cliente": "Beta Varejo e Comércio Digital Ltda",
        "cliente_doc": "45.123.789/0001-55",
        "endereco_cliente": "Av. Getúlio Vargas, 1020 - Savassi",
        "cidade_cliente": "Belo Horizonte/MG",
        "itens": [
            {"descricao": "Licença Anual Nexus Data Warehouse Enterprise", "quantidade": 5, "unidade": "LIC", "valor_unitario": 3600.00, "valor_total": 18000.00},
            {"descricao": "Treinamento Especializado em Engenharia de Dados RAG (40h)", "quantidade": 1, "unidade": "SRV", "valor_unitario": 8500.00, "valor_total": 8500.00},
            {"descricao": "Suporte Premium 24x7 SLA 1 hora (Plano Semestral)", "quantidade": 1, "unidade": "SRV", "valor_unitario": 6200.00, "valor_total": 6200.00}
        ],
        "valor_total": 32700.00,
        "observacoes": "Prestação de serviços e licenciamento digital. Faturamento direto para centro de custos TI."
    }
    
    # Documento 3: Mobiliário Corporativo e Escritório
    doc3 = {
        "numero_nota": "NF-1003",
        "data_emissao": "22/01/2026",
        "fornecedor": "ErgoOffice Móveis Corporativos Ltda",
        "cnpj": "34.567.890/0001-12",
        "endereco_fornecedor": "Rodovia Anhanguera, km 104 - Distrito Industrial",
        "cidade_fornecedor": "Jundiaí/SP",
        "cliente": "Gama Consultoria Estratégica EIRELI",
        "cliente_doc": "56.789.012/0001-33",
        "endereco_cliente": "Praça XV de Novembro, 20 - Centro",
        "cidade_cliente": "Rio de Janeiro/RJ",
        "itens": [
            {"descricao": "Cadeira Ergonômica Presidente NR-17 Mesh Pro", "quantidade": 15, "unidade": "UN", "valor_unitario": 890.00, "valor_total": 13350.00},
            {"descricao": "Mesa Plataforma de Trabalho 4 Lugares com Calha Elétrica", "quantidade": 4, "unidade": "UN", "valor_unitario": 2450.00, "valor_total": 9800.00},
            {"descricao": "Armário Alto com Chave e Gaveteiro Volante", "quantidade": 6, "unidade": "UN", "valor_unitario": 750.00, "valor_total": 4500.00}
        ],
        "valor_total": 27650.00,
        "observacoes": "Entrega agendada no 5º andar. Montagem inclusa realizada pela equipe técnica do fabricante."
    }
    
    # Documento 4: Materiais e Cabos de Conectividade
    doc4 = {
        "numero_nota": "NF-1004",
        "data_emissao": "28/01/2026",
        "fornecedor": "FibraNet Distribuidora de Redes e Fibras Ópticas",
        "cnpj": "45.678.901/0001-23",
        "endereco_fornecedor": "Rua Santa Ifigênia, 780 - Centro",
        "cidade_fornecedor": "São Paulo/SP",
        "cliente": "Delta Telecomunicações e Fibra Ltda",
        "cliente_doc": "67.890.123/0001-44",
        "endereco_cliente": "Av. Beira Mar, 500 - Meireles",
        "cidade_cliente": "Fortaleza/CE",
        "itens": [
            {"descricao": "Bobina de Cabo de Rede Furukawa Cat6 UTP 305m", "quantidade": 8, "unidade": "CX", "valor_unitario": 720.00, "valor_total": 5760.00},
            {"descricao": "Patch Panel 24 Portas Cat6 Carregado", "quantidade": 5, "unidade": "UN", "valor_unitario": 310.00, "valor_total": 1550.00},
            {"descricao": "Conector RJ45 Macho Cat6 Blindado (Pacote com 100un)", "quantidade": 10, "unidade": "PCT", "valor_unitario": 125.00, "valor_total": 1250.00},
            {"descricao": "Rack Fechado 19 Polegadas 44U Piso com Porta de Vidro", "quantidade": 1, "unidade": "UN", "valor_unitario": 3400.00, "valor_total": 3400.00}
        ],
        "valor_total": 11960.00,
        "observacoes": "Materiais para expansão de cabeamento estruturado e redes ópticas. Transporte rodoviário segurado."
    }
    
    invoices = [doc1, doc2, doc3, doc4]
    
    for inv in invoices:
        pdf_path = os.path.join(output_dir, f"{inv['numero_nota']}.pdf")
        create_invoice(pdf_path, inv)
        
    print("\n[SUCESSO] 4 Notas Fiscais fictícias geradas com sucesso em data/samples/")

if __name__ == "__main__":
    generate_all_samples()
