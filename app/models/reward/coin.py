# -*- coding: utf-8  -*-
# @Author: ty
# @File name: coin.py 
# @IDE: PyCharm
# @Create time: 1/17/21 5:53 PM
# @Description:  奖励金币
from datetime import datetime

from flask import current_app

from app import db
from app.config.enum import COIN_TRADE_REASON, COIN_TRADE_TYPE, COIN_TYPE
from app.models.user.user import User
from app.utils.utils import format_date

__all__ = ['CoinWallet', 'Trade', 'CoinTrade']


class CoinWallet(db.Document):
    """钱包"""
    meta = {
        'indexes': ['user']
    }
    # Field
    user = db.ReferenceField('User', unique=True)
    balance = db.IntField(required=True, default=0)
    holdding = db.IntField(required=True, default=0)
    cash = db.IntField(required=True, default=0)
    holdding_cash = db.IntField(required=True, default=0)
    latest_expired_time = db.DateTimeField(default=datetime(1989, 6, 3))

    @classmethod
    def create(cls, user, balance=0, holdding=0):
        wallet = cls.objects(user=user).modify(upsert=True, new=True, set__user=user, set__balance=balance,
                                               set__holdding=holdding)
        return wallet

    @classmethod
    def get_or_create(cls, user):
        wallet = CoinWallet.objects(user=user).first()
        if not wallet:
            wallet = CoinWallet.create(user=user)
        return wallet

    def pay(self, order, amount, coin_type=COIN_TYPE.COIN):
        if coin_type == COIN_TYPE.COIN and amount > self.balance:
            current_app.logger.error(
                'order coin exceed wallet balance. order: {}, amount: {}, balance: {}'.format(order.id, amount,
                                                                                              self.balance))
            amount = self.balance
        if coin_type == COIN_TYPE.CASH and amount > self.cash:
            current_app.logger.error(
                'order cash exceed balance. order: {}, amount: {}, balance: {}'.format(order.id, amount, self.cash))
            amount = self.cash

        time = datetime.utcnow()
        reason = COIN_TRADE_REASON.PAY
        kind = COIN_TRADE_TYPE.OUTCOME
        user = User.objects(id=order.customer_id).first()
        trade = CoinTrade.create(user=user, amount=amount, time=time, kind=kind, reason=reason, wallet=self,
                                 reason_id=str(order.id), coin_type=coin_type)
        return trade


class Trade(db.Document):
    """"""
    meta = {
        'db_alias': 'db_reward',
        'indexes': ['wallet', 'user', 'time', 'kind', 'reason_id', 'reason'],
        'ordering': ['wallet'],
        'allow_inheritance': True,
    }
    user = db.ReferenceField('User')
    wallet = db.ReferenceField('CoinWallet')
    amount = db.IntField(required=True)
    coin_type = db.StringField(choices=COIN_TYPE, default=COIN_TYPE.COIN)
    time = db.DateTimeField(required=True)
    kind = db.StringField(required=True, choices=tuple(COIN_TRADE_TYPE))
    reason = db.StringField(required=True, choices=tuple(COIN_TRADE_REASON))
    reason_id = db.StringField()
    description = db.StringField()
    is_hold = db.BooleanField()

    descs = {
        'PAY': '购买',
        'CANCEL': '取消订单',
        'SHIPPING_FEE': '返还运费',
        'PROMOTE': '参与活动',
        'WECHAT_LOGIN': '微信帐号登录',
        'IOS_APP': '下载手机客户端',
        'VERIFIED_ID': '上传身份证资料',
        'SHARED': '分享链接',
        'SECOND_SHARED': '你的链接被分享了',
        'SHARED_ORDER': '通过你的链接购买',
        'ORDER': '订单完成',
        'OTHER': '其他',
    }

    def clean(self):
        if not self.description:
            self.description = self.descs.get(self.reason, '')


class CoinTrade(Trade):
    """"""
    meta = {
        'indexes': ['wallet', 'kind', 'user', 'time', 'reason_id', 'reason'],
        'ordering': ['wallet'],
    }

    @classmethod
    def create(cls, user, amount, kind, reason, time=None, wallet=None, reason_id=None, coin_type=COIN_TYPE.COIN,
               description=None):
        if not user:
            return
        if not amount > 0:
            return
        if not wallet:
            wallet = CoinWallet.get_or_create(user=user)
        if time is None:
            time = datetime.utcnow()

        trade = cls(user=user, wallet=wallet, amount=amount, time=time, kind=kind, reason=reason,
                    reason_id=str(reason_id), coin_type=coin_type, description=description)
        trade.save()
        return trade

    @classmethod
    def post_save(cls, sender, document, created, **kwargs):
        if not created:
            return
        amount = document.amount if document.kind == COIN_TRADE_TYPE.INCOME else -1 * document.amount
        if document.coin_type == COIN_TYPE.COIN:
            document.wallet.update(inc__balance=amount)
        else:
            document.wallet.update(inc__cash=amount)

        Signals.coin_trade_confirmed.send('coin_trade_confirmed', trade=document)

    def to_json(self):
        return {
            'amount': self.amount,
            'coin_type': self.coin_type,
            'time': format_date(self.time),
            'kind': self.kind,
            'type': self.kind,
            'reason': self.reason,
            'reason_id': self.reason_id,
            'description': self.description or self.descs.get(self.reason, ''),
            'is_hold': False,
        }


db.post_save.connect(CoinTrade.post_save, sender=CoinTrade)
