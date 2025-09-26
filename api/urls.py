from django.urls import include
from django.urls import path
from rest_framework import routers
from api.views import EmployeeViewSet, ShiftViewSet, SwapRequestViewSet, ShiftSelectionViewSet

router = routers.DefaultRouter()

router.register('employees', EmployeeViewSet)
router.register('shifts', ShiftViewSet)
router.register('swap-requests', SwapRequestViewSet)
router.register('user-shifts-requests', ShiftSelectionViewSet)

urlpatterns = [
     path('', include(router.urls))
]