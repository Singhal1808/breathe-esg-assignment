from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActivityRecordViewSet, BatchViewSet, SourceSystemViewSet, TenantViewSet, summary, upload

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")
router.register("sources", SourceSystemViewSet, basename="source")
router.register("batches", BatchViewSet, basename="batch")
router.register("activities", ActivityRecordViewSet, basename="activity")

urlpatterns = [
    path("", include(router.urls)),
    path("summary/", summary),
    path("upload/", upload),
]

