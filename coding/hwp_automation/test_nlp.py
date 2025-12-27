
import os
import json
import logging
from nlp.processor import NLPEngine
from core_bridge import WSLBridge

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NLPVerifier")

def main():
    # 1. Initialize Engines
    nlp_engine = NLPEngine()
    bridge = WSLBridge()
    
    # 2. Define Test Prompts (Korean)
    prompts = [
        "텍스트를 입력합니다. 이것은 NLP 테스트입니다.",
        "글자 크기 20.0",
        "진하게 설정해줘",
        "가운데 정렬",
        "이미지 삽입: C:\\Temp\\test_image.png", # Using Windows path directly for simplicity in this test
        "3행 3열 표 만들어"
    ]
    
    # 3. Process Prompts -> Actions -> Payload
    all_actions = []
    logger.info("--- Phase 1: NLP Processing ---")
    for prompt in prompts:
        actions = nlp_engine.process_prompt(prompt)
        all_actions.extend(actions)
        
    # 4. Serialize
    payload_path = os.path.abspath("nlp_action_request.json")
    payload_data = [action.model_dump() for action in all_actions]
    
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated Payload: {payload_path}")

    # 5. Execute
    logger.info("--- Phase 2: Remote Execution ---")
    script_path = os.path.abspath("executor_win.py")
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        logger.info("Verification SUCCESS!")
    else:
        logger.error(f"Verification FAILED with code {return_code}")

if __name__ == "__main__":
    main()
