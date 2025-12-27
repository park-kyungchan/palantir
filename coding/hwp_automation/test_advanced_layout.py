
import os
import json
import logging
from core_bridge import WSLBridge
from lib.models import Open, MultiColumn, InsertText, MoveToField, FileSaveAs

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdvancedVerifier")

def main():
    bridge = WSLBridge()
    
    # 시나리오:
    # 1. 새 문서 시작 (기본)
    # 2. 다단 설정 (2단) -> PDF 재구성 기능 검증
    # 3. 텍스트 입력
    # 4. 저장 (temp.hwpx)
    # 5. 저장된 파일 열기 -> 기존 파일 수정 기능 검증
    # 6. 필드 이동 시도 (필드가 없으므로 실패 로그 확인, 기능 동작 여부만 체크)
    
    actions = [
        # 1. 문서 포맷팅 (다단)
        MultiColumn(count=2, same_size=True, gap=3000),
        InsertText(text="이 텍스트는 1단에 위치합니다.\n"),
        # 2. 저장
        FileSaveAs(path="C:\\Temp\\advanced_test.hwpx", format="HWPX"),
        # 3. 닫기/새로 열기 시뮬레이션을 위해 Open 호출 (실제로는 현재 창에서 열림)
        Open(path="C:\\Temp\\advanced_test.hwpx", format="HWPX"),
        # 4. 필드 테스트 (실패하더라도 코드 경로 진입 확인)
        MoveToField(field="non_existent_field", text="Updated Content")
    ]
    
    # 페이로드 생성
    payload_path = os.path.abspath("advanced_action_request.json")
    payload_data = [action.model_dump() for action in actions]
    
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Payload generated: {payload_path}")

    # 실행
    logger.info("--- Remote Execution ---")
    script_path = os.path.abspath("executor_win.py")
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        logger.info("Verification SUCCESS!")
    else:
        logger.error(f"Verification FAILED with code {return_code}")

if __name__ == "__main__":
    main()
