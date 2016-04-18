# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-18 23:28
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Category title')),
                ('followed_by', models.ManyToManyField(related_name='followed_categories', to=settings.AUTH_USER_MODEL, verbose_name='Users following this category')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=10000, verbose_name='Comment text')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Comment creation time')),
                ('commenter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Commenter')),
                ('parent', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='videos.Comment', verbose_name='Comment parent')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, unique=True, verbose_name='Tag title')),
                ('followed_by', models.ManyToManyField(related_name='followed_tags', to=settings.AUTH_USER_MODEL, verbose_name='Users following this tag')),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('description', models.TextField(blank=True, max_length=5000, verbose_name='Video description')),
                ('published', models.DateTimeField(verbose_name='Video publication date')),
                ('title', models.CharField(max_length=100, verbose_name='Video title')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Last updated')),
                ('video_id', models.CharField(max_length=100, unique=True, verbose_name='Youtube ID for video')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videos.Category', verbose_name='Video category')),
                ('favorited_by', models.ManyToManyField(related_name='favorite_videos', to=settings.AUTH_USER_MODEL, verbose_name='Users who favorited video')),
                ('tags', models.ManyToManyField(to='videos.Tag', verbose_name='Video tags')),
                ('uploader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_videos', to=settings.AUTH_USER_MODEL, verbose_name='Video uploader')),
                ('votes', models.ManyToManyField(related_name='liked_videos', to=settings.AUTH_USER_MODEL, verbose_name='Users who liked video')),
            ],
        ),
        migrations.CreateModel(
            name='ViewCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Date and time video views were counted')),
                ('views', models.BigIntegerField(verbose_name='Video view count')),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videos.Video', verbose_name='Video views are counted for')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.SmallIntegerField(verbose_name='Vote value assigned by User, 1 or -1')),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videos.Comment', verbose_name='Comment voted on')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User who voted on comment')),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='video',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videos.Video', verbose_name='Video comment is for'),
        ),
        migrations.AddField(
            model_name='comment',
            name='votes',
            field=models.ManyToManyField(related_name='comments_voted_on', through='videos.Vote', to=settings.AUTH_USER_MODEL, verbose_name='User votes on comment'),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('comment', 'voter')]),
        ),
        migrations.AlterUniqueTogether(
            name='viewcount',
            unique_together=set([('video', 'count_datetime')]),
        ),
    ]
