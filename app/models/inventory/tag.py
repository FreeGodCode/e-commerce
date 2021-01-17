# -*- coding: utf-8  -*-
# @Author: ty
# @File name: tag.py 
# @IDE: PyCharm
# @Create time: 1/17/21 5:29 PM
# @Description: 标签
from app import db
from app.config.enum import TAG_TYPES

__all__ = ['Tag']


class Tag(db.Document):
    """标签"""
    meta = {
        'db_alias': 'db_inventory',
        'indexes': ['en']
    }

    en = db.StringField(required=True, unique=True)
    cn = db.StringField()
    kind = db.StringField(required=True, choices=TAG_TYPES, default=TAG_TYPES.CATEGORY)

    def __unicode__(self):
        return '{}'.format(self.en)

    @classmethod
    def get_tags(cls):
        return [dict(en=tag.en, cn=tag.cn) for tag in Tag.objects.all()]

    @classmethod
    def get_tag_or_create(cls, en, cn=None):
        if not Tag.objects(en=en):
            Tag(en=en, cn=cn, kind=TAG_TYPES.CATEGORY).save()

    @classmethod
    def update_cn(cls, en, cn):
        Tag.objects(en=en).update(set__cn=cn)

    def to_json(self):
        return dict(id=str(self.id), en=self.en, cn=self.cn, kind=self.kind)
