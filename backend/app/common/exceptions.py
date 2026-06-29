from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.response import error_response


class AppException(Exception):
    """项目统一业务异常。"""

    def __init__(self, code: int = 400, message: str = "请求处理失败") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.code,
            content=error_response(message=exc.message, code=exc.code).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_response(message="服务器内部错误", code=500).model_dump(),
        )
