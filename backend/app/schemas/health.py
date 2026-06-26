from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    detail: str
    checks: dict[str, str] = Field(default_factory=dict)
