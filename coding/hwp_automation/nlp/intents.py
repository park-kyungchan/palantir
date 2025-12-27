
import re
from typing import Optional, Dict, Any, List, Type
from lib.models import HwpAction, InsertText, CreateTable, InsertImage, SetFontSize, SetFontBold, SetAlign

class IntentParser:
    """
    Rule-based NLP Engine for HWP Automation.
    Maps Korean regex patterns to HwpAction objects.
    """
    
    def parse(self, prompt: str) -> List[HwpAction]:
        actions = []
        
        # 1. Insert Image
        # Pattern: "이미지 삽입: path" or "사진 넣어: path"
        image_match = re.search(r"(이미지|사진)\s*(삽입|추가|넣어).*?:\s*(.+)", prompt)
        if image_match:
            path = image_match.group(3).strip()
            # Default to 50x50mm if not specified (future: parse size)
            actions.append(InsertImage(path=path, width=50, height=50))
            return actions

        # 2. Create Table
        # Pattern: "5행 3열 표"
        table_match = re.search(r"(\d+)(행|줄)\s*(\d+)(열|칸)", prompt)
        if table_match and ("표" in prompt or "테이블" in prompt):
            rows = int(table_match.group(1))
            cols = int(table_match.group(3))
            actions.append(CreateTable(rows=rows, cols=cols))
            return actions

        # 3. Font Size
        # Pattern: "글자 크기 15" or "폰트 20"
        size_match = re.search(r"(글자|폰트)\s*(크기|사이즈)?\s*(\d+(\.\d+)?)", prompt)
        if size_match:
            size = float(size_match.group(3))
            actions.append(SetFontSize(size=size))
            return actions

        # 4. Bold
        # Pattern: "진하게" or "볼드"
        if "진하게" in prompt or "볼드" in prompt or "굵게" in prompt:
            actions.append(SetFontBold(is_bold=True))
            return actions
            
        # 5. Alignment
        # Pattern: "가운데 정렬", "왼쪽 정렬"
        if "가운데" in prompt and "정렬" in prompt:
            actions.append(SetAlign(align_type="Center"))
            return actions
        elif "오른쪽" in prompt and "정렬" in prompt:
            actions.append(SetAlign(align_type="Right"))
            return actions
        elif "왼쪽" in prompt and "정렬" in prompt:
            actions.append(SetAlign(align_type="Left"))
            return actions

        # Default: Insert Text
        # If no command found, treat as text insertion
        actions.append(InsertText(text=prompt))
        return actions
