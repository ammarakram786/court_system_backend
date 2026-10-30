from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, NotFound
from core.exceptions import custom_exception_handler
from core.pagination import StandardResultsSetPagination

class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_endpoint(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['database'], 'healthy')

        api_response = self.client.get('/api/health/')
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.data['status'], 'ok')


class CustomExceptionHandlerTests(TestCase):
    def test_handles_django_validation_error(self):
        exc = DjangoValidationError({'code': ['Code must be unique.']})
        resp = custom_exception_handler(exc, {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['status'], 'error')
        self.assertEqual(resp.data['code'], 400)
        self.assertIn('code', resp.data['detail'])

    def test_handles_protected_error(self):
        from unittest.mock import MagicMock
        exc = ProtectedError("Cannot delete", MagicMock())
        resp = custom_exception_handler(exc, {})
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data['status'], 'error')
        self.assertEqual(resp.data['code'], 409)

    def test_handles_drf_exceptions(self):
        exc = NotFound("Resource not found.")
        resp = custom_exception_handler(exc, {})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data['status'], 'error')
        self.assertEqual(resp.data['code'], 404)


class PaginationTests(TestCase):
    def test_pagination_response_structure(self):
        paginator = StandardResultsSetPagination()
        paginator.page = type('MockPage', (), {
            'number': 1,
            'paginator': type('MockPaginator', (), {'count': 50, 'num_pages': 3})(),
            'has_next': lambda self: False,
            'has_previous': lambda self: False,
        })()
        paginator.request = None
        data = [{'id': 1}, {'id': 2}]
        resp = paginator.get_paginated_response(data)
        self.assertEqual(resp.data['status'], 'success')
        self.assertEqual(resp.data['count'], 50)
        self.assertEqual(resp.data['total_pages'], 3)
        self.assertEqual(resp.data['current_page'], 1)
        self.assertEqual(resp.data['results'], data)

    def test_pagination_schema(self):
        paginator = StandardResultsSetPagination()
        schema = paginator.get_paginated_response_schema({'type': 'array'})
        self.assertIn('status', schema['properties'])
        self.assertIn('total_pages', schema['properties'])
        self.assertIn('current_page', schema['properties'])
