from typing import Literal

from pydantic import BaseModel


class CheckRequest(BaseModel):
    source_text: str
    generated_title: str
    generated_summary: str


class CheckItem(BaseModel):
    name: str
    status: Literal["pass", "warning", "fail"]
    message: str


class CheckResponse(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    risk_label: Literal["低风险", "中风险", "高风险"]
    check_items: list[CheckItem]
    suggestions: list[str]
