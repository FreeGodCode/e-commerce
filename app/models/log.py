# -*- coding: utf-8  -*-
# @Author: ty
# @File name: log.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:37 PM
# @Description: 物流
from datetime import datetime

from app import db

__all__ = ['LogisticLog']


class LogisticLog(db.Document):
    """"""
    meta = {
        'db_alias': 'db_log',
        'allow_inheritance': True,
        'indexes': ['logistic_id', 'timestamp'],
        'ordering': ['-timestamp'],
    }
    log_type = db.StringField()
    logistic_id = db.ObjectIdField(required=True)
    timestamp = db.DateTimeField(default=datetime.utcnow)
    user_id = db.StringField(required=False)
    info = db.DictField()

    @classmethod
    def create(cls, log, data, user_id='system'):
        return cls(logistic_id=log.id, info=data, user_id=user_id).save()
