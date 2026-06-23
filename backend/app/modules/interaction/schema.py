from pydantic import BaseModel


class InteractionTestData(BaseModel):
    module: str
    description: str


class InteractionResult(BaseModel):
    target_id: int
    target_type: str
    status: bool
