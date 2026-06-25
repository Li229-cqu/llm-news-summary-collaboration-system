from pydantic import BaseModel


class TimelineNewsItem(BaseModel):
    id: int
    title: str
    content: str
    source: str
    publish_time: str


class TimelineGenerateRequest(BaseModel):
    topic_id: int
    topic_name: str
    news_items: list[TimelineNewsItem]


class TimelineItem(BaseModel):
    event_id: int
    event_time: str
    event_title: str
    event_summary: str
    source_news_id: int
    source_title: str
    source_name: str


class TimelineGenerateResponse(BaseModel):
    topic_id: int
    topic_name: str
    timeline: list[TimelineItem]
