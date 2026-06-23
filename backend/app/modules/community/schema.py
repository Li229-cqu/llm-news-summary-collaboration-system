from pydantic import BaseModel


class CommunityTestData(BaseModel):
    module: str
    description: str


class CommunityPost(BaseModel):
    id: int
    title: str
    content: str
    author: str
