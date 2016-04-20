from django.conf.urls import url

from videos import views

urlpatterns = [
        url(regex=r'^api/$',
            view=views.VideoListView.as_view(),
            name='videos_rest_api'),
        url(regex=r'^api/(?P<id>[-\w]+)$',
            view=views.VideoDetailView.as_view(),
            name='videos_rest_api')
        ]
