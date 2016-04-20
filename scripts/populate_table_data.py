from datetime import timedelta
import itertools
import random

import faker

from profiles.models import User, Profile
from videos.models import (Category, Comment, CommentVote, Tag, Video,
                           VideoVote, ViewCount)
from videos.mixins import VideoAPIMixin

fake = faker.Factory.create()


def exclude_user(user_ids, id_to_exclude):
    """
    Helper function to simplify excluding a user_id from a list
    """
    id_index = user_ids.index(id_to_exclude)
    return user_ids[:id_index] + user_ids[id_index+1:]


def populate_category_table():
    """
    Populate youtube categories from the category list api call for the US
    """
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
    """
    Create 100 random users to associate with video submissions, comments, etc
    done using bulk create with the same password hash as the first user
    created normally
    """
    # Create the first fake user from which a hashed password will be gathered
    # for future entries
    first_user = User.objects.create_user(fake.user_name(),
                                          fake.email(),
                                          fake.password())
    first_user.save()
    first_user.profile.blurb = fake.text
    first_user.profile.website = fake.url
    first_user.profile.save()
    hashed_password = first_user.password
    fake_users = [User(username=fake.user_name(),
                       first_name=fake.first_name(),
                       last_name=fake.last_name(),
                       email=fake.email(),
                       password=hashed_password)
                  for index
                  in range(99)]
    User.objects.bulk_create(fake_users)
    user_ids = list(User.objects.values_list('id', flat=True))
    # Exclude first_user id as a profile has already been created for it
    user_ids.remove(first_user.id)
    # Create profiles for all bulk created users
    profiles = [Profile(user_id=id, blurb=fake.text, website=fake.url)
                for id
                in user_ids]
    Profile.objects.bulk_create(profiles)


def populate_video_table():
    """
    Populate video table by querying 50 videos from each category from
    youtube
    """
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
        Video.objects.create_videos(user_ids[index % 50],
                                    *video_ids[index:index+50])


def populate_user_relationships():
    """
    Creates random relationships for users with other users, categories, tags
    and videos
    """
    id_objects = [Category, User, Tag, Video]
    id_map = map(lambda x: x.objects.values_list('id', flat=True), id_objects)
    category_ids, user_ids, tag_ids, video_ids = [list(query)
                                                  for query
                                                  in list(id_map)]
    for user in User.objects.iterator():
        user.favorite_videos.add(*random.sample(video_ids, 10))
        user.followed_categories.add(*random.sample(category_ids, 10))
        user.followed_tags.add(*random.sample(tag_ids, 50))
        user.following.add(*random.sample(exclude_user(user_ids, user.id), 5))


def populate_comment_table():
    """
    Generate comment data by having each user generate comments for each
    video and then randomly generate 1000 comments on randomly selected
    existing comments
    """
    user_ids = list(User.objects.values_list('id', flat=True))
    video_ids = list(Video.objects.values_list('id', flat=True))
    # Generate comments from all users for all videos
    video_comments = [Comment(text=fake.text(),
                              commenter_id=user_id,
                              video_id=video_id)
                      for user_id in user_ids
                      for video_id in video_ids]
    Comment.objects.bulk_create(video_comments)
    # Generate random comments to comments from all users
    for number_of_generations in range(1000):
        comments = [Comment(text=fake.text(),
                            commenter_id=random.choice(user_ids),
                            parent_id=comment.id,
                            video_id=comment.video_id)
                    for comment
                    in Comment.objects.all().order_by('?')[:100]]
        Comment.objects.bulk_create(comments)


def populate_user_votes_comments():
    """
    Populate user voting data by having each user randomly vote for
    10,000 comments.
    """
    comment_ids = list(Comment.objects.values_list('id', flat=True))
    user_ids = list(User.objects.values_list('id', flat=True))
    for user_id in user_ids:
        comments = random.sample(comment_ids, 10000)  # 10,000 is 5% of 200,000
        positive_votes = [CommentVote(value=1,
                                      comment_id=comment_id,
                                      voter_id=user_id)
                          for comment_id
                          in comments[:5000]]
        negative_votes = [CommentVote(value=-1,
                                      comment_id=comment_id,
                                      voter_id=user_id)
                          for comment_id
                          in comments[5000:]]
        votes = itertools.chain(positive_votes, negative_votes)
        CommentVote.objects.bulk_create(votes)


def populate_user_votes_videos():
    """
    Populate user voting data by having each user randomly vote for
    50 videos
    """
    video_ids = list(Video.objects.values_list('id', flat=True))
    user_ids = list(User.objects.values_list('id', flat=True))
    for user_id in user_ids:
        videos = random.sample(video_ids, 50)  # 50 is 5% of 1,000
        positive_votes = [VideoVote(value=1,
                                    video_id=video_id,
                                    voter_id=user_id)
                          for video_id
                          in videos[:5000]]
        negative_votes = [VideoVote(value=-1,
                                    video_id=video_id,
                                    voter_id=user_id)
                          for video_id
                          in videos[5000:]]
        votes = itertools.chain(positive_votes, negative_votes)
        VideoVote.objects.bulk_create(votes)


def populate_video_viewcounts():
    """
    Simulate video comment viewcounts by subtracting a random amount of views
    from a videos intial viewcount and associating the difference with a day
    before the day the viewcount was gathered from. Continuing until the count
    goes to zero
    """
    past_views = []
    for viewcount in ViewCount.objects.iterator():
        end_time = viewcount.count_datetime
        video_id = viewcount.video_id
        count = viewcount.views
        viewcounts = []
        while count > 0:
            count -= random.randint(0, count)
            viewcounts.append(count)
        past_views.append([ViewCount(video_id=video_id,
                                     count_datetime=(
                                         end_time - timedelta(days=day+1)),
                                     views=count)
                           for day, count
                           in enumerate(viewcounts)])
    ViewCount.objects.bulk_create(itertools.chain(*past_views))


def populate_tables():
    populate_category_table()
    populate_user_table()
    populate_video_table()
    populate_user_relationships()
    populate_comment_table()
    populate_user_votes_comments()
    populate_user_votes_videos()
    populate_video_viewcounts()
