from django.views.generic import ListView

from .models import Comment, Video


class VideoListView(ListView):
    model = Video
    paginate_by = 10
    template_name = 'videos/video-list.html'

    QUERY_DICT = dict(likes=Video.objects.order_by_votes,
                      views=Video.objects.order_by_views,
                      submission='created',
                      publication='published')

    TITLE_DICT = dict(likes='Most Liked Videos',
                      views='Most Viewed Vidoes',
                      submission='Most Recent User Submissions',
                      publication='Most Recently Published Videos')

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

    def get_context_data(self, **kwargs):
        context = super(VideoListView, self).get_context_data(**kwargs)
        first_video_index = context['page_obj'].start_index()
        video_indices = [first_video_index + current_index
                         for current_index
                         in range(0, len(context['object_list']))]
        context['object_list'] = list(zip(video_indices,
                                          context['object_list']))
        context['title'] = self.TITLE_DICT.get(self.kwargs['list_by'],
                                               self.TITLE_DICT['likes'])
        return context


class CommentListView(ListView):
    model = Video
    template_name = 'videos/video-comments.html'

    def get_queryset(self):
        """
        Override base queryset method to allow for querying by the video id
        the comments are related to and structuring the data to allow for
        child parent representation
        """
        parents = Comment.objects.order_by_votes().filter(
                video_id=self.kwargs['video_id'], parent_id=None)
        return parents

    def get_context_data(self, **kwargs):
        context = super(CommentListView, self).get_context_data(**kwargs)
        context['video'] = Video.objects.get(id=self.kwargs['video_id'])
        return context
