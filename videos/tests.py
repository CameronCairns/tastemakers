import pdb 

from django.test import TestCase

from videos.models import Video
from videos.mixins import VideoAPIMixin

class VideoTestCase(TestCase, VideoAPIMixin):
    def setUp(self):
        parameters = dict(part='id',
                          fields='items/id/videoId',
                          max_result=10, 
                          # Don't need to be embarassed while testing
                          safeSearch='strict', 
                          type='video')
        JSON = self._get_info_from_api('search', parameters)
        video_ids = [data['id']['videoId']
                     for data
                     in JSON['items']]
        for video_id in video_ids:
            Video.objects.create_video(video_id)

    def test_video_objects_created(self):
        # Make sure video objects are created
        self.assertTrue(Video.objects.all().count() > 0)

    def test_view_count_created_on_video_save(self):
        # Make sure that all video objects have view counts associated with
        # them
        self.assertEqual(len([video
                              for video
                              in Video.objects.all()
                              if video.viewcount_set.count() > 0]),
                         Video.objects.all().count())
