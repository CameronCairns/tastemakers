from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

import dateutil.parser

from profiles.models import User
from videos.mixins import VideoAPIMixin


class Category(models.Model):
    """
    Every youtube video must have a category assigned to it so we keep track
    of them here to easily find videos belonging to each category
    """
    # Attributes
    # Should be unique but youtube has two separate categories named Comedy
    title = models.CharField(_('Category title'), max_length=100)

    # Many to Many Relationships
    followed_by = models.ManyToManyField(User,
                                         verbose_name=_(
                                           'Users following this category'),
                                         symmetrical=False,
                                         related_name='followed_categories')

    def __str__(self):
        return self.title


class Tag(models.Model):
    """
    Each youtube video has a variety of tags. Store them as a separate table
    to allow for finding videos with the same tag
    """
    # Attributes
    title = models.CharField(_('Tag title'), max_length=500, unique=True)

    # Many to Many Relationships
    followed_by = models.ManyToManyField(User,
                                         verbose_name=_(
                                             'Users following this tag'),
                                         symmetrical=False,
                                         related_name='followed_tags')

    def __str__(self):
        return self.title


class VideoManager(models.Manager, VideoAPIMixin):
    """
    Custom manager needed to couple the gathering of data needed to create
    an object with its api calls and logic
    """
    def create_videos(self, user_id, *video_ids):
        """
        function allows for the singular or bulk creation of video objects
        given their video_id
        """
        # Ensure there are no repeat video_ids entered
        video_ids = list(set(video_ids))
        # Find videos that already exist to avoid bulk create failure
        extant_videos = Video.objects.filter(
                video_id__in=video_ids).values_list('video_id', flat=True)
        # Derive new video_ids from excluding members of extant video_ids
        video_ids = [video_id
                     for video_id
                     in video_ids
                     if video_id not in extant_videos]
        # Define the fields to receive from the API
        fields = ('items/snippet('
                  'publishedAt, categoryId, tags, title, description)')
        # Define the api parameters shared by all videos
        # Note the syntax in defining the id, api allows for getting info
        # on multiple videos given a comma separated video_id list
        parameters = dict(part='snippet',
                          id=', '.join(video_ids),
                          fields=fields)
        JSON = self._get_info_from_api('videos', parameters)
        # Collect tags for creation and/or association after video creation
        tags = {video_ids[i]:
                (video_info['snippet']['tags']
                 if 'tags' in video_info['snippet']
                 else [])
                for i, video_info
                in enumerate(JSON['items'])}
        # Collect video objects for bulk creation
        videos = [Video(category_id=video_info['snippet']['categoryId'],
                        description=video_info['snippet']['description'],
                        published=dateutil.parser.parse(
                            video_info['snippet']['publishedAt']),
                        title=video_info['snippet']['title'],
                        uploader_id=user_id,
                        video_id=video_ids[i])
                  for i, video_info
                  in enumerate(JSON['items'])]
        self.bulk_create(videos)
        # Need to fetch the saved videos from the database since bulk create
        # does not update the previously created video objects
        videos = Video.objects.filter(video_id__in=video_ids).all()
        # Find the view count for all the recently created videos
        ViewCount.objects.create_viewcounts(*videos)
        # Create and/or associate each videos tags with that video using a tag
        # object
        for video in videos:
            if tags[video.video_id]:
                # Ensure there are no repeat tags
                unique_tags = list(set(tags[video.video_id]))
                # Find tags that already exist to avoid bulk create failure
                extant_tags = Tag.objects.filter(
                        title__in=unique_tags).values_list(
                                'title', flat=True)
                # Derive new_tags from any associated tags that don't already
                # exist in Tags table
                new_tags = [Tag(title=tag)
                            for tag
                            in unique_tags
                            if tag not in extant_tags]
                # Create any new tags
                if new_tags:
                    Tag.objects.bulk_create(new_tags)
                # Now gather all tag objects and associate them with the video
                video_tags = Tag.objects.filter(title__in=tags[video.video_id])
                video.tags.add(*video_tags)
        return videos


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
                                max_length=100)

    # Relationships
    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('Video category'))
    uploader = models.ForeignKey(User,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('Video uploader'),
                                 related_name='uploaded_videos')

    # Many to Many Relationships
    tags = models.ManyToManyField(Tag, verbose_name=_('Video tags'))
    votes = models.ManyToManyField(User,
                                   through='VideoVote',
                                   verbose_name=_('Users who liked video'),
                                   related_name='liked_videos')
    favorited_by = models.ManyToManyField(User,
                                          related_name='favorite_videos',
                                          verbose_name=_(
                                              'Users who favorited video'))

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

    # Relationships
    video = models.ForeignKey(Video,
                              on_delete=models.CASCADE,
                              verbose_name=_('Video views are counted for'))

    # Manager
    objects = ViewCountManager()

    class Meta:
        # Avoid creation of multiple viewcounts for same datetime and video
        unique_together = ('video', 'count_datetime')

    def __str__(self):
        return str(self.count_datetime) + ': ' + str(self.views)


class Comment(models.Model):
    # Attributes
    text = models.CharField(_('Comment text'), max_length=10000)
    created = models.DateTimeField(_('Comment creation time'),
                                   auto_now_add=True)

    # Relations
    parent = models.ForeignKey('self',
                               null=True,
                               default=None,
                               on_delete=models.CASCADE,
                               verbose_name=_('Comment parent'))
    commenter = models.ForeignKey(User,
                                  verbose_name=_('Commenter'),
                                  on_delete=models.CASCADE)
    video = models.ForeignKey(Video,
                              on_delete=models.CASCADE,
                              verbose_name=_('Video comment is for'))

    # ManyToMany
    votes = models.ManyToManyField(User,
                                   verbose_name=_('User votes on comment'),
                                   through='CommentVote',
                                   related_name=_('comments_voted_on'))

    @cached_property
    def score(self):
        return self.commentvote_set.aggregate(
                Sum('value')).get('value__sum', 0)


class CommentVote(models.Model):
    # Attributes
    value = models.SmallIntegerField(_('Vote value assigned by User, 1 or -1'))

    # Relations
    comment = models.ForeignKey(Comment,
                                on_delete=models.CASCADE,
                                verbose_name=_('Comment voted on'))
    voter = models.ForeignKey(User,
                              on_delete=models.CASCADE,
                              verbose_name=_('User who voted on comment'))

    class Meta:
        unique_together = ('comment', 'voter')


class VideoVote(models.Model):
    # Attributes
    value = models.IntegerField(_('Vote value'))

    # Relations
    video = models.ForeignKey(Video,
                              on_delete=models.CASCADE,
                              verbose_name=_('Video voted on'))
    voter = models.ForeignKey(User,
                              on_delete=models.CASCADE,
                              verbose_name=_('User who voted on video'))

    class Meta:
        unique_together = ('video', 'voter')
