import re
from typing import List, Optional
from lib.ir import Document, Section, Paragraph, TextRun, Equation, Image

# Alias for compatibility if needed, or update usage below
IRTextRun = TextRun
IREquation = Equation
IRImage = Image

class MarkdownParser:
    """
    Parses Mathpix Markdown (MMD) into the internal IR Document model.
    Handles headings, bold text, inline/display math, and basic structure.
    Also applies semantic tagging logic (AnswerBox/ProblemBox) based on text patterns.
    """
    
    # Regex Patterns
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.*)')
    MATH_DISPLAY_PATTERN = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    MATH_INLINE_PATTERN = re.compile(r'\$(.*?)\$') # Basic inline match
    IMAGE_PATTERN = re.compile(r'!\[(.*?)\]\((.*?)\)')
    BOLD_PATTERN = re.compile(r'\*\*(.*?)\*\*')
    
    # Semantic Patterns (migrated from SemanticTagger)
    PROBLEM_PATTERN = re.compile(r"^\s*(\d+\s*\.|\(?\d+\)?)\s*") # e.g., "7.", "(1)"
    ANSWER_PATTERN = re.compile(r"^\s*(정답|답)\s*")

    def parse(self, markdown_text: str) -> Document:
        doc = Document(sections=[])
        current_section = Section(paragraphs=[])
        doc.sections.append(current_section)
        
        lines = markdown_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 1. Check Heading (New Section?)
            # For HWPX, we might treat headings just as Styled Paragraphs for now
            # unless we really want logical sections. 
            # Let's verify if 'Section' object in IR implies 'Page Break' or 'Logical Group'.
            # Usually HWP Sections are page setup boundaries.
            # So maybe we just map Headings to "Header" styled paragraphs.
            
            heading_match = self.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                # Create a Header Paragraph
                para = self._create_paragraph(text, style="Header")
                current_section.paragraphs.append(para)
                continue
                
            # 2. Regular Paragraph (Problem or Answer or Normal)
            style = "Normal"
            if self.PROBLEM_PATTERN.match(line):
                style = "ProblemBox"
            elif self.ANSWER_PATTERN.match(line):
                style = "AnswerBox"
                
            para = self._create_paragraph(line, style=style)
            current_section.paragraphs.append(para)
            
        return doc

    def _create_paragraph(self, text: str, style: str) -> Paragraph:
        para = Paragraph(style=style)
        para.elements = self._parse_inline_elements(text)
        return para

    def _parse_inline_elements(self, text: str) -> List[any]:
        elements = []
        
        # Naive tokenization: We need to handle overlapping patterns priority.
        # Priority: Image > DisplayMath > InlineMath > Bold > Text
        # Since this is a simple parser, let's process sequentially or split by regex.
        
        # Let's try a simple split approach for Math first (most distinctive).
        # We will split text by $$ then $. 
        # This is non-trivial for nested structures but Mathpix MMD is usually clean.
        
        # 1. Split by Display Math
        parts = self.MATH_DISPLAY_PATTERN.split(text)
        # parts[0] = text, parts[1] = match, parts[2] = text ...
        
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This is the Math Content
                elements.append(IREquation(script=part.strip()))
            else:
                # This is "Text" (which might contain inline math or bold)
                if part:
                    self._parse_inline_math(part, elements)
                    
        return elements

    def _parse_inline_math(self, text: str, elements: List[any]):
        parts = self.MATH_INLINE_PATTERN.split(text)
        for i, part in enumerate(parts):
            if i % 2 == 1:
                elements.append(IREquation(script=part.strip()))
            else:
                if part:
                    self._parse_bold(part, elements)

    def _parse_bold(self, text: str, elements: List[any]):
        parts = self.BOLD_PATTERN.split(text)
        for i, part in enumerate(parts):
            if i % 2 == 1:
                elements.append(IRTextRun(text=part, is_bold=True))
            else:
                if part:
                    elements.append(IRTextRun(text=part))

