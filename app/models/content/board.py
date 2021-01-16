# -*- coding: utf-8  -*-
# @Author: ty
# @File name: board.py 
# @IDE: PyCharm
# @Create time: 1/16/21 5:19 PM
# @Description: 广播
from datetime import datetime

from app import db

__all__ = ['ChangeLog', 'Board']


class ChangeLog(db.EmbededDocument):
    """"""
    user = db.StringField()
    date = db.DateTimeField(required=True, default=datetime.utcnow)
    action = db.StringField()
    item = db.StringField()
    info = db.StringField()


class Board(db.Document):
    """广播"""
    meta = {
        'db_alias': 'db_content',
        'indexes': ['published_at', 'title'],
        'ordering': ['-published_at']
    }
    # 标题
    title = db.StringField(required=True)
    # 描述
    description = db.StringField()
    # 状态
    status = db.StringField(default='PENDING', choices=['PUBLISHED', 'PENDING'])
    # 广播类型
    board_type = db.StringField()

    items = db.ListField(db.StringField())
    # 图片
    image = db.StringField()
    # 作者
    author = db.StringField()
    # 参与者
    participants = db.ListField(db.StringField())
    # 浏览次数
    view_count = db.IntField(default=0)
    # 创建时间
    created_at = db.DateTimeField(default=datetime.utcnow)
    # 定义时间
    modified = db.DateTimeField()
    # 发布时间
    published_at = db.DateTimeField()
    # 过期时间
    expired_date = db.DateTimeField()

    def __unicode__(self):
        return '%s' % str(self.id)

    @classmethod
    def create(cls, user, board_type):
        """
        创建
        :param user:
        :param board_type:
        :return:
        """
        default_title = str(datetime.utcnow().date())
        board = Board(title=default_title, author=user, board_type=board_type, participants=[user])
        board._add_log(user, 'NEW')
        board.save()

    @classmethod
    def get_board(cls, board_id):
        return cls.objects(id=board_id).first()

    def add_item(self, user, item):
        """
        添加
        :param user:
        :param item:
        :return:
        """
        self._add_remove_item(user, 'ADD', item)

    def remove_item(self, user, item):
        """
        删除
        :param user:
        :param item:
        :return:
        """
        self._add_remove_item(user, 'REMOVE', item)

    def publish(self, user):
        """
        发布
        :param user:
        :return:
        """
        self.status = 'PUBLISHED'
        self.published_at = datetime.utcnow()
        self._add_log(user, 'PUBLISH')

    def unpublish(self, user):
        """
        未发布
        :param user:
        :return:
        """
        self.status = 'PENDING'
        self.published_at = None
        self._add_log(user, 'UNPUBLISH')

    def reorder_item(self, item, index):
        """

        :param item:
        :param index:
        :return:
        """
        self.items.remove(item)
        self.items.insert(index, item)

    def add_comment(self, user, comment):
        """

        :param user:
        :param comment:
        :return:
        """
        self._add_log(user, 'COMMENT', info=comment)

    def _add_remove_item(self, user, action, item):
        """

        :param user:
        :param action:
        :param item:
        :return:
        """
        if item not in self.items:
            self.items.append(item)
        else:
            self.items.remove(item)

        self._add_log(user, action, item)

    def _add_log(self, user, action, item=None, info=''):
        """
        添加日志
        :param user:
        :param action:
        :param item:
        :param info:
        :return:
        """
        if user not in self.participants:
            self.participants.append(user)

        self.logs.insert(0, ChangeLog(user=user, action=action, item=item, info=info))
        self.save()

    def to_json(self):
        return dict(id=str(self.id), date=str(self.published_at), image=self.image, desc=self.description,
                    title=self.title, )
