
from nlp.intents import IntentParser
from lib.models import HwpAction
from typing import List

class NLPEngine:
    def __init__(self):
        self.parser = IntentParser()
        
    def process_prompt(self, prompt: str) -> List[HwpAction]:
        """
        Main entry point for NLP processing.
        Currently uses the Rule-based IntentParser.
        Future: Can dispatch to LLM if Rule-based fails.
        """
        print(f"[NLP] Processing prompt: '{prompt}'")
        actions = self.parser.parse(prompt)
        for action in actions:
            print(f"[NLP] Identified Intent: {action.action_type}")
        return actions
