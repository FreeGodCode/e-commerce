# -*- coding: utf-8  -*-
# @Author: ty
# @File name: banner.py 
# @IDE: PyCharm
# @Create time: 1/16/21 5:04 PM
# @Description: 轮播图
import datetime

from app import db

__all__ = ['Banner']

from app.models.content.board import Board
from app.utils.utils import format_date


class Banner(db.Document):
    """"""
    meta = {
        'db_alias': 'db_content',
        'indexes': ['published']
    }
    created_at = db.DateTimeField(default=datetime.datetime.utcnow, required=True)
    banner_type = db.StringField(default='BOARD', choices=['BOARD', 'URL'])
    target = db.StringField()
    img = db.StringField()
    date_from = db.DateTimeField(default=datetime.datetime.today())
    date_until = db.DateTimeField(default=datetime.datetime(2029, 12, 30))
    published = db.BooleanField(default=True)
    order = db.SequenceField()

    def __repr__(self):
        return '<Banner object: {}>'.format(str(self.id))

    @classmethod
    def get_latest(cls, n=10):
        now = datetime.datetime.now()
        docs = cls.objects(date_from__lte=now, date_until__gt=now).order_by('-order', '-created_at').limit(n)
        return docs

    @property
    def target_obj(self):
        if self.banner_type == 'BOARD':
            return Board.objects(id=self.target).first()
        return self.target

    def to_json(self):
        return {
            'type': self.banner_type,
            'target': self.target,
            'img': self.img,
            'created_at': format_date(self.created_at)
        }
