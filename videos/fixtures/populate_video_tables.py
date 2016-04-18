import itertools
import os
import json

import requests

from profiles.models import User
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

def populate_user_table():
    # Create the first fake user from which a hashed password will be gathered
    # for future entries
    first_user = User.objects.create_user('first user',
                                          'firstuser@tastemakers.com',
                                          'fake_password')
    first_user.save()
    hashed_password = first_user.password
    fake_users = [User(username='user{}'.format(index),
                       first_name='user{}first'.format(index),
                       last_name='user{}last'.format(index),
                       email='user{}@tastemakers.com'.format(index),
                       password=hashed_password)
                  for index 
                  in range(100)]
    User.objects.bulk_create(fake_users)

def populate_video_table():
    user_ids = User.objects.values_list('id', flat=True)
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
        Video.objects.create_videos(user_ids[index%50],
                                    *video_ids[index:index+50])
