from app.common.exceptions import AIServiceException
from app.mock.sample_outputs import GENERATE_OUTPUT
from app.schemas.generate import GenerateRequest, GenerateResponse


def generate_title_summary(request: GenerateRequest) -> GenerateResponse:
    """返回固定标题摘要 Mock 数据。"""
    if not request.input_text.strip():
        raise AIServiceException(code=400, message="输入文本不能为空")

    if not 1 <= request.title_count <= 5:
        raise AIServiceException(code=400, message="标题数量必须在 1-5 范围内")

    return GenerateResponse(**GENERATE_OUTPUT)
