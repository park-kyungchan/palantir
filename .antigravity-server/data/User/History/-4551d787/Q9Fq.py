import subprocess
import re
from typing import List, Tuple
from lib.knowledge.schema import APIMethodDefinition, APIPropertyDefinition

class APIIngestor:
    """
    Parses 'HwpAutomation_2504.pdf' to extract API Methods and Properties.
    Pattern: 'Name(Method)' and 'Name(Property)'
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def process(self) -> Tuple[List[APIMethodDefinition], List[APIPropertyDefinition]]:
        cmd = ["pdftotext", "-layout", self.pdf_path, "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        full_text = result.stdout
        
        methods = []
        properties = []
        
        lines = full_text.split('\n')
        
        # Regex Patterns
        # Line usually starts with whitespace then Name(Type)
        method_pattern = re.compile(r"^\s*(\w+)\(Method\)(.*)")
        prop_pattern = re.compile(r"^\s*(\w+)\(Property\)(.*)")
        
        for line in lines:
            line = line.replace('\f', '') # Remove form feed
            
            # Check Method
            m_match = method_pattern.match(line)
            if m_match:
                name = m_match.group(1).strip()
                desc = m_match.group(2).strip()
                methods.append(APIMethodDefinition(name=name, description=desc))
                continue
                
            # Check Property
            p_match = prop_pattern.match(line)
            if p_match:
                name = p_match.group(1).strip()
                desc = p_match.group(2).strip()
                properties.append(APIPropertyDefinition(name=name, description=desc))
                continue
                
        return methods, properties

if __name__ == "__main__":
    ingestor = APIIngestor("HwpAutomation_2504.pdf")
    m, p = ingestor.process()
    print(f"Extracted {len(m)} Methods and {len(p)} Properties.")
    if m:
        print(f"Sample Method: {m[0].name} - {m[0].description}")
    if p:
        print(f"Sample Property: {p[0].name} - {p[0].description}")
