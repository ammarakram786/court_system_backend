from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourtViewSet, PoliceStationViewSet, CaseCategoryViewSet,
    CaseViewSet, CasePartyViewSet, CaseProceedingViewSet,
    CauseListViewSet, CauseListItemViewSet
)

router = DefaultRouter()
router.register(r'courts', CourtViewSet, basename='court')
router.register(r'police-stations', PoliceStationViewSet, basename='police-station')
router.register(r'case-categories', CaseCategoryViewSet, basename='case-category')
router.register(r'cases', CaseViewSet, basename='case')
router.register(r'case-parties', CasePartyViewSet, basename='case-party')
router.register(r'case-proceedings', CaseProceedingViewSet, basename='case-proceeding')
router.register(r'cause-lists', CauseListViewSet, basename='cause-list')
router.register(r'cause-list-items', CauseListItemViewSet, basename='cause-list-item')

urlpatterns = [
    path('', include(router.urls)),
]
