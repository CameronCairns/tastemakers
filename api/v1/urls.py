from django.conf.urls import url, include

urlpatterns = [
        url(r'^videos/', include('api.v1.videos.urls')),
        ]
