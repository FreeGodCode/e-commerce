# -*- coding: utf-8  -*-
# @Author: ty
# @File name: express.py 
# @IDE: PyCharm
# @Create time: 1/15/21 12:07 AM
# @Description:
from datetime import datetime

from app import db

__all__ = ['Express', 'ExpressRequestLog', 'ExpressTracking', 'PartnerExpressTracking']

STATUS = {
    '1': '在途中',
    '2': '已揽收',
    '3': '已签收',
    '4': '退签',
    '5': '同城派运中',
    '6': '退回',
    '7': '转单',
}


class Express(db.Document):
    """快递"""
    meta = {
        'indexes': ['name']
    }
    name = db.StringField(unique=True)
    cn_name = db.StringField()
    logo_url = db.StringField()
    desc = db.StringField()

    def to_json(self):
        return dict(key=self.name, name=self.cn_name, logo=self.logo_url, desc=self.desc)


class ExpressRequestLog(db.Document):
    """"""
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    company = db.StringField()
    number = db.StringField()
    respond = db.DictField()
    is_success = db.BooleanField()


class ExpressTracking(db.Document):
    """快递轨迹"""
    company = db.StringField(required=True)
    number = db.StringField(required=True, unique_with='company')
    to = db.StringField()
    is_check = db.StringField(required=True, default='0')

    # 快递单当前签收状态, 包括: 0: 在途中,1:已揽收, 2: 疑难, 3: 已签收, 4: 退签, 5: 同城派送中, 6: 退回, 7: 转单等状态
    status = db.StringField()
    # dictionary in data
    # {
    #     'context': '', #内容
    #     'time': '',   #时间,原始格式
    #     'ftime': '',  #格式化时间
    #     'status': '', #状态
    #     'areaCode': '',   #地区编号
    #     'areaName': '',   #地名
    # }
    data = db.ListField(db.DictField())
    # time
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
    is_subscribed = db.BooleanField(default=False)
    modified = db.DateTimeField()
    retries = db.IntField(default=0)

    @classmethod
    def find(cls, company, number):
        cls.objects(company=company, number=number).update_one(set__company=company, set__number=number, upsert=True)
        return cls.objects.get(company=company, number=number)

    @classmethod
    def subscribed(cls, company, number):
        obj = cls.objects(company=company, number=number, is_subscribed=True)
        return True if obj else False

    @classmethod
    def update_info(cls, data):
        cls.objects(company=data['company'], number=data['number']).update_one(
            set__is_check=data['is_check'],
            set__status=STATUS.get(data['STATUS']),
            set__data=data['data'],
            set__modified=datetime.utcnow(),
            upsert=True)

    @property
    def is_checked(self):
        if self.is_check and self.is_check == '0':
            return False
        elif self.is_check == '1':
            return True

    @property
    def history(self):
        result = []
        for d in self.data:
            formated = {k: v for k, v in d.items() if k in ['ftime', 'context']}
            result.append(formated)
        return result

    def to_json(self):
        return dict(company=self.company, number=self.number, is_check=self.is_check, status=self.status,
                    data=self.data)


class PartnerExpressTracking(db.Document):
    """"""
    company = db.StringField()
    number = db.StringField(required=True, unique_with='company')
    data = db.ListField(db.DictField())
    created_at = db.DateTimeField(default=datetime.utcnow, required=True)
