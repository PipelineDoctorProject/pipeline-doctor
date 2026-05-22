from pydantic import BaseModel


class ExplanationSection(BaseModel):
    label: str
    content: str


class InsightExplanationResponse(BaseModel):
    title: str
    summary: str
    sections: list[ExplanationSection]
    provider: str
    model: str
