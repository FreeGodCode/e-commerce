# -*- coding: utf-8  -*-
# @Author: ty
# @File name: brand.py 
# @IDE: PyCharm
# @Create time: 1/17/21 11:06 AM
# @Description: 品牌
from app import db

__all__ = ['Brand']


class Brand(db.Document):
    """"""
    meta = {
        'db_alias': 'db_inventory',
        'indexes': ['en'],
    }
    en = db.StringField(required=True, unique=True)
    cn = db.StringField()
    description = db.StringField()
    logo = db.StringField()

    def __unicode__(self):
        return '{}'.format(self.en)

    def to_json(self):
        return dict(
            id=str(self.id),
            en=self.en,
            cn=self.cn,
            logo=self.logo,
            description=self.description,
        )

    @classmethod
    def get_brand_or_create(cls, en):
        try:
            brand = cls.objects.get(en=en)
        except:
            brand = cls(en=en).save()

        return brand
