import pdb 

from django.test import TestCase

from videos.models import Video
from videos.mixins import VideoAPIMixin

class VideoTestCase(TestCase, VideoAPIMixin):
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
        Video.objects.create_videos(*video_ids)

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
