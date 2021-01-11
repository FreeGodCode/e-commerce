# -*- coding: utf-8  -*-
# @Author: ty
# @File name: permission.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:45 PM
# @Description:
__all__ = ['BackendPermission', 'Role']

from app import db


class BackendPermission(db.Document):
    """"""
    meta = {
        'indexes': ['name'],
    }
    name = db.StringField(required=True, unique=True)
    roles = db.ListField(db.ReferenceField('Role'))


class Role(db.Document):
    """"""
    name = db.StringField(max_length=128, unique=True)
    description = db.StringField(max_length=256)

    def __unicode__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other or self.name == getattr(other, 'name', None)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)
