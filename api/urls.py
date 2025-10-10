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
     path('google-calendar/init/', views.google_calendar_init, name='google_calendar_init'),
     path('oauth2callback/', views.google_calendar_redirect, name='google_calendar_redirect'),
     path('google-calendar/events/', views.list_events, name='list_events'),
]