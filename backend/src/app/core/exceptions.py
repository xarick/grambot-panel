class AppError(Exception):
    status_code: int = 400

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ForbiddenError(AppError):
    status_code = 403


class UnauthorizedError(AppError):
    status_code = 401


class ValidationError(AppError):
    status_code = 422
