import fitz
import re
from typing import List, Dict, Any
from lib.digital_twin.schema import DigitalTwin, Page, Block, Content, GlobalSettings

class TextBasedActionIngestor:
    """
    Fast ingestor for 'ActionTable_2504.pdf' using PyMuPDF text extraction.
    Leverages the known layout (Tables) to build the Digital Twin.
    """
    def __init__(self, pdf_path: str):
        self.doc = fitz.open(pdf_path)
        self.pdf_path = pdf_path

    def process(self) -> DigitalTwin:
        pages = []
        for i, page in enumerate(self.doc):
            page_num = i + 1
            blocks = self._extract_page_blocks(page, page_num)
            pages.append(Page(page_num=page_num, blocks=blocks))

        return DigitalTwin(
            document_id="ActionTable_2504",
            global_settings=GlobalSettings(),
            pages=pages
        )

    def _extract_page_blocks(self, page: fitz.Page, page_num: int) -> List[Block]:
        blocks = []
        
        # 1. Extract Text
        # We assume the page is largely a table.
        # Structure: Action ID | ParameterSet ID | Description | Note
        # PyMuPDF 'words' or 'text' might be tricky if columns merge.
        # Let's try 'Get Text' blocks and reconstruction logic to form a 'Table Block'.
        
        # For this specific PDF, lines are usually well separated.
        # We will treating the entire page content as a potential 'Table Candidates'
        
        text = page.get_text("text")
        lines = text.split('\n')
        
        # We construct a synthetic "Table Data" from the text lines.
        # Note: This is a heuristics-based approach for the Audit demonstration.
        # Real production would use `page.find_tables()` (PyMuPDF high level).
        
        try:
            tabs = page.find_tables() # Requires PyMuPDF >= 1.23
            if tabs.tables:
                for idx, tab in enumerate(tabs):
                    # headers = tab.header.names
                    data = tab.extract()
                    # data is List[List[str]]
                    
                    # Convert to Block
                    b = Block(
                        id=f"p{page_num}_t{idx}",
                        type="table",
                        role="body",
                        content=Content(table_data=data)
                    )
                    blocks.append(b)
            else:
                # Fallback if find_tables fails or not available
                pass
        except Exception as e:
            # Fallback logic if find_tables crashes
            import logging
            logging.getLogger(__name__).debug("find_tables failed: %s", e)
            
        return blocks

if __name__ == "__main__":
    ingestor = TextBasedActionIngestor("ActionTable_2504.pdf")
    twin = ingestor.process()
    print(f"Ingested {len(twin.pages)} pages.")
    print(f"Page 2 Blocks: {len(twin.pages[1].blocks)}")
    # Verify Table Extraction
    if twin.pages[1].blocks:
         print(twin.pages[1].blocks[0].content.table_data[:3])
