from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserViewSet, RoleViewSet, PermissionViewSet,
    PermissionOverrideViewSet, OrganizationViewSet, RankViewSet, AppointmentViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'overrides', PermissionOverrideViewSet, basename='permission-override')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'ranks', RankViewSet, basename='rank')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
