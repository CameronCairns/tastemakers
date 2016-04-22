from django.db import models
from django.db.models import Max, Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

import dateutil.parser

from profiles.models import User
from videos.mixins import VideoAPIMixin


def remove_existing(manager, items, attribute):
    """
    Helper function to remove items from a list that have already been
    created
    """
    unique_items = list(set(items))
    kwargs = {attribute + '__in': unique_items}
    extant_items = manager.filter(**kwargs).values_list(attribute, flat=True)
    return [item for item in unique_items if item not in extant_items]


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


class TagManager(models.Manager):
    def create_tags(self, *tag_titles):
        new_tags = remove_existing(self, tag_titles, 'title')
        tags = [self.model(title=tag)
                for tag
                in new_tags]
        # Create any new tags
        if tags:
            self.bulk_create(tags)
        return self.filter(title__in=tag_titles).values_list('id', flat=True)


class Tag(models.Model):
    """
    Each youtube video has a variety of tags. Store them as a separate table
    to allow for finding videos with the same tag
    """
    # Attributes
    title = models.CharField(_('Tag title'), max_length=500, unique=True)

    # Relations
    followed_by = models.ManyToManyField(User,
                                         verbose_name=_(
                                             'Users following this tag'),
                                         symmetrical=False,
                                         related_name='followed_tags')

    # Manager
    objects = TagManager()

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
        given their video_id(s)
        """
        new_videos = remove_existing(self, video_ids, 'video_id')
        JSON = self.get_video_info(new_videos)
        tags = {new_videos[i]:
                (video_info['snippet']['tags']
                 if 'tags' in video_info['snippet']
                 else [])
                for i, video_info
                in enumerate(JSON['items'])}
        videos = [self.model(category_id=video_info['snippet']['categoryId'],
                             description=video_info['snippet']['description'],
                             published=dateutil.parser.parse(
                                 video_info['snippet']['publishedAt']),
                             title=video_info['snippet']['title'],
                             uploader_id=user_id,
                             video_id=new_videos[i])
                  for i, video_info
                  in enumerate(JSON['items'])]
        if videos:
            self.bulk_create(videos)
            # Get primary keys generated after bulk create, and videos objects
            videos = self.filter(video_id__in=new_videos).all()
            video_ids = videos.values_list('id', flat=True)
            video_list = list(videos)
            # Users automatically vote for any video they submit
            VideoVote.objects.create_votes(user_id, *video_ids)
            # Find the view count for all the recently created videos
            ViewCount.objects.create_viewcounts(*video_list)
            for video in video_list:
                # Create and/or associate each videos tags with that video
                if tags[video.video_id]:
                    video_tags = Tag.objects.create_tags(*tags[video.video_id])
                    video.tags.add(*video_tags)
        return videos

    def get_video_info(self, video_ids):
        # API Request Parameters
        fields = ('items/snippet('
                  'publishedAt, categoryId, tags, title, description)')
        parameters = dict(part='snippet',
                          id=', '.join(video_ids),
                          fields=fields)
        return(self._get_info_from_api('videos', parameters))

    def order_by_votes(self, descending=True):
        # Replace this with a more complex algorithm later
        query = self.annotate(vote_score=Sum('videovote__value'))
        # query = query.prefetch_related('videovote')
        ordering = '{}vote_score'.format('-' if descending else '')
        return query.order_by(ordering)

    def order_by_views(self, descending=True):
        # Replace this with a more complex algorithm later
        query = self.annotate(max_views=Max('viewcount__views'))
        # query = query.prefetch_related('viewcount')
        ordering = '{}max_views'.format('-' if descending else '')
        return query.order_by(ordering)


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
        viewcounts = [self.model(views=video_info['statistics']['viewCount'],
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


class CommentManager(models.Manager):
    def order_by_votes(self, descending=True):
        query = self.annotate(vote_score=Sum('commentvote__value'))
        ordering = '{}vote_score'.format('-' if descending else '')
        return query.order_by(ordering)

    def get_children(self, depth=None):
        """
        Function to return the children of a parent process, descends into
        each childs children as well until all children have been exaughsted
        or the maximum depth has been reached
        """
        if depth is None:
            return [[comment, comment.children.get_children()]
                    if comment.children.count()
                    else comment
                    for comment
                    in self.all()]
        elif depth == 0:
            # Maximum depth reached so just return all children related to this
            # object and exit the function
            return self.all()
        else:
            # Still traversing down child relations
            return [comment.children.get_children(depth=depth-1)
                    if comment.children.count()
                    else comment
                    for comment
                    in self.all()]


class Comment(models.Model):
    # Attributes
    text = models.CharField(_('Comment text'), max_length=10000)
    created = models.DateTimeField(_('Comment creation time'),
                                   auto_now_add=True)

    # Relations
    parent = models.ForeignKey('self',
                               related_name='children',
                               null=True,
                               default=None,
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

    # Manager
    objects = CommentManager()

    # Methods
    def save(self, *args, **kwargs):
        """
        User that creates comment automatically votes for it
        """
        if self.pk is None:
            # Has not been saved before so it is being created
            super(Comment, self).save(*args, **kwargs)
            CommentVote.create(value=1,
                               voter=self.commenter,
                               comment=self)
        else:
            super(Comment, self).save(*args, **kwargs)


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


class VideoVoteManager(models.Manager):
    def create_votes(self, user_id, *video_ids):
        # Want this to fail loudly if logic tries to vote on video already
        # voted on so no stripping of existing values done
        vote_weight = 1
        votes = [self.model(value=vote_weight,
                            video_id=video_id,
                            voter_id=user_id)
                 for video_id
                 in video_ids]
        self.bulk_create(votes)


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

    # Manager
    objects = VideoVoteManager()

    class Meta:
        unique_together = ('video', 'voter')
