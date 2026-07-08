from __future__ import annotations
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ProfileTestData(BaseModel):
    module: str
    description: str


class ProfileOverview(BaseModel):
    user_id: int
    browse_count: int
    favorite_count: int
    comment_count: int
    ai_generate_count: int


class BrowseHistoryItem(BaseModel):
    news_id: int
    title: str
    category_name: str
    browse_time: str
    # 通用字段，支持新闻浏览和帖子浏览
    type: str = "news"
    target_id: Optional[int] = None
    target_title: Optional[str] = ""


class FavoriteItem(BaseModel):
    news_id: int
    target_id: Optional[int] = None
    title: str
    summary: str
    category_name: str
    source: str
    publish_time: str
    favorited_at: Optional[str] = None
    target_type: Optional[str] = "news"


class CommentRecordItem(BaseModel):
    comment_id: int
    news_id: int
    news_title: str
    category_name: str
    content: str
    like_count: int
    status: int
    create_time: str
    # 通用字段，支持新闻评论和帖子评论
    type: str = "news"
    target_id: Optional[int] = None
    target_title: Optional[str] = ""


class AIRecordItem(BaseModel):
    id: int
    source: str
    source_news_id: Optional[Union[int, str]] = None
    source_title: str
    input_text: str
    candidate_titles: List[str]
    summary_short: str
    summary_long: Optional[str] = None
    risk_level: str = "low"
    create_time: Optional[str] = None


class SubscriptionCategory(BaseModel):
    id: int
    name: str
    code: str
    subscribed: bool = False


class SubscriptionResponse(BaseModel):
    subscribed_category_ids: List[int]
    categories: List[SubscriptionCategory]


class SubscriptionUpdateRequest(BaseModel):
    category_ids: List[int]


class PaginationResponse(BaseModel):
    list: List[dict]
    total: int
    page: int
    page_size: int


class ReadingTrajectorySummary(BaseModel):
    total_reads: int = 0
    unique_news_count: int = 0
    category_count: int = 0
    topic_count: int = 0
    top_category: str = ""
    top_topic: str = ""
    date_range: str = ""


class ReadingTrajectoryNode(BaseModel):
    id: str
    name: str = ""
    type: str = ""
    value: int = 0
    read_count: int = 0
    news_id: Optional[int] = None
    category_id: Optional[int] = None
    topic_id: Optional[int] = None
    category_name: str = ""
    topic_name: str = ""
    browse_time: str = ""


class ReadingTrajectoryEdge(BaseModel):
    source: str
    target: str
    value: int = 1
    type: str = ""


class ReadingTopCategory(BaseModel):
    category_id: Optional[int] = None
    category_name: str = ""
    read_count: int = 0


class ReadingTopTopic(BaseModel):
    topic_id: Optional[int] = None
    topic_name: str = ""
    read_count: int = 0


class ReadingRecentNews(BaseModel):
    news_id: Optional[int] = None
    title: str = ""
    category_name: str = ""
    topic_name: str = ""
    browse_time: str = ""


class ReadingTrajectoryResponse(BaseModel):
    summary: ReadingTrajectorySummary
    nodes: List[ReadingTrajectoryNode] = Field(default_factory=list)
    edges: List[ReadingTrajectoryEdge] = Field(default_factory=list)
    top_categories: List[ReadingTopCategory] = Field(default_factory=list)
    top_topics: List[ReadingTopTopic] = Field(default_factory=list)
    recent_news: List[ReadingRecentNews] = Field(default_factory=list)


class ReadingTimelineSummary(BaseModel):
    total_days: int = 0
    total_reads: int = 0
    most_active_date: str = ""
    most_active_category: str = ""


class ReadingTimelineCategoryItem(BaseModel):
    category_id: Optional[int] = None
    category_name: str = ""
    read_count: int = 0


class ReadingTimelineTopicItem(BaseModel):
    topic_id: Optional[int] = None
    topic_name: str = ""
    read_count: int = 0


class ReadingTimelineNewsItem(BaseModel):
    news_id: Optional[int] = None
    title: str = ""
    category_name: str = ""
    topic_name: str = ""
    browse_time: str = ""


class ReadingTimelineDateItem(BaseModel):
    date: str = ""
    total_reads: int = 0
    categories: List[ReadingTimelineCategoryItem] = Field(default_factory=list)
    topics: List[ReadingTimelineTopicItem] = Field(default_factory=list)
    news: List[ReadingTimelineNewsItem] = Field(default_factory=list)


class ReadingTimelineResponse(BaseModel):
    summary: ReadingTimelineSummary
    items: List[ReadingTimelineDateItem] = Field(default_factory=list)


class ReadingHeatmapCell(BaseModel):
    x: str = ""
    y: str = ""
    value: int = 0
    news_count: int = 0


class ReadingHeatmapSummary(BaseModel):
    max_value: int = 0
    most_active_category: str = ""
    most_active_date: str = ""


class ReadingHeatmapResponse(BaseModel):
    x_axis: List[str] = Field(default_factory=list)
    y_axis: List[str] = Field(default_factory=list)
    cells: List[ReadingHeatmapCell] = Field(default_factory=list)
    summary: ReadingHeatmapSummary


# ===== 近 7 天阅读报告 =====

class WeeklyReportRange(BaseModel):
    days: int = 7
    start_date: str = ""
    end_date: str = ""


class WeeklyReportPersona(BaseModel):
    title: str = ""
    description: str = ""


class WeeklyReportOverview(BaseModel):
    browse_count: int = 0
    favorite_count: int = 0
    comment_count: int = 0
    ai_count: int = 0
    active_days: int = 0


class WeeklyReportScores(BaseModel):
    reading: int = 0
    collecting: int = 0
    interaction: int = 0
    ai_usage: int = 0


class DailyActivityItem(BaseModel):
    date: str = ""
    count: int = 0


class TopicRankItem(BaseModel):
    name: str = ""
    count: int = 0
    percent: int = 0


class WeeklyReportHighlight(BaseModel):
    label: str = ""
    value: str = ""
    desc: str = ""


class WeeklyReportHighlight(BaseModel):
    label: str = ""
    value: str = ""
    desc: str = ""
    icon: str = ""
    narrative: str = ""


class AnalysisTexts(BaseModel):
    profile_analysis: str = ""
    behavior_analysis: str = ""
    activity_analysis: str = ""
    topic_analysis: str = ""


class PageAnalyses(BaseModel):
    overview: str = ""
    trajectory: str = ""
    conclusion: str = ""


class AiAnalysisResult(BaseModel):
    enabled: bool = False
    source: str = "fallback"
    summary: str = ""
    insights: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    page_analyses: PageAnalyses = Field(default_factory=PageAnalyses)
    reading_style: str = ""
    closing: str = ""
    quality_score: float = 0.0


class WeeklyReportResponse(BaseModel):
    range: WeeklyReportRange = Field(default_factory=WeeklyReportRange)
    persona: WeeklyReportPersona = Field(default_factory=WeeklyReportPersona)
    summary: str = ""
    overview: WeeklyReportOverview = Field(default_factory=WeeklyReportOverview)
    behavior_scores: WeeklyReportScores = Field(default_factory=WeeklyReportScores)
    daily_activity: List[DailyActivityItem] = Field(default_factory=list)
    topic_rank: List[TopicRankItem] = Field(default_factory=list)
    highlights: List[WeeklyReportHighlight] = Field(default_factory=list)
    ai_analysis: AiAnalysisResult = Field(default_factory=AiAnalysisResult)
    analysis_texts: AnalysisTexts = Field(default_factory=AnalysisTexts)
    empty: bool = True
