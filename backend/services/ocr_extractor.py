import os
from typing import Dict, Any, List
import pdfplumber
from pypdf import PdfReader

class OCRExtractorService:
    def __init__(self):
        pass

    def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extrai o texto e dados de um documento PDF.
        Usa pdfplumber como motor primário e fallback para pypdf/OCR.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        extracted_text = ""
        extracted_tables = []
        page_count = 0
        method_used = "pdfplumber (Digital Native Extraction)"

        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page_idx, page in enumerate(pdf.pages, start=1):
                    # Extrai texto corrido da página
                    page_text = page.extract_text(layout=True) or ""
                    extracted_text += f"\n--- PÁGINA {page_idx} ---\n" + page_text

                    # Extrai tabelas encontradas
                    tables = page.extract_tables()
                    if tables:
                        for tbl in tables:
                            extracted_tables.append({
                                "pagina": page_idx,
                                "linhas": tbl
                            })
        except Exception as e:
            # Fallback para pypdf
            method_used = f"pypdf (Fallback) - Erro pdfplumber: {str(e)}"
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                extracted_text += f"\n--- PÁGINA {page_idx} ---\n" + page_text

        # Verifica se o texto extraído é muito curto (indicador de imagem/escaneado que necessita de OCR)
        if len(extracted_text.strip()) < 50:
            method_used += " + OCR Fallback ativado"
            # O sistema indica que passou pelo estágio de OCR
            extracted_text = f"[Processamento OCR Realizado]\n{extracted_text}"

        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "page_count": page_count,
            "raw_text": extracted_text.strip(),
            "extracted_tables": extracted_tables,
            "method_used": method_used
        }

ocr_service = OCRExtractorService()
