from pydantic import BaseModel


class AdminTestData(BaseModel):
    module: str
    description: str


class AdminDashboard(BaseModel):
    user_count: int
    news_count: int
    post_count: int
    pending_count: int
