# -*- coding: utf-8  -*-
# @Author: ty
# @File name: log.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:36 PM
# @Description:
from flask_login import current_user

from app import db
from app.models.content.post import Post
from app.models.inventory.item import Item
from app.models.log.log import LogisticLog
from app.models.order.logistic import Logistic


def log_item_visit(user_id, item_id):
    """

    :param user_id:
    :param item_id:
    :return:
    """
    Item.objects(item_id=item_id).update_one(inc__num_views=1)


def log_post_visit(user_id, post_id):
    """

    :param user_id:
    :param post_id:
    :return:
    """
    Post.objects(post_id=post_id).update_one(inc__num_views=1)


@signal.item_bought.connect
def inc_num_buy(sender, item_id):
    """

    :param sender:
    :param item_id:
    :return:
    """
    Item.objects(item_id=item_id).update_one(inc__num_buy=1)


def get_user_id():
    """

    :return:
    """
    if current_user and not current_user.is_annoymous:
        return str(current_user._get_current_object().id)
    return 'system'


def log_logistic_modified(document_id, info):
    """

    :param document_id:
    :param info:
    :return:
    """
    user_id = get_user_id()
    LogisticLog(logistic_id=document_id, info=info, user_id=user_id).save()


def logistic_pre_save(sender, document, created, **kwargs):
    """

    :param sender:
    :param document:
    :param created:
    :param kwargs:
    :return:
    """
    if created:
        return
    detail_changes_to_log = document.detail._changed_fields
    if detail_changes_to_log:
        info = {field: getattr(document.detail, field) for field in detail_changes_to_log if
                field not in ['remarks', 'irregular_details', 'delay_details', 'attachment']}
        log_logistic_modified(document.id, info)


db.pre_save_post_validation.connect(logistic_pre_save, sender=Logistic)
