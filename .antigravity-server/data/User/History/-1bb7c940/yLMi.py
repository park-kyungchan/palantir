
import fitz  # PyMuPDF
from typing import List, Optional, Tuple
from lib.ingestors.base import BaseIngestor, IngestorCapabilities
from lib.ir import Document, Section, Paragraph, TextRun, Table, TableRow, TableCell, Figure, Image

class PyMuPDFIngestor(BaseIngestor):
    """Fast ingestor for native digital PDFs using PyMuPDF."""

    def __init__(self, extract_images: bool = True):
        self.extract_images = extract_images

    def ingest(self, path: str) -> Document:
        doc = Document()
        # open document
        try:
            pdf = fitz.open(path)
        except Exception as e:
            raise Exception(f"Failed to open PDF: {e}")

        for page_num, page in enumerate(pdf):
            section = doc.add_section()

            # Extract text blocks with coordinates
            # text_page = page.get_textpage()
            # blocks = text_page.extractDICT()["blocks"]
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)["blocks"]

            # Extract tables
            tables = page.find_tables()
            
            # Simple heuristic: Identify table bbox to exclude text from those areas?
            # For now, PyMuPDF find_tables is separate. We might duplicate content if not careful.
            # Strategy: Process tables, then process text blocks that are NOT inside table rects.
            
            table_rects = [tab.bbox for tab in tables]

            # Process Images
            if self.extract_images:
                # get_images returns (xref, smask, width, height, bpc, colorspace, alt. colorspace, name, filter, referencer)
                image_list = page.get_images()
                for img_info in image_list:
                    xref = img_info[0]
                    # We would extract image bytes here, save to temp, and add Figure/Image to IR.
                    # For prototype, we verify we CAN extract. Real impl would save file.
                    # section.paragraphs.append(Paragraph(elements=[Figure(path=f"img_{xref}.png")]))
                    pass

            # Process Tables
            for tab in tables:
                ir_table = self._convert_table(tab)
                # Wrap table in a paragraph or add directly? IR supports Paragraph elements having Table.
                # But generic structure usually implies Paragraph contains content.
                # Let's add a paragraph containing the table.
                section.elements.append(Paragraph(elements=[ir_table]))

            # Process Text Blocks
            for b in blocks:
                if b['type'] == 0: # Text
                    bbox = fitz.Rect(b['bbox'])
                    # Check if inside any table
                    if any(bbox.intersects(fitz.Rect(tr)) for tr in table_rects):
                        continue # specific text processing inside table usually handled by find_tables?
                        # Actually find_tables extracts text. So safe to skip intersections.
                    
                    for line in b["lines"]:
                        # Concatenate spans in a line
                        runs = []
                        for span in line["spans"]:
                            runs.append(TextRun(
                                text=span["text"],
                                font_size=span["size"],
                                font_name=span["font"]
                            ))
                        if runs:
                            # Create a paragraph for the line (or block).
                            # HWPX usually treats lines as paragraphs if hard break.
                            section.elements.append(Paragraph(elements=runs))

        pdf.close()
        return doc

    def _convert_table(self, fitz_table) -> Table:
        rows = []
        # Header? fitz_table.header check
        
        # Extract data
        data = fitz_table.extract()
        for r_idx, row_data in enumerate(data):
            cells = []
            for col_idx, cell_text in enumerate(row_data):
                # Basic text cell
                if cell_text is None:
                    cell_text = ""
                # Determine colspan/rowspan if possible? 
                # fitz_table.cells gives more detail (rect, text).
                # extract() just gives text matrix.
                # For high fidelity, we should iterate fitz_table.cells if we want span info.
                # For this pass, simple matrix.
                
                # Check for None content (merged cells often appear as None or empty in simple extract?)
                # actually find_tables handles merge somewhat.
                
                runs = [TextRun(text=str(cell_text))]
                cells.append(TableCell(content=runs))
            rows.append(TableRow(cells=cells))
            
        return Table(rows=rows)

    def supports(self, path: str) -> bool:
        return path.lower().endswith('.pdf')

    @property
    def capabilities(self) -> IngestorCapabilities:
        return IngestorCapabilities(
            supports_ocr=False,
            supports_tables=True,
            supports_images=True,
            supports_equations=False,
            supports_multi_column=True,
            supported_languages={'ko', 'en', 'ja', 'zh'}
        )
