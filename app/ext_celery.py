# -*- coding: utf-8  -*-
# @Author: ty
# @File name: ext_celery.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:21 PM
# @Description:
from celery import Celery

from app.create_app import create_app


def make_celery(app=None):
    """

    :param app:
    :return:
    """
    app = app or create_app(app_name='worker')
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
