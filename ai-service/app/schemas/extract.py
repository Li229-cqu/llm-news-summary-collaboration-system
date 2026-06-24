from pydantic import BaseModel


class ExtractRequest(BaseModel):
    input_text: str


class ExtractResponse(BaseModel):
    keywords: list[str]
    news_elements: dict[str, list[str]]
