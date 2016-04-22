from django.views.generic import ListView

from .models import Video


class VideoListView(ListView):
    model = Video
    paginate_by = 10
    template_name = 'videos/video-list.html'

    QUERY_DICT = dict(likes=Video.objects.order_by_votes,
                      views=Video.objects.order_by_views,
                      submission='created',
                      publication='published')

    def get_queryset(self):
        """
        Override queryset to allow querying and filtering by custom manager
        methods and queries
        """
        query = self.QUERY_DICT.get(self.kwargs['list_by'],
                                    self.QUERY_DICT['likes'])
        if callable(query):
            return query()
        else:
            return Video.objects.order_by(query)
