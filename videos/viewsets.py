from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Video
from .serializers import VideoSerializer


class VideoListView(ListAPIView):
    serializer_class = VideoSerializer
    lookup_field = 'id'
    queryset = Video.objects.all().prefetch_related('tags')


class VideoDetailView(RetrieveAPIView):
    serializer_class = VideoSerializer
    lookup_field = 'id'
    queryset = Video.objects.all()
