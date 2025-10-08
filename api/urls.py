from django.urls import include
from django.urls import path
from rest_framework import routers

from api import views
from api.views import EmployeeViewSet, ShiftViewSet, SwapRequestViewSet, ShiftSelectionViewSet

router = routers.DefaultRouter()

router.register('employees', EmployeeViewSet)
router.register('shifts', ShiftViewSet)
router.register('swap-requests', SwapRequestViewSet)
router.register('user-shifts-requests', ShiftSelectionViewSet)

urlpatterns = [
     path('', include(router.urls)),
     path('auth/google/connect/', views.google_calendar_init, name='google_connect'),
     path('auth/google/callback/', views.google_callback, name='google_callback'),
]