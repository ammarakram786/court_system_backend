import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    # Handle Django model ValidationErrors cleanly as HTTP 400 Bad Request
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            detail = exc.message_dict
        elif hasattr(exc, 'messages'):
            detail = exc.messages
        else:
            detail = str(exc)
        return Response(
            {
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'detail': detail
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle protected foreign key deletions as HTTP 409 Conflict
    if isinstance(exc, ProtectedError):
        msg = "Cannot delete this record because other records depend on it."
        try:
            if exc.protected_objects:
                sample_obj = next(iter(exc.protected_objects))
                model_name = getattr(sample_obj._meta, 'verbose_name_plural', 'records')
                msg = f"Cannot delete this record because dependent {model_name} exist."
        except (StopIteration, AttributeError):
            pass
        return Response(
            {
                'status': 'error',
                'code': status.HTTP_409_CONFLICT,
                'detail': msg
            },
            status=status.HTTP_409_CONFLICT
        )

    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            'status': 'error',
            'code': response.status_code,
            'detail': response.data
        }
        response.data = custom_data
    else:
        logger.exception(f"Unhandled exception: {exc}")
        response = Response(
            {
                'status': 'error',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'detail': 'An unexpected internal server error occurred.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
