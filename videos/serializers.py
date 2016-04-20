from rest_framework import serializers

from .models import Tag, Video


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('title',)


class VideoSerializer(serializers.ModelSerializer):
    # tags = TagSerializer(read_only=True, many=True)
    tags = serializers.SlugRelatedField(many=True,
                                        read_only=True,
                                        slug_field='title')

    class Meta:
        model = Video
        fields = ('title', 'uploader', 'description', 'video_id', 'category',
                  'tags', 'created', 'updated')
