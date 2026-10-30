from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiTypes

@extend_schema(
    summary="Health check endpoint",
    description="Production health check verifying database connectivity and service status.",
    responses={
        200: OpenApiTypes.OBJECT,
        503: OpenApiTypes.OBJECT
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Production health check endpoint verifying database connectivity and system status.
    """
    db_status = 'healthy'
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'

    is_healthy = db_status == 'healthy'
    return Response(
        {
            'status': 'ok' if is_healthy else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'database': db_status,
            'version': '1.0.0',
        },
        status=200 if is_healthy else 503
    )
