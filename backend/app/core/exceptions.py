from fastapi import HTTPException


class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def http_exception(detail: str, status_code: int = 400) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)
