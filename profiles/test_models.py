from django.test import TestCase

from profiles.models import User, Profile


class ProfilesTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('test_user',
                                        'test@tastemakers.com',
                                        'test_password')
        hashed_password = user.password
        fake_users = [User(username='user{}'.format(index),
                           first_name='user{}first'.format(index),
                           last_name='user{}last'.format(index),
                           email='user{}@tastemakers.com'.format(index),
                           password=hashed_password)
                      for index
                      in range(100)]
        User.objects.bulk_create(fake_users)
        user_ids = list(User.objects.values_list('id', flat=True))
        # Original user had profile created on save so don't include in list
        user_ids.remove(user.id)
        # Create profiles for all bulk created users
        profiles = [Profile(user_id=id)
                    for id
                    in user_ids]
        Profile.objects.bulk_create(profiles)
        # emulate following users
        user.following.add(*user_ids)

    def test_users_created(self):
        self.assertEqual(User.objects.count(), 101)

    def test_profiles_created(self):
        self.assertEqual(Profile.objects.count(), 101)

    def test_users_associated_with_profile(self):
        self.assertEqual(User.objects.exclude(profile=None).count(), 101)

    def test_user_can_follow_other_users(self):
        user = User.objects.get(username='test_user')
        self.assertEqual(user.following.count(), 100)

    def test_users_can_be_followed(self):
        self.assertEqual(User.objects.exclude(followers=None).count(),
                         100)
