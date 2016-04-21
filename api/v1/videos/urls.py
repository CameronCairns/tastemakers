from django.conf.urls import url, include

from rest_framework import routers

from api.v1.videos import viewsets

router = routers.DefaultRouter()
router.register(r'videos', viewsets.VideoListViewSet)

urlpatterns = [
         url(r'^', include(router.urls))
         ]
