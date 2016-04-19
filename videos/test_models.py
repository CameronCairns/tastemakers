import itertools

from django.db import transaction
from django.db.utils import IntegrityError
from django.test import TestCase

from profiles.models import User
from videos.models import Comment, Video, Vote, Category, Tag
from videos.mixins import VideoAPIMixin

class VideosTestCase(TestCase, VideoAPIMixin):
    def setUp(self):
        parameters = dict(part='id',
                          fields='items/id/videoId',
                          maxResults=10, 
                          # Don't need to be embarassed while testing
                          safeSearch='strict', 
                          type='video')
        JSON = self._get_info_from_api('search', parameters)
        video_ids = [data['id']['videoId']
                     for data
                     in JSON['items']]
        user = User.objects.create_user('test_user',
                                        'test@tastemakers.com',
                                        'test_password')
        user.save()
        Video.objects.create_videos(user.id, *video_ids)
        # create comments
        parents = [Comment(text='Parent text',
                           commenter_id=user.id,
                           video_id=id)
                   for id
                   in Video.objects.values_list('id', flat=True)]
        Comment.objects.bulk_create(parents)
        children = [Comment(text='Child text',
                            commenter_id=user.id,
                            video_id=parent.video_id,
                            parent=parent)
                    for parent
                    in Comment.objects.all()]
        Comment.objects.bulk_create(children)

    def test_video_objects_created(self):
        # Make sure video objects are created
        self.assertTrue(Video.objects.all().count() > 0)

    def test_view_count_created_on_video_save(self):
        # Make sure that all video objects have view counts associated with
        # them
        self.assertEqual(Video.objects.exclude(viewcount=None).count(),
                         Video.objects.count())
    def test_category_associated(self):
        self.assertEqual(Video.objects.exclude(category=None).count(),
                         Video.objects.count())

    def test_tags_associated(self):
        # Make sure that tags are associated with a video if they exist
        self.assertEqual(Video.objects.exclude(category=None).count(),
                         Video.objects.count())

    def test_commenting_on_videos(self):
        # Test that comments associated with Videos
        self.assertEqual(Video.objects.exclude(comment=None).count(),
                         Video.objects.count())
        # Test that parent comments were created
        self.assertEqual(Comment.objects.filter(parent=None).count(),
                         Video.objects.count())
        # Test that child comments were created
        self.assertEqual(Comment.objects.exclude(parent=None).count(),
                         Video.objects.count())

    def test_voting_on_comments(self):
        comment = Comment.objects.all()[0]
        user = User.objects.all()[0]
        # Test first vote works
        vote = Vote.objects.create(value=1, comment=comment, voter=user)
        self.assertEqual(Vote.objects.count(), 1)
        # Test that points are calculated properly
        self.assertEqual(comment.score, 1)
        # Test that negative votes create negative scores
        vote.value = -1
        vote.save()
        # Test that the score attribute is cached
        self.assertEqual(comment.score, 1)
        # Test that cache invalidation works correctly
        del comment.score
        self.assertEqual(comment.score, -1)
        # Test that a user can only vote for a comment once
        try:
            # Should fail
            with transaction.atomic():
                vote = Vote.objects.create(value=-1, comment=comment, voter=user)
            self.assertTrue(0, 'duplicate vote allowed')
        except IntegrityError:
            pass

    def test_user_can_follow_categories(self):
        user = User.objects.all()[0]
        category_ids = Category.objects.values_list('id', flat=True)
        user.followed_categories.add(*category_ids)
        self.assertEqual(user.followed_categories.count(),
                         Category.objects.count())

    def test_user_can_follow_tags(self):
        user = User.objects.all()[0]
        tag_ids = Tag.objects.values_list('id', flat=True)
        user.followed_tags.add(*tag_ids)
        self.assertEqual(user.followed_tags.count(),
                         Tag.objects.count())

    def test_user_can_favorite_videos(self):
        user = User.objects.all()[0]
        video_ids = Video.objects.values_list('id', flat=True)
        user.favorite_videos.add(*video_ids)
        self.assertEqual(user.favorite_videos.count(),
                         Video.objects.count())
