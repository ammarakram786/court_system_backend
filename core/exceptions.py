from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
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
