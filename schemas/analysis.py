from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
    period: str = Field(default='daily')
    count: int = Field(default=60, ge=20, le=250)
