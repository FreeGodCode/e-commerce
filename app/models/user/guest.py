# -*- coding: utf-8  -*-
# @Author: ty
# @File name: guest.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:14 PM
# @Description: 游客
from app import db
from app.models.user.user import FavorAction

__all__ = ['GuestRecord']


class GuestRecord(db.Document, FavorAction):
    """visit records for guests user"""
    meta = {
        'indexes': ['session_key']
    }
    session_key = db.StringField(required=True)
    device_tokens = db.ListField(db.StringField())
    num_favors = db.IntField(default=0, min_value=0)
    favor_items = db.ListField(db.IntField())

    @classmethod
    def by_key(cls, key):
        cls.objects(session_key=key).update_one(set__session_key=key, upsert=True)
        return cls.objects.get(session_key=key)
