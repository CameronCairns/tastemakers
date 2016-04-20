from django.contrib import admin

from videos.models import (Category, Comment, CommentVote, Video, VideoVote,
                           ViewCount, Tag)

# Register your models here.
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(CommentVote)
admin.site.register(Video)
admin.site.register(VideoVote)
admin.site.register(ViewCount)
admin.site.register(Tag)
