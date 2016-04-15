from django.db import models
from django.utils.translation import ugettext_lazy as _

import dateutil.parser

from videos.mixins import VideoAPIMixin

class Category(models.Model):
    """
    Every youtube video must have a category assigned to it so we keep track
    of them here to easily find videos belonging to each category
    """
    # Attributes
    title = models.CharField(_('Category title'), max_length=100)

class VideoManager(models.Manager, VideoAPIMixin):
    """
    Custom manager needed to couple the gathering of data needed to create
    an object with its api calls and logic
    """
    def create_videos(self, *video_ids):
        """
        function allows for the singular or bulk creation of video objects
        given their video_id
        """
        # Define the fields to receive from the API
        fields =('items/snippet('
                 'publishedAt, categoryId, tags, title, description)')
        # Define the api parameters shared by all videos
        # Note the syntax in defining the id, api allows for getting info
        # on multiple videos given a comma separated video_id list
        parameters = dict(part='snippet',
                          id=', '.join(video_ids),
                          fields=fields)
        # Get JSON from API response 
        JSON = self._get_info_from_api('videos', parameters)
        videos = [Video(category_id=video_info['snippet']['categoryId'],
                        description=video_info['snippet']['description'],
                        published=dateutil.parser.parse(
                            video_info['snippet']['publishedAt']),
                        title=video_info['snippet']['title'],
                        video_id=video_ids[i])
                        
                  for i, video_info
                  in enumerate(JSON['items'])]
        self.bulk_create(videos)
        # Need to fetch the saved videos from the database since bulk create
        # does not update the previously created video objects
        videos = Video.objects.filter(video_id__in=video_ids).all()
        ViewCount.objects.create_viewcounts(*videos)
                

class Video(models.Model):
    # Attributes
    created = models.DateTimeField(_('Creation date'), auto_now_add=True)
    description = models.TextField(_('Video description'),
                                   max_length=5000,
                                   blank=True)
    published = models.DateTimeField(_('Video publication date'))
    title = models.CharField(_('Video title'), max_length=100)
    updated = models.DateTimeField(_('Last updated'), auto_now=True)
    video_id = models.CharField(_('Youtube ID for video'),
                                unique=True,
                                max_length=500)

    # Relationships
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('Video category'))
    # uploader = models.ForeignKey(_('Video uploader'), User)

    # Many to Many Relationships
    # tags = models.ManyToManyField(_('Video tags'), Tag, blank=True)

    # Manager
    objects = VideoManager()

    def __str__(self):
        return self.title

class ViewCountManager(models.Manager, VideoAPIMixin):
    """
    Custom manager needed to couple the gathering of data needed to create
    an object with its api calls and logic
    """
    def create_viewcounts(self, *videos):
        # Define the parameters to supply to the API
        parameters = dict(part='statistics',
                          id=', '.join(video.video_id for video in videos),
                          fields='items/statistics/viewCount')
        # Get JSON from API response
        JSON = self._get_info_from_api('videos', parameters)
        # Extract view counts for each video
        viewcounts = [ViewCount(views=video_info['statistics']['viewCount'],
                                video=videos[i])
                      for i, video_info
                      in enumerate(JSON['items'])]
        # Now create the object(s) with the gathered information
        self.bulk_create(viewcounts)

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
