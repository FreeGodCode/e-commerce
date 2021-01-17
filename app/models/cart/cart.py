# -*- coding: utf-8  -*-
# @Author: ty
# @File name: cart.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:30 PM
# @Description: 购物车
from app import db

__all__ = ['Cart', 'EntrySpec', 'CartEntry']


class Cart(db.Document):
    """购物车模型类"""
    meta = {
        'db_alias': 'db_cart',
        'indexes': ['user_id', 'session_key']
    }
    entries = db.EmbeddedDocumentListField('CartEntry')

    user_id = db.StringField()
    session_key = db.StringField()

    def __repr__(self):
        return '<Cart: {}>'.format(self.id)


class CartEntry(db.EmbeddedDocument):
    """购物车实体类"""
    sku = db.IntField(required=True)
    quantity = db.IntField(default=1, required=True)
    created_at = db.DateTimeField()
    first_price = db.FloatField(default=0)


class EntrySpec(db.Document):
    meta = {
        'db_alias': 'db_cart',
        'indexes': ['sku', 'item_id']
    }
    # 唯一标识
    sku = db.IntField(required=True, unique=True)
    item_id = db.IntField()
    title = db.StringField()

    primary_image = db.StringField()
    item_available = db.BooleanField()

    price = db.FloatField()
    available = db.BooleanField()
    attributes = db.DictField()
    images = db.ListField(db.StringField())

    attribute_list = db.ListField(db.StringField())
    attribute_desc = db.DictField()

    brand = db.DictField()

    last_update_date = db.DateTimeField()
    carts = db.ListField(db.ReferenceField('Cart'))
    last_empty_date = db.DateTimeField()
