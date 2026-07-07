from rest_framework import status
from rest_framework.views import exception_handler


def _normalize_error_detail(detail):
    if isinstance(detail, list):
        return [_normalize_error_detail(item) for item in detail]
    if isinstance(detail, dict):
        return {key: _normalize_error_detail(value) for key, value in detail.items()}
    return str(detail)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    errors = _normalize_error_detail(response.data)
    message = "Request failed."
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        message = "Authentication credentials were not provided or are invalid."
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        message = "You do not have permission to perform this action."
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        message = "Resource not found."
    elif response.status_code == status.HTTP_400_BAD_REQUEST:
        message = "Validation failed."
    elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        message = "Request was throttled."

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
