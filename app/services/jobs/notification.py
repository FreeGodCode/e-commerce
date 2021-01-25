# -*- coding: utf-8  -*-
# @Author: ty
# @File name: notification.py 
# @IDE: PyCharm
# @Create time: 1/25/21 11:56 AM
# @Description: 通知
from flask_mail import Message

from app import mail
from app.services import celery


@celery.task
def send_mail(recipients, title, message, sender='thechosenone_ty@163.com', cc=None):
    """

    :param recipients:
    :param title:
    :param message:
    :param sender:
    :param cc:
    :return:
    """
    msg = Message(title, recipients=recipients)
    if sender:
        msg.sender = sender
    if cc:
        msg.cc = cc

    msg.html = message
    mail.send(msg)
    return True
