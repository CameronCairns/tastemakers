from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    """
    Class to define users for the website. Adds some extra attributes to the
    user class built into Django and adds a recursive manytomany for following
    other users submissions, likes, etc
    """
    # Attributes
    email_verified = models.BooleanField(_('Email is verified'),
                                         default=False)

    # Relations
    following = models.ManyToManyField('self',
                                       symmetrical=False,
                                       verbose_name=_('Followed users'),
                                       related_name='followers')

    # Manager
    objects = UserManager()

    # Functions
    def save(self, *args, **kwargs):
        """
        Create a profile object and relate user to it upon creation of a user
        object
        """
        if self.pk is None:
            super(User, self).save(*args, **kwargs)
            Profile.objects.create(user=self)
        else:
            super(User, self).save(*args, **kwargs)

    def __str__(self):
        return '{0} {1}'.format(self.first_name, self.last_name)


class Badge(models.Model):
    """
    Badges that are awarded to a user when they have accomplished predefined
    achievements. Important gamification aspect of the application
    """
    title = models.CharField(_('Badge title'),
                             max_length=100)
    description = models.TextField(_('Badge description'))


class Profile(models.Model):
    """
    Class to hold the profile information about a user. This information is
    not essential to most use cases so there is no need to keep this data
    stored with the core user object
    """
    # Attributes
    blurb = models.CharField(_('User blurb'),
                             max_length=10000,
                             blank=True,
                             default='')
    website = models.URLField(_('User website'),
                              blank=True,
                              default='')
    # User login and core information stored in custom User class
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE,
                                verbose_name=_('User'))

    # Many to Many Relations
    badges = models.ManyToManyField(Badge,
                                    verbose_name=_('User badges'))
