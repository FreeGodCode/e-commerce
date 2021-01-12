# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order_status.py 
# @IDE: PyCharm
# @Create time: 1/12/21 11:34 AM
# @Description:
from app import db

__all__ = ['OrderStatus']


class OrderStatus(db.Document):
    """"""
    meta = {
        'db_alias': 'db_order',
        'indexes': ['user_id'],
    }
    user_id = db.ObjectIdField(required=True)
    orders = db.ListField(db.ReferenceField('Order'))
    items = db.ListField(db.IntField())
    total = db.FloatField(default=0)
    received = db.FloatField(default=0)
    num_orders = db.IntField(default=0)
    num_unpaid = db.IntField(default=0)
    num_waiting = db.IntField(default=0)

    def clean(self):
        for field in ('total', 'received', 'num_orders', 'num_unpaid', 'num_waiting'):
            if getattr(self, field, 0) < 0:
                setattr(self, field, 0)

    @classmethod
    def by_user(cls, user_id):
        cls.objects(user_id=user_id).update_one(set__user_id=user_id, upsert=True)
        return cls.objects(user_id=user_id).first()
