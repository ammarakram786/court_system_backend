from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, RankViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'ranks', RankViewSet, basename='rank')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
