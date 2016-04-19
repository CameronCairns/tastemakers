from django.contrib import admin

from videos.models import Category, Comment, Video, ViewCount, Vote, Tag

# Register your models here.
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Video)
admin.site.register(ViewCount)
admin.site.register(Vote)
admin.site.register(Tag)
