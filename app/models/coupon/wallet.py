# -*- coding: utf-8  -*-
# @Author: ty
# @File name: wallet.py 
# @IDE: PyCharm
# @Create time: 1/16/21 9:48 PM
# @Description:
import datetime

from app import db
from app.config.enum import COUPON_APPLY
from app.models.coupon.coupon import Coupon

__all__ = ['ConsumableCoupon', 'CouponWallet']


class ConsumableCoupon(db.EmbeddedDocument):
    """"""
    code = db.StringField(required=True)
    number = db.IntField(default=1)

    @property
    def coupon(self):
        return Coupon.objects(code=self.code).first()

    @property
    def is_expired(self):
        return self.coupon.is_expired

    def to_json(self):
        if not self.coupon:
            return None
        res = self.coupon.to_json()
        res['number'] = self.number
        res['display_code'] = res['code']
        return res


class CouponWallet(db.Document):
    meta = {
        'db_alias': 'db_order',
        'indexes': ['consumable_coupons.code']
    }
    consumable_coupons = db.EmbeddedDocumentListField('ConsumableCoupon')
    coupons = db.ListField(db.StringField())
    coins = db.IntField(required=True, default=0)

    def add_consumable_coupon(self, code, number):
        coupon = Coupon.objects(code=code, apply=COUPON_APPLY.BY_DISPLAY_ID).first()
        if not coupon:
            return
        c = ConsumableCoupon(code=code, number=number)
        self.update(push__consumable_coupons=c)
        Signals.coupon_received.send(self, wallet=self, coupon=coupon)
        return coupon

    def get_consumable_coupon(self, code):
        try:
            coupon = self.consumable_coupons.get(code=code)
            return coupon
        except:
            return None

    def has_consumable_coupon(self, code):
        c = self.get_consumable_coupon(code)
        if c and not c.is_expired:
            return True
        return False

    def has_coupon(self, coupon):
        for c in self.consumable_coupons:
            if c.code == coupon.code and not c.is_expired:
                return True
            return False

    def use_consumable_coupon(self, code):
        if not code:
            return
        try:
            coupon = self.consumable_coupons.get(code=code)
        except:
            return

        if coupon.is_expired:
            return

        if coupon.number > 1:
            coupon.number -= 1
        else:
            self.consumable_coupons.remove(coupon)

        self.save()

    def clear_expired_coupon(self):
        for c in self.consumable_coupons:
            if datetime.datetime.utcnow() >= c.coupon.expire_date + datetime.timedelta(days=31):
                self.consumable_coupons.remove(c)

        self.save()

    def to_json(self):
        cc = [c.to_json() for c in self.consumable_coupons]
        return dict(consumable_coupon=cc, coupon=self.coupons)
