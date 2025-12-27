
import os
import json
import logging
from core_bridge import WSLBridge
from lib.models import (
    Open, InsertText, FileSaveAs, 
    SetFontSize, SetFontBold, SetAlign, 
    SetLineSpacing, SetLetterSpacing
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Reconstructor")

def main():
    bridge = WSLBridge()
    
    # Content extracted from 20251228.hwpx
    title = "교회소식"
    items = [
        "1. 복령교회에 처음 오신 분들을 주님의 이름으로 환영합니다.",
        "2. 예배 10분전 예배실 입장 찬양과 기도로 시작합니다.",
        "3. 모든 성도는 공적인 예배(주일예배, 오후예배, 수요예배) 등을 하나님께 올려드립니다.",
        "4. 말씀배가운동 - 매일 10장 통독 운동 - 카톡에(조별로) 통독 올리기",
        "5. 매주(토)요일 오후 2시 [찾아가는 OK전도] 합니다.",
        "6. 5k 사랑나눔 day 결신자 맡은 대로 중보기도 합니다.(별지참조)",
        "7. 이번 주일(28일 주일예배)는 송영주일로 드립니다.",
        "8. 12월 31일(수)요일은 송구영신예배로 드립니다. [시간: 저녁 9시]",
        "9. [NCMN] 협약교회 정기모임: 2025년 12월 29일(월) 오전 9시 30분 ~ 오후 5시 / 경기도 [NCMN] 비전센터",
        "10. 2026년 카렌다 가져가세요.",
        "11. 다음 주일[2026년 1월 4일 주일] 신년감사주일로 드립니다."
    ]
    
    actions = []
    
    # 1. Header Styling
    actions.append(InsertText(text=title + "\n"))
    actions.append(SetFontSize(size=20.0))
    actions.append(SetFontBold(is_bold=True))
    actions.append(SetAlign(align_type="Center"))
    actions.append(SetLetterSpacing(spacing=-5)) # Tight header
    
    # 2. Reset for Body
    actions.append(InsertText(text="\n"))
    actions.append(SetFontSize(size=11.0))
    actions.append(SetFontBold(is_bold=False))
    actions.append(SetAlign(align_type="Justify")) # Justified text looks better
    actions.append(SetLineSpacing(spacing=160)) # Comfortable reading
    actions.append(SetLetterSpacing(spacing=-3)) # Modern body spacing
    
    # 3. Body Content
    for item in items:
        actions.append(InsertText(text=item + "\n"))
        
    # 4. Save
    output_path = "C:\\Temp\\20251228_reconstructed_enhanced.hwpx"
    actions.append(FileSaveAs(path=output_path, format="HWPX"))
    
    # Payload
    payload_path = os.path.abspath("reconstruct_payload.json")
    payload_data = [action.model_dump() for action in actions]
    
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Payload ready: {payload_path}")
    
    # Execute
    logger.info("--- Executing Reconstruction ---")
    script_path = os.path.abspath("executor_win.py")
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        logger.info(f"Success! Output at: {output_path}")
    else:
        logger.error(f"Failed with code {return_code}")

if __name__ == "__main__":
    main()
