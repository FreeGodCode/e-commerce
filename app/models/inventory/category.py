# -*- coding: utf-8  -*-
# @Author: ty
# @File name: category.py 
# @IDE: PyCharm
# @Create time: 1/17/21 11:13 AM
# @Description: 分类
from app import db

__all__ = ['Category']


class Category(db.Document):
    """类别"""
    meta = {
        'db_alias': 'db_inventory',
        'indexes': ['en'],
    }
    en = db.StringField(required=True, unique=True)
    cn = db.StringField()
    level = db.IntField(required=True)
    logo = db.StringField()

    def __unicode__(self):
        return '{}'.format(self.en)

    @classmethod
    def get_category_or_create(cls, sub, level):
        category = cls.objects(en=sub, level=level).first()
        if not category:
            category = cls(en=sub, level=level).save()
        return category

    @classmethod
    def update_cn(cls, en, cn):
        cls.objects(en=en).update(set__cn=cn)

    def to_json(self):
        return dict(
            en=self.en,
            cn=self.cn,
            level=self.level,
            logo=self.logo,
        )
