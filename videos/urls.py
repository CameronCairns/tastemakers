from django.conf.urls import url

from videos import views

urlpatterns = [
        url(r'^videos/(?P<list_by>[-\w]+)/$',
            views.VideoListView.as_view(),
            name='videos_video_list'),
        url(r'^videos/(?P<video_id>\d+)/comments$',
            views.CommentListView.as_view(),
            name='videos_video_comments')
        ]
