
from django.urls import path
from rest_framework import routers
from matches import views

router = routers.SimpleRouter()
router.register(r'matches', views.MatchViewSet, basename="match")

urlpatterns = router.urls