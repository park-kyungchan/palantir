from fastapi import APIRouter, Path, HTTPException, Depends
from app.domain.models.analysis import NumberAnalysis
from app.application.use_cases.analyze_number import AnalyzeNumberUseCase
from app.domain.services.math_service import MathService

router = APIRouter()

def get_math_service() -> MathService:
    return MathService()

def get_analyze_use_case(service: MathService = Depends(get_math_service)) -> AnalyzeNumberUseCase:
    return AnalyzeNumberUseCase(service)

@router.get("/analyze/{number}", response_model=NumberAnalysis)
async def analyze_number(
    number: int = Path(..., title="The number to analyze", ge=1, le=1000000),
    use_case: AnalyzeNumberUseCase = Depends(get_analyze_use_case)
) -> NumberAnalysis:
    """
    Analyze a number to determine if it's prime and find its prime factors.
    """
    if number > 1000000:
        raise HTTPException(status_code=400, detail="Number too large")
        
    try:
        result = use_case.execute(number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
