from django.contrib import admin

from videos.models import Video, ViewCount

# Register your models here.
admin.site.register(Video)
admin.site.register(ViewCount)
