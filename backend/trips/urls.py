from django.urls import path
from .views import TripRouteView, health

urlpatterns = [
    path("route/", TripRouteView.as_view(), name="trip-route"),
    path("health/", health, name="health"),
]
