# -*- coding: utf-8  -*-
# @Author: ty
# @File name: post.py 
# @IDE: PyCharm
# @Create time: 1/16/21 5:19 PM
# @Description:
from datetime import datetime

from flask import current_app
from mongoengine import queryset_manager

from app import db
from app.config.enum import POST_TAG_TYPES, POST_STATUS, NOTIFICATION_TYPE, ACTIVITY_STATUS
from app.models.user.user import User

__all__ = ['Post', 'PostComment', 'PostLike', 'PostFeedback', 'PostActivity', 'PostTag', '']


@update_modified.apply
class Post(db.Document):
    meta = {
        'db_alias': 'db_content',
        'indexes': ['post_id', 'user_id', 'title', 'post_type', 'location', 'tags', 'num_views', 'created_at'],
        'ordering': ['-created_at']
    }

    post_id = db.SequenceField(required=True, unique=True, primary_key=True)
    primary_image = db.StringField()
    images = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    title = db.StringField(default='')
    location = db.PointField()
    location_extra = db.DictField()
    post_type = db.StringField(default=POST_TAG_TYPES.SHOW, choices=POST_TAG_TYPES)

    # extra
    num_likes = db.IntField(default=0)
    num_comments = db.IntField(default=0)
    num_views = db.IntField(default=0)

    status = db.StringField(default=POST_STATUS.NEW, required=True, choices=POST_STATUS)
    approved = db.BooleanField(default=True, required=True)

    # time
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    modified = db.DateTimeField()
    user_id = db.ObjectIdField()

    def __unicode__(self):
        return '%s' % self.post_id

    def __repr__(self):
        return '%s' % self.post_id

    @queryset_manager
    def approved_posts(doc_cls, queryset):
        return queryset.filter(approved=True)

    @classmethod
    def create(cls, post):
        for tag in post['tags']:
            PostTag.get_tag_or_create(tag)
        post = Post(**post)
        post.approved = False
        post.save()
        post_id = post.post_id
        return post_id

    @classmethod
    def modify(cls, new_post):
        """

        :param new_post:
        :return:
        """
        try:
            old_post = Post.objects.get(post_id=new_post['post_id'])
            old_post.status = POST_STATUS.MOD
        except DoseNotExist:
            current_app.logger.warning('does not exist in db: {}'.format(new_post))
            return

        for k, v in new_post.items():
            setattr(old_post, k, v)
        old_post.save()

        return old_post.post_id

    @classmethod
    def delete_post(cls, post_id):
        """

        :param post_id:
        :return:
        """
        try:
            post = cls.objects.get(id=post_id)
            post.status = 'DEL'
            post.approved = False
            post.save()
            return post.post_id
        except DoesNotExist:
            pass

    @property
    def small_thumbnail(self):
        return self.primary_image[:23] + 'post_thumbs/180x180/' + self.primary_image[23:]

    @property
    def large_thumbnail(self):
        return self.primary_image[:23] + 'post_thumbs/480x480/' + self.primary_image[23:]

    @property
    def user(self):
        return User.objects(id=self.user_id).first()

    def to_simple_json(self):
        type_map = {
            'SHOW': '心情',
            'SERVICE': '服务',
            'TRADE': '买卖',
        }
        type_dt = {
            'en': self.post_type,
            'cn': type_map[self.post_type],
        }
        return dict(post_id=str(self.post_id),
                    title=self.title,
                    type=type_dt,
                    primary_image=self.primary_image,
                    large_url=self.large_thumbnail,
                    small_url=self.small_thumbnail,
                    images=self.images,
                    created_at=self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    num_likes=self.num_likes,
                    num_views=self.num_views,
                    num_comments=self.num_comments,
                    tags=self.tags,
                    status=self.status
                    )


class PostComment(db.Document):
    """"""
    meta = {
        'db_alias': 'db_comment',
        'indexes': ['user_id', 'content', 'post', 'created_at'],
        'ordering': ['-created_at']
    }
    user_id = db.ObjectIdField()
    content = db.StringField(required=True)
    post = db.ReferenceField('Post')
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)

    @property
    def user(self):
        return User.objects(id=self.user_id).first()

    def to_json(self):
        user = self.user
        return dict(id=str(self.id), content=self.content,
                    user=dict(id=str(user.id), name=user.name, avatar_url=user.avatar_url,
                              avatar_thumb=user.avatar_thumb), created_at=self.created_at.strftime('%Y-%m-%d %H:%M:%S'))


class PostLike(db.Document):
    meta = {
        'db_alias': 'db_content',
        'indexes': ['user_id', 'post', 'created_at'],
        'ordering': ['-created_at'],
    }
    user_id = db.ObjectIdField()
    post = db.ReferenceField('Post')
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)

    @property
    def user(self):
        return User.objects(id=self.user_id).first()

    def to_json(self):
        user = self.user
        return dict(id=str(self.id), user=dict(id=str(user.id), name=user.name, avatar_url=user.avatar_url,
                                               avatar_thumb=user.avatar_thumb), )


class PostActivity(db.Document):
    """"""
    meta = {
        'db_alias': 'db_content',
        'indexes': ['user_id', 'to_user_id', 'post', 'created_at', 'action'],
        'ordering': ['created_at'],
    }
    user_id = db.ObjectIdField()
    post = db.ReferenceField('Post')
    action = db.StringField(choices=NOTIFICATION_TYPE)
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    to_user_id = db.ObjectIdField()
    info = db.StringField(default='')

    @property
    def user(self):
        return User.objects(id=self.user_id).first()

    @property
    def to_user(self):
        return User.objects(id=self.to_user_id).first()

    def to_json(self):
        user = self.user
        return dict(id=str(self.id), user=dict(id=str(user.id), name=user.name, avatar_url=user.avatar_url,
                                               avatar_thumb=user.avatar_thumb), )

    @classmethod
    def create(cls, user, to_user, post, action, info=''):
        notification = cls(user_id=user, to_user=to_user, post=post, action=action, info=info).save()
        return notification


class PostFeedback(db.Document):
    """"""
    meta = {
        'db_alias': 'db_content',
        'indeses': ['user_id', 'post', 'subject', 'created_at'],
        'ordering': ['-created_at'],
    }
    user_id = db.ObjectIdField()
    post = db.ReferenceField('Post')
    subject = db.StringField()
    status = db.StringField(default=ACTIVITY_STATUS.PENDING, choices=ACTIVITY_STATUS)
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)

    @property
    def user(self):
        return User.objects(id=self.user_id).first()


class PostTag(db.Document):
    """"""
    meta = {
        'db_alias': 'db_content',
        'indexes': ['name', 'kind', 'created_at'],
        'ordering': ['created_at'],
    }
    name = db.StringField(required=True, unique=True)
    bg_color = db.StringField(default='#f8f8f8')
    font_color = db.StringField(default='#444')
    kind = db.StringField(required=True, choices=POST_TAG_TYPES, default=POST_TAG_TYPES.UNCLASSIFIED)
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)

    def __unicode__(self):
        return '%s' % self.name

    @classmethod
    def get_tag_or_create(cls, name, kind=POST_TAG_TYPES.UNCLASSIFIED):
        if not cls.objects(name=name):
            bg_color, font_color = None, None
            if kind == POST_TAG_TYPES.TRADE:
                bg_color = '#e6b500'
                font_color = '#fff'
            elif kind == POST_TAG_TYPES.SERVICE:
                bg_color = '#EA004F'
                font_color = '#fff'
            elif kind == POST_TAG_TYPES.SHOW:
                bg_color = '#0a9dc7'
                font_color = '#fff'
            else:
                bg_color = '#f8f8f8'
                font_color = '#444'

            cls(name=name, kind=kind, bg_color=bg_color, font_color=font_color).save()

    def to_json(self):
        return dict(name=self.name, bg_color=self.bg_color, font_color=self.font_color)
