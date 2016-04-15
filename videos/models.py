from django.db import models
from django.utils.translation import ugettext_lazy as _

import dateutil.parser
import requests

from users import User
class APIBasedModel(models.Model):
    # Constants
    API_URL = 'https://www.googleapis.com/youtube/v3/videos'
    with open('API_Key.txt', 'r') as f:
        API_KEY = f.read()

    @class_method
    def get_info_from_api(cls, params):
        response = requests.get(cls.API_URL,
                                params={**{key: cls.API_KEY}, **params})
        return response.json()['items'][0]

    # Protected Methods
    _get_from_api = get_from_api

class Video(APIBasedModel):
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

    # Methods
    def __init__(self, video_id):
        fields =('items/snippet('
                 'publishedAt, categoryId, tags, title, description)')
        parameters = dict(part='snippet',
                          id=video_id,
                          fields=fields)
        data = self._get_info_from_api(parameters)['snippet']
        self.description = data['description']
        self.published = dateutil.parser.parse(data['publishedAt'])
        self.title = data['title']
        self.video_id = video_id

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
            super(Video, self).save(*args, **kwargs)

    def update_view_count(self):
        ViewCount(self).save()

class ViewCount(APIBasedModel):
    # Attributes
    views = models.BigIntegerField(_('Video view count'))
    count_datetime = models.DateTimeField(
        _('Date and time video views were counted'),
        auto_now_add=True)

    #Relationships
    video = models.ForeignKey(_('Video views are counted for'), Video)

    # Methods
    def __init__(self, video):
        parameters = dict(part='statistics',
                          id=video.video_id,
                          fields='items/statistics/viewCount')
        data = self._get_from_api(parameters)
        self.video = video
        self.views = data['statistics']['viewCount']

    def __str__(self):
        return str(self.count_datetime) + ': ' + str(self.views)
