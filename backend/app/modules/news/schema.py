from typing import Optional

from pydantic import BaseModel


class NewsTestData(BaseModel):
    module: str
    description: str


class NewsItem(BaseModel):
    id: int
    title: str
    summary: str


class NewsDetail(NewsItem):
    content: Optional[str] = None
