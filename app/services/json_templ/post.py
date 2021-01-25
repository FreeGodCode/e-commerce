# -*- coding: utf-8  -*-
# @Author: ty
# @File name: post.py 
# @IDE: PyCharm
# @Create time: 1/25/21 5:05 PM
# @Description:
from flask_login import current_user

from app.config.enum import NOTIFICATION_TYPE
from app.models.content.post import PostLike


def post_json(post):
    '''

    :param post:
    :return:
    '''
    post_data = post.to_simple_json()
    location = ''
    if post.location_extra:
        location = ','.join(post.location_extra.values())
    post_data.update({'location': location})

    is_liked = bool(PostLike.objects(post=post, user_id=current_user.id)) if current_user.is_authenticated else False
    post_data.update({'is_liked': is_liked})

    user = post.user
    user_info = dict(
        id=str(user.id),
        name=user.name,
        avatar_url=user.avatar_url,
        avatar_thumb=user.avatar_thumb,
    )
    post_data.update({'user': user_info})

    return post_data


def notification_json(notification):
    """

    :param notification:
    :return:
    """
    if notification.action == NOTIFICATION_TYPE.POST_LIKED:
        sub_title = '赞你的帖子'
    if notification.action == NOTIFICATION_TYPE.FOLLOW:
        sub_title = '关组你'
    if notification.action == NOTIFICATION_TYPE.COMMENT:
        sub_title = '评论你的帖子'
    if notification.action == NOTIFICATION_TYPE.REPLY:
        sub_title = '回复了你'

    user = notification.user
    return dict(
        created_at=notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        action=notification.action,
        sub_title=sub_title,
        content=notification.info,
        user=dict(
            id=str(user.id),
            name=user.name,
            avatar_url=user.avatar_url,
            avatar_thumb=user.avatar_thumb,
        ),
    )
