# -*- coding: utf-8  -*-
# @Author: ty
# @File name: vendor.py 
# @IDE: PyCharm
# @Create time: 1/17/21 5:29 PM
# @Description: 供应商
from app import db

__all__ = ['Vendor']


class Vendor(db.Document):
    """供应商"""
    name = db.StringField(required=True, unique=True)
    cn_name = db.StringField()
    logo = db.StringField()
    desc = db.StringField()
    country = db.StringField(default='China')
    url = db.StringField()

    @classmethod
    def get_or_create(cls, name):
        vendor = cls.objects(name=name).first()
        if not vendor:
            vendor = cls(name=name).save()
        return vendor

    def to_json(self):
        return dict(name=self.name, cn_name=self.cn_name, logo=self.logo, desc=self.desc, country=self.country,
                    url=self.url)
