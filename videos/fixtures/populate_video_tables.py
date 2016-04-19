import itertools
import json
import os
import random

import requests

from profiles.models import User, Profile
from videos.models import Category, Video, Tag
from videos.mixins import VideoAPIMixin

def exclude_user(user_ids, id_to_exclude):
    id_index = user_ids.index(id_to_exclude)
    return user_ids[:id_index] + user_ids[id_index+1:]

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
    user_ids = list(User.objects.values_list('id', flat=True))
    # Exclude first_user id as a profile has already been created for it
    user_ids.remove(first_user.id)
    # Create profiles for all bulk created users
    profiles = [Profile(user_id=id)
                for id
                in user_ids]
    Profile.objects.bulk_create(profiles)

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

def populate_user_relationships():
    """
    Creates random relationships for users with other users, categories, tags
    and videos
    """
    id_objects = [Category, User, Tag, Video]
    id_map = map(lambda x:x.objects.values_list('id', flat=True), id_objects)
    category_ids, user_ids, tag_ids, video_ids = [list(query)
                                                  for query
                                                  in list(id_map)]
    for user in User.objects.iterator():
        user.favorite_videos.add(*random.sample(video_ids, 10))
        user.followed_categories.add(*random.sample(category_ids, 10))
        user.followed_tags.add(*random.sample(tag_ids, 50))
        user.following.add(*random.sample(exclude_user(user_ids, user.id), 5))


def populate_tables():
    populate_category_table()
    populate_user_table()
    populate_video_table()
    populate_user_relationships()
