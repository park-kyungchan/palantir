import time
from app.domain.models.analysis import NumberAnalysis
from app.domain.services.math_service import MathService

class AnalyzeNumberUseCase:
    def __init__(self, math_service: MathService):
        self.math_service = math_service

    def execute(self, number: int) -> NumberAnalysis:
        start_time = time.time()
        
        is_prime = self.math_service.is_prime_number(number)
        factors = self.math_service.get_prime_factors(number)
        
        # Note: execution_time is technically metadata, but we can return it if needed.
        # For pure domain model, we might exclude it, but let's keep it simple for now.
        
        return NumberAnalysis(
            number=number,
            is_prime=is_prime,
            factors=factors
        )
