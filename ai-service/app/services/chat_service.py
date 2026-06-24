from app.common.exceptions import AIServiceException
from app.mock.sample_outputs import CHAT_OUTPUT
from app.schemas.chat import ChatRequest, ChatResponse


def chat(request: ChatRequest) -> ChatResponse:
    """返回固定新闻助手 Mock 数据。"""
    if not request.question.strip():
        raise AIServiceException(code=400, message="问题不能为空")

    return ChatResponse(**CHAT_OUTPUT)
