import itertools
import os

import json

import requests

from videos.models import Category, Video
from videos.mixins import VideoAPIMixin

def populate_category_table():
    # By inspection I found that categories are the same across supported
    # youtube regions
    parameters = dict(part='snippet', regionCode='US')
    JSON = VideoAPIMixin._get_info_from_api('videoCategories',
                                            params=parameters)
    categories = [Category(pk=data['id'], title=data['snippet']['title'])
                  for data
                  in JSON['items']]
    Category.objects.bulk_create(categories)

def populate_video_table():
    parameters = dict(part='id',
                      fields='items/id/videoId',
                      maxResults=50, 
                      # Don't need to be embarassed while testing
                      safeSearch='strict', 
                      type='video',
                      # Only want to allow embeddable videos for dev database
                      videoEmbeddable='true')
    responses = [VideoAPIMixin._get_info_from_api('search', params={
                     **parameters, **{'videoCategoryId': category_id}})
                 for category_id
                 in Category.objects.values_list('id', flat=True)]
    video_ids = list(itertools.chain(*[[data['id']['videoId']
                                      for data
                                      in JSON['items']]
                                     for JSON
                                     in responses]))
    for index in range(0, len(video_ids), 50):
        Video.objects.create_videos(*video_ids[index:index+50])
