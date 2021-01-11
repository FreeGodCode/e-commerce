# -*- coding: utf-8  -*-
# @Author: ty
# @File name: address.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:03 PM
# @Description:
from datetime import datetime

from app import db

__all__ = ['Address']


class Address(db.Document):
    """地址"""
    created_at = db.DateTimeField(default=datetime.utcnow)

    # address detail
    country = db.StringField(required=True)
    prov = db.StringField(required=True)
    city = db.StringField()
    street = db.StringField()
    postcode = db.StringField()

    # receiver information
    receiver = db.StringField(required=True)
    mobile_number = db.StringField()

    def __unicode__(self):
        return '%s' % str(self.id)
        # return '{}'.format(self.postcode)

    @property
    def fields(self):
        return ['country', 'prov', 'city', 'street', 'postcode', 'receiver', 'mobile_number']

    def to_json(self):
        result = {field: getattr(self, field) for field in self.fields}
        result.update({'id': str(self.id)})
        return result
