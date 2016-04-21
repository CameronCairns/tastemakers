from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from videos.models import Video
from .serializers import VideoSerializer


class VideoListViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    queryset = Video.objects.all().prefetch_related('tags')

    @list_route()
    def liked(self, request):
        most_liked_videos = Video.objects.order_by_votes()[20]
        serializer = self.get_serializer(most_liked_videos, many=True)
        return Response(serializer.data)


class VideoDetailViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    lookup_field = 'id'
    queryset = Video.objects.all()
