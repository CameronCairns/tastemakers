from django.db import models
from django.utils.translation import ugettext_lazy as _

import dateutil.parser

from videos.mixins import VideoAPIMixin

class VideoManager(models.Manager, VideoAPIMixin):
    """
    Custom manager needed to couple the gathering of data needed to create
    an object with its api calls and logic
    """
    def create_video(self, video_id):
        # Define the fields to receive from the API
        fields =('items/snippet('
                 'publishedAt, categoryId, tags, title, description)')
        # Define the parameters to supply to the API
        parameters = dict(part='snippet',
                          id=video_id,
                          fields=fields)
        # Get JSON from API response
        JSON = self._get_info_from_api('videos', parameters)
        # Information needed is located at the snippet key
        snippet = JSON['items'][0]['snippet']
        published_datetime = dateutil.parser.parse(snippet['publishedAt'])
        # Now create the object with the gathered information and return it
        return self.create(description=snippet['description'],
                           published=published_datetime,
                           title=snippet['title'],
                           video_id=video_id)

class Video(models.Model):
    # Attributes
    created = models.DateTimeField(_('Creation date'), auto_now_add=True)
    description = models.TextField(_('Video description'),
                                   max_length=5000,
                                   blank=True)
    published = models.DateTimeField(_('Video publication date'))
    title = models.CharField(_('Video title'), max_length=100)
    updated = models.DateTimeField(_('Last updated'), auto_now=True)
    video_id = models.CharField(_('Youtube ID for video'), max_length=500)

    # Relationships
    # category = models.ForeignKey(_('Video category'), Category)
    # uploader = models.ForeignKey(_('Video uploader'), User)

    # Many to Many Relationships
    # tags = models.ManyToManyField(_('Video tags'), Tag, blank=True)

    # Manager
    objects = VideoManager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Find the view count for the video once it has been successfully
        # created
        if self.id is None:
            # Object has not been created yet 
            super(Video, self).save(*args, **kwargs)
            self.update_view_count()
        else:
            # Object is just being updated
            super(Video, self).save(*args, **kwargs)

    def update_view_count(self):
        ViewCount.objects.create_viewcount(self)

class ViewCountManager(models.Manager, VideoAPIMixin):
    """
    Custom manager needed to couple the gathering of data needed to create
    an object with its api calls and logic
    """
    def create_viewcount(self, video):
        # Define the parameters to supply to the API
        parameters = dict(part='statistics',
                          id=video.video_id,
                          fields='items/statistics/viewCount')
        # Get JSON from API response
        JSON = self._get_info_from_api('videos', parameters)
        # Now create the object with the gathered information and return it
        return self.create(views=JSON['items'][0]['statistics']['viewCount'],
                           video=video)

class ViewCount(models.Model):
    # Attributes
    count_datetime = models.DateTimeField(
        _('Date and time video views were counted'),
        auto_now_add=True)
    views = models.BigIntegerField(_('Video view count'))

    #Relationships
    video = models.ForeignKey(Video,
                              on_delete=models.CASCADE,
                              verbose_name=_('Video views are counted for'))

    # Manager
    objects = ViewCountManager()

    def __str__(self):
        return str(self.count_datetime) + ': ' + str(self.views)
