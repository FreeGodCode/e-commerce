# -*- coding: utf-8  -*-
# @Author: ty
# @File name: notification.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:37 PM
# @Description:
from flask import render_template

from app.config.order_status import SHIPPING_HISTORY, ORDER_STATUS_DESCRIPTION

from app.config import *
from app.services import jobs


@user_signup.connect
def notification_user_signup(sender, user):
    """
    用户注册成功邮件通知
    :param sender:
    :param user:
    :return:
    """
    title = '您已成功注册'
    message = '请进入程序登录'
    jobs.notification.send_mail.delay([user.account.email], title, message)


def notification_order(order, status):
    """
    订单状态变更邮件通知
    :param order:
    :param status:
    :return:
    """
    user = order.customer
    title = '订单状态改变'
    status_desc = ORDER_STATUS_DESCRIPTION.get(status)
    status_history = SHIPPING_HISTORY.get(status)
    message = render_template('email/order_status_change.html', user=user, order=order, status_history=status_history,
                              status_desc=status_desc)
    jobs.notification_send_mail.delay([user.account.email], title, message)
