"""近 7 天阅读报告 AI 分析的请求和响应 schema。"""

from pydantic import BaseModel, Field


class ProfileReportRequest(BaseModel):
    """发给 AI 服务的结构化报告数据（已聚合，不含原始文本）。"""

    task_type: str = "profile_weekly_report"
    range_days: int = 7
    overview: dict = Field(default_factory=dict)
    behavior_scores: dict = Field(default_factory=dict)
    persona_title: str = ""
    daily_summary: dict = Field(default_factory=dict)
    top_topics: list[dict] = Field(default_factory=list)
    highlights: list[dict] = Field(default_factory=list)


class ProfileReportQuality(BaseModel):
    passed: bool = True
    score: float = 1.0
    issues: list[str] = Field(default_factory=list)


class PageAnalyses(BaseModel):
    overview: str = ""
    trajectory: str = ""
    conclusion: str = ""


class ProfileReportResponse(BaseModel):
    ai_summary: str = ""
    ai_insights: list[str] = Field(default_factory=list)
    ai_suggestions: list[str] = Field(default_factory=list)
    persona_description: str = ""
    page_analyses: PageAnalyses = Field(default_factory=PageAnalyses)
    reading_style: str = ""
    closing: str = ""
    quality: ProfileReportQuality = Field(default_factory=ProfileReportQuality)
    source: str = "mock"
