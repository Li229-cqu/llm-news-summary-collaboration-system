from pydantic import BaseModel


class ProfileTestData(BaseModel):
    module: str
    description: str


class ProfileOverview(BaseModel):
    user_id: int
    browse_count: int
    favorite_count: int
    comment_count: int
    ai_generate_count: int
