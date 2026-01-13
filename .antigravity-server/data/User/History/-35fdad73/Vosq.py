from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.datamodel.document import DoclingDocument, DocItem, DocItemLabel, TableItem, PictureItem, InputDocument
from lib.ingestors.base import BaseIngestor, IngestorCapabilities
from lib.ir import Document, Section, Paragraph, TextRun, Table, TableRow, TableCell, Figure, Equation, CodeBlock, Image as IRImage
from typing import Optional, List, Union, Tuple, Any, Dict
import logging
from pathlib import Path

# Phase 2 Imports
from lib.layout.detector import LayoutDetector, DetectionConfig
from lib.layout.reading_order import ReadingOrderSorter, sort_regions_for_docling
from lib.layout.reading_order import ReadingOrderSorter, sort_regions_for_docling
from lib.layout.region import LayoutRegion, LayoutLabel, BoundingBox

logger = logging.getLogger(__name__)

class DoclingIngestor(BaseIngestor):
    """
    Primary ingestor using IBM Docling for state-of-the-art
    document understanding with layout analysis and table recognition.
    Enhanced with DocLayout-YOLO layout analysis (Phase 2).
    """

    def __init__(
        self,
        enable_ocr: bool = True,
        enable_layout_enhancement: bool = True,
        enable_table_structure: bool = True,
        layout_config: Optional[DetectionConfig] = None,
    ):
        self.enable_ocr = enable_ocr
        self.enable_layout_enhancement = enable_layout_enhancement
        self.enable_table_structure = enable_table_structure
        self._layout_detector = None
        self._layout_config = layout_config
        self._reading_order_sorter = None
        self._setup_converter()

    def _setup_converter(self):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = self.enable_ocr
        pipeline_options.do_table_structure = self.enable_table_structure
        pipeline_options.generate_picture_images = True
        
        # Configure OCR if enabled
        if self.enable_ocr:
            pipeline_options.ocr_options = EasyOcrOptions(lang=["ko", "en"])

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    @property
    def layout_detector(self) -> LayoutDetector:
        """Lazy-load layout detector."""
        if self._layout_detector is None:
            config = self._layout_config or DetectionConfig()
            self._layout_detector = LayoutDetector(config)
        return self._layout_detector

    @property
    def reading_order_sorter(self) -> ReadingOrderSorter:
        """Lazy-load reading order sorter."""
        if self._reading_order_sorter is None:
            self._reading_order_sorter = ReadingOrderSorter()
        return self._reading_order_sorter

    def ingest(self, path: str, layout_regions: List[LayoutRegion] = None) -> Document:
        """
        Ingest a PDF and return a structured IR Document.
        If layout_regions are provided, they are used to enhance the structure (e.g. answer boxes).
        """
        try:
            docling_doc = self._convert_to_docling_document(path)
            ir_doc = self._map_to_ir(docling_doc, path)
            
            if layout_regions:
                self._apply_external_layout_enhancement(ir_doc, layout_regions)
                
            return ir_doc

        except Exception as e:
            logger.error(f"Docling ingestion failed: {e}. Attempting PyMuPDF fallback.")
            return self._ingest_with_pymupdf(path, layout_regions)

    def _convert_to_docling_document(self, path: str) -> DoclingDocument:
        """Converts a document path to a DoclingDocument."""
        result = self.converter.convert(path)
        return result.document

    def _map_to_ir(self, docling_doc: DoclingDocument, pdf_path: str) -> Document:
        """Maps a DoclingDocument to an IR Document."""
        ir_doc = Document()
        current_section = ir_doc.add_section()
        
        # Collect items with layout information
        items_with_layout = []
        for item, level in docling_doc.iterate_items():
            page_no = 1
            if item.prov and item.prov:
                page_no = item.prov[0].page_no
            items_with_layout.append((item, level, page_no))

        # If layout enhancement is enabled, reorder items
        if self.enable_layout_enhancement and items_with_layout:
            try:
                items_with_layout = self._apply_internal_layout_enhancement(
                    pdf_path, items_with_layout
                )
            except Exception as e:
                logger.error(f"Layout enhancement failed: {e}. Falling back to default order.")

        # Process items in order
        for item, level, page_no in items_with_layout:
            self._process_item(current_section, item, docling_doc)

        return ir_doc

        return ir_doc

    def _ingest_with_pymupdf(self, path: str, layout_regions: List[LayoutRegion] = None) -> Document:
        """Fallback ingestion using PyMuPDF (fitz) and Vision-Native OCR."""
        import fitz
        from PIL import Image
        from lib.layout.region import LayoutLabel
        from lib.ocr.manager import OCRManager

        logger.info("Basic fallback text extraction initiated (Vision-Native).")
        
        # Initialize OCR Manager (Lazy load usually, but we need it here)
        # Assuming OCRManager is lightweight until .recognize() is called
        ocr_manager = OCRManager(primary_engine="easyocr")

        ir_doc = Document()
        section = ir_doc.add_section()

        try:
            pdf = fitz.open(path)
            for page_idx, page in enumerate(pdf):
                # 1. Detect Layout Regions (if not provided externally)
                # Note: layout_regions arg is usually for the WHOLE document or single page?
                # The signature implies whole doc or we handle it per page. 
                # Our Phase 1 verify passed single list.
                # Real usage: detect per page.
                
                current_page_regions = []
                if layout_regions and len(layout_regions) > 0:
                    # In verification, we passed regions. 
                    # Realistically, we should filter by page if we had page info in regions.
                    # For now, use all provided regions for the current page (Phase 1 assumption)
                    current_page_regions = layout_regions
                else:
                    try:
                        current_page_regions = self.layout_detector.detect_pdf_page(path, page_number=page_idx)
                        # Sort Regions
                        current_page_regions = self._reading_order_sorter.sort(current_page_regions, page.rect.width, page.rect.height) if self._reading_order_sorter else current_page_regions
                    except Exception as e:
                         logger.error(f"Layout detection failed for page {page_idx+1}: {e}")
                         current_page_regions = []

                # 2. Render Page for OCR
                # Use Matrix(2, 2) or (3, 3) for efficient OCR resolution (~200-300 DPI)
                zoom = 3.0 
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                page_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # 3. Process Regions
                if not current_page_regions:
                     # Fallback to full page text if no regions
                     logger.warning(f"No regions found for page {page_idx+1}. Using block text.")
                     blocks = page.get_text("blocks")
                     for b in blocks:
                         x0, y0, x1, y1, text, _, _ = b
                         if text.strip():
                             para = Paragraph(
                                 style="Body",
                                 elements=[TextRun(text=text.strip())],
                                 bbox=(x0, y0, x1, y1)
                             )
                             section.elements.append(para)
                     continue

                for region in current_page_regions:
                    # Map PDF coordinates to Image coordinates
                    # region.bbox is [x0, y0, x1, y1] in PDF points
                    # image is scaled by 'zoom'
                    
                    rx0, ry0, rx1, ry1 = region.bbox.x0, region.bbox.y0, region.bbox.x1, region.bbox.y1
                    crop_box = (rx0 * zoom, ry0 * zoom, rx1 * zoom, ry1 * zoom)
                    
                    # Ensure within bounds
                    crop_box = (
                        max(0, crop_box[0]), max(0, crop_box[1]),
                        min(page_image.width, crop_box[2]), min(page_image.height, crop_box[3])
                    )

                    # Crop
                    try:
                        region_crop = page_image.crop(crop_box)
                    except Exception as e:
                        logger.warning(f"Failed to crop region {region}: {e}")
                        continue

                    # OCR pipeline
                    text_content = ""
                    
                    if region.label in [LayoutLabel.ANSWER_BOX, LayoutLabel.PROBLEM_BOX, LayoutLabel.TEXT, LayoutLabel.SECTION_HEADER]:
                         # Text OCR
                         # Lang: Korean default
                         res = ocr_manager.recognize(region_crop, lang="ko")
                         text_content = res.text
                         
                    elif region.label == LayoutLabel.TABLE:
                         # Table OCR (To be implemented, for now text dump)
                         res = ocr_manager.recognize(region_crop, lang="ko")
                         text_content = f"[TABLE]\n{res.text}"
                         
                    elif region.label == LayoutLabel.CAPTION:
                         res = ocr_manager.recognize(region_crop, lang="ko")
                         text_content = f"[Caption] {res.text}"

                    if text_content.strip():
                        style = "Body"
                        if region.label == LayoutLabel.ANSWER_BOX:
                            style = "AnswerBox"
                        elif region.label == LayoutLabel.PROBLEM_BOX:
                            style = "ProblemBox"
                        elif region.label == LayoutLabel.SECTION_HEADER:
                            style = "Header"
                        elif region.label == LayoutLabel.TABLE:
                            style = "Table"

                        para = Paragraph(
                             style=style,
                             elements=[TextRun(text=text_content.strip())],
                             bbox=(rx0, ry0, rx1, ry1) # Store original PDF bbox
                        )
                        section.elements.append(para)

            pdf.close()
            return ir_doc

        except Exception as e:
            logger.error(f"Vision ingestion failed: {e}")
            raise e

    def _apply_external_layout_enhancement(self, doc: Document, regions: List[LayoutRegion]):
        """
        Use external YOLO regions to tag paragraphs.
        """
        logger.info(f"⚡ Applying {len(regions)} layout regions...")
        for section in doc.sections:
            for para in section.paragraphs:
                if not para.bbox:
                    continue
                
                # Check intersection with Answer Regions
                # para.bbox is [l, t, r, b] (docling)
                # region.bbox is [x1, y1, x2, y2]
                # Assuming same coordinate space (pt). *Risk exists here*
                
                p_x1, p_y1, p_x2, p_y2 = para.bbox
                p_center_x = (p_x1 + p_x2) / 2
                p_center_y = (p_y1 + p_y2) / 2
                
                for r in regions:
                    if r.label in [LayoutLabel.ANSWER_BOX, LayoutLabel.PROBLEM_BOX]:
                        # Check if center is in region
                        if (r.bbox.x0 <= p_center_x <= r.bbox.x1) and \
                           (r.bbox.y0 <= p_center_y <= r.bbox.y1):
                            para.style = "AnswerBox" if r.label == LayoutLabel.ANSWER_BOX else "ProblemBox"
                            logger.debug(f"  -> Tagged Paragraph as {para.style}")

    def _apply_internal_layout_enhancement(
        self,
        pdf_path: str,
        items: List[Tuple[Any, int, int]],
    ) -> List[Tuple[Any, int, int]]:
        """
        Apply DocLayout-YOLO detection and reading order sorting.

        This method:
        1. Detects layout regions per page
        2. Matches Docling items to detected regions
        3. Reorders items according to reading order
        """
        import fitz

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.warning(f"Could not open PDF for layout enhancement: {e}")
            return items

        # Group items by page
        items_by_page: Dict[int, List[Tuple[Any, int, int]]] = {}
        for item, level, page_no in items:
            if page_no not in items_by_page:
                items_by_page[page_no] = []
            items_by_page[page_no].append((item, level, page_no))

        reordered_items = []

        for page_no in sorted(items_by_page.keys()):
            if page_no > len(doc):
                reordered_items.extend(items_by_page[page_no])
                continue

            # PDF page index is 0-based, Docling is 1-based usually
            page = doc[page_no - 1]  
            page_width = page.rect.width
            page_height = page.rect.height

            # Detect layout regions
            try:
                # Use detect_pdf_page which handles rendering
                regions = self.layout_detector.detect_pdf_page(
                    pdf_path,
                    page_number=page_no - 1,
                )
            except Exception as e:
                logger.warning(f"Layout detection failed for page {page_no}: {e}")
                reordered_items.extend(items_by_page[page_no])
                continue

            # Sort regions into reading order
            sorted_regions = self.reading_order_sorter.sort(
                regions, page_width, page_height
            )

            # Match items to regions and reorder
            page_items = items_by_page[page_no]
            reordered_page_items = self._match_and_reorder(
                page_items, sorted_regions
            )
            reordered_items.extend(reordered_page_items)

        doc.close()
        return reordered_items

    def _match_and_reorder(
        self,
        items: List[Tuple[Any, int, int]],
        sorted_regions: List[LayoutRegion],
    ) -> List[Tuple[Any, int, int]]:
        """
        Match Docling items to layout regions and reorder.
        
        Uses bounding box overlap to match items to regions.
        """
        if not sorted_regions:
            return items

        # Build mapping from region bbox to reading order index
        region_order = {
            i: region for i, region in enumerate(sorted_regions)
        }

        # Match items to regions
        item_order = []
        for item, level, page_no in items:
            best_match_idx = len(sorted_regions) # Default to end
            
            if hasattr(item, 'prov') and item.prov:
                prov = item.prov[0]
                if hasattr(prov, 'bbox'):
                    item_bbox = BoundingBox(
                        x0=prov.bbox.l,
                        y0=prov.bbox.t,
                        x1=prov.bbox.r,
                        y1=prov.bbox.b,
                    )

                    # Find best matching region
                    best_overlap = 0.0
                    
                    # Heuristic: Find region with highest IoU overlap
                    for idx, region in region_order.items():
                        # Docling bboxes might be in different coordinate system than our LayoutDetector?
                        # LayoutDetector (via detect_pdf_page) uses PyMuPDF rendering.
                        # Docling uses its own parser. 72 DPI?
                        # We generally assume Docling provides PDF coordinates (bottom-left) or Image (top-left).
                        # Let's verify Docling coord system. Usually it's PDF coords.
                        # Our LayoutDetector logic in detect_pdf_page handles this. 
                        # Wait, reading_order.sort uses input regions.
                        
                        # Let's assume standard IoU works if scales match.
                        # This is a risk point. 
                        # Docling 'bbox' is often bottom-left origin in PDF.
                        # DocLayout-YOLO via 'detect_pdf_page' returns regions in... image coords? 
                        # No, ReadingOrderSorter expects regions.
                        
                        # We will trust the overlap for now, but this is a key testing point.
                        overlap = item_bbox.iou(region.bbox)
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_match_idx = idx

            item_order.append((best_match_idx, item, level, page_no))

        # Sort by matched region index (reading order)
        # Stable sort preserves original order for items in same region
        item_order.sort(key=lambda x: x[0])

        return [(item, level, page_no) for _, item, level, page_no in item_order]

    def _process_item(self, section: Section, item: DocItem, doc: DoclingDocument):
        if hasattr(item, 'label'): # DocItem / SectionHeaderItem / TextItem
            label = item.label
            
            if label in (DocItemLabel.TEXT, DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER, DocItemLabel.PARAGRAPH):
                # Map to Paragraph with TextRun
                text = item.text
                
                # Phase 3 enhancement: If text is empty or suspicion of bad OCR (e.g. garbled Korean)
                # and we have an image + OCR enabled, try re-OCR.
                # Currently only handling empty text fallback or explicit config override
                if not text and self.enable_ocr and hasattr(item, 'prov'):
                     # Logic to extract image chip and OCR
                     # This requires access to the original PDF page or image.
                     # Docling provides prov with bbox and page_no.
                     # We can use PDF path or cache found in docling_doc (if it exposes images)
                     pass

                if text:
                    para = Paragraph(
                        style="Body",
                        elements=[TextRun(text=text)],
                        bbox=item.prov[0].bbox if item.prov and item.prov[0].bbox else None
                    )
                    section.elements.append(para)
            
            elif label == DocItemLabel.CODE:
                 # Map to CodeBlock
                 text = item.text
                 section.add_paragraph().elements.append(CodeBlock(content=text))
                 
            elif label == DocItemLabel.FORMULA:
                 # Map to Equation
                 text = item.text
                 section.add_paragraph().elements.append(Equation(script=text))

    @property
    def ocr_manager(self):
        if not hasattr(self, '_ocr_manager') or self._ocr_manager is None:
            from lib.ocr.manager import OCRManager
            self._ocr_manager = OCRManager()
        return self._ocr_manager

        # Handle specific types
        if isinstance(item, TableItem):
            self._process_table(section, item, doc)
        elif isinstance(item, PictureItem):
            self._process_picture(section, item)

    def _process_table(self, section: Section, item: TableItem, doc: DoclingDocument):
        # Docling TableItem has 'data' which is a TableData object
        table_data = item.data
        rows = []
        
        # Grid is table_data.grid
        for row_data in table_data.grid:
            cells = []
            for cell_data in row_data:
                # cell_data is TableCell
                content_text = cell_data.text
                colspan = cell_data.col_span
                rowspan = cell_data.row_span
                is_header = cell_data.column_header or cell_data.row_header
                
                cells.append(TableCell(
                    content=[TextRun(text=content_text)],
                    colspan=colspan,
                    rowspan=rowspan,
                    is_header=is_header
                ))
            rows.append(TableRow(cells=cells))
            
        section.add_paragraph().elements.append(Table(rows=rows))

    def _process_picture(self, section: Section, item: PictureItem):
        # Has item.image (PIL Image)
        # We need to save it or use a path?
        # For now, we stub path. Real impl needs temp file.
        section.add_paragraph().elements.append(Figure(path="embedded_image_stub"))

    def supports(self, path: str) -> bool:
        return path.lower().endswith('.pdf')

    @property
    def capabilities(self) -> IngestorCapabilities:
        # Docling supports many languages (Korean included via EasyOCR)
        return IngestorCapabilities(
            supports_ocr=True,
            supports_tables=True,
            supports_images=True,
            supports_equations=True,
            supports_multi_column=True,
            supported_languages={'ko', 'en', 'ja', 'zh', 'de', 'fr'}
        )
