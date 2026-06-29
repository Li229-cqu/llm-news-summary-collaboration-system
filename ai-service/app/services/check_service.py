from app.common.exceptions import AIServiceException
from app.mock.sample_outputs import CHECK_OUTPUT
from app.schemas.check import CheckRequest, CheckResponse


def check_consistency(request: CheckRequest) -> CheckResponse:
    """返回固定一致性校验 Mock 数据。"""
    if not request.source_text.strip():
        raise AIServiceException(code=400, message="新闻原文不能为空")

    if not request.generated_title.strip():
        raise AIServiceException(code=400, message="生成标题不能为空")

    if not request.generated_summary.strip():
        raise AIServiceException(code=400, message="生成摘要不能为空")

    return CheckResponse(**CHECK_OUTPUT)
