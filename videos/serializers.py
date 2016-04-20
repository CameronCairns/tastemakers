from rest_framework import serializers

from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('title', 'uploader', 'description', 'video_id', 'category',
                  'tags', 'created', 'updated')
