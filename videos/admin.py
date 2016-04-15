from django.contrib import admin

from videos.models import Category, Video, ViewCount

# Register your models here.
admin.site.register(Category)
admin.site.register(Video)
admin.site.register(ViewCount)
