from django.conf.urls import url

from videos import viewsets

urlpatterns = [
        url(regex=r'^api/$',
            view=viewsets.VideoListView.as_view(),
            name='videos_rest_api'),
        url(regex=r'^api/(?P<id>[-\w]+)$',
            view=viewsets.VideoDetailView.as_view(),
            name='videos_rest_api')
        ]
