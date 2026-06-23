from app.common.exceptions import AIServiceException
from app.mock.sample_outputs import EXTRACT_OUTPUT
from app.schemas.extract import ExtractRequest, ExtractResponse


def extract_elements(request: ExtractRequest) -> ExtractResponse:
    """返回固定要素抽取 Mock 数据。"""
    if not request.input_text.strip():
        raise AIServiceException(code=400, message="输入文本不能为空")

    return ExtractResponse(**EXTRACT_OUTPUT)
