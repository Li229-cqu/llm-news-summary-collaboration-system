from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


def success_response(
    data: Optional[T] = None,
    message: str = "success",
    code: int = 200,
) -> ApiResponse[T]:
    return ApiResponse(code=code, message=message, data=data)


def error_response(
    message: str = "error",
    code: int = 400,
    data: Optional[T] = None,
) -> ApiResponse[T]:
    return ApiResponse(code=code, message=message, data=data)
