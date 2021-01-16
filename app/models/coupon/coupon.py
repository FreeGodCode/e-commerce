# -*- coding: utf-8  -*-
# @Author: ty
# @File name: coupon.py 
# @IDE: PyCharm
# @Create time: 1/16/21 9:22 PM
# @Description: 优惠卷
from datetime import datetime

from app import db
from app.config.enum import COUPON_SCOPE, COUPON_TYPES, COUPON_APPLY

__all__ = ['Coupon']


class Coupon(db.Document):
    meta = {
        'db_alias': 'db_order',
        'indexes': ['code', 'apply', 'expire_date', 'description'],
        'strict': False,
    }
    scope = db.StringField(required=True, choices=COUPON_SCOPE, default=COUPON_SCOPE.ORDER)
    coupon_type = db.StringField(default=COUPON_SCOPE.NORMAL, required=True, choices=COUPON_TYPES)
    value = db.FloatField()
    description = db.StringField()
    effective_date = db.DateTimeField(default=datetime.utcnow)
    expire_date = db.DateTimeField(default=datetime(2022, 12, 31))
    code = db.StringField(unique=True)

    apply = db.StringField(required=True, default=COUPON_APPLY.BY_DISPLAY_ID, choices=COUPON_APPLY)
    required_amount = db.FloatField(default=0)
    required_final = db.FloatField(default=0)
    required_new_order = db.BooleanField(default=False)
    once_per_user = db.BooleanField(default=False)

    note = db.StringField()
    coupon_category = db.StringField(choices=['PROMOTION', 'STAFF', 'NEW_USER'], default='PROMOTION')

    @property
    def is_expired(self):
        if not self.expire_date:
            return False
        return datetime.utcnow() >= self.expire_date

    def to_json(self):
        return dict(coupon_type=self.coupon_type,
                    value=self.value,
                    code=self.code,
                    effective_date=format_date(self.effective_date, '%Y-%m-%d'),
                    expire_date=format_date(self.expire_date, '%Y-%m-%d'),
                    is_expired=self.is_expired,
                    description=self.description,
                    )

    def is_effective(self):
        return self.effective_date <= datetime.utcnow() < self.expire_date

    def can_apply(self, order):
        res = bool(self.required_final <= order.final
                   and self.required_amount <= order.amount
                   and not (self.require_new_order and order.customer.orders)
                   and not (self.once_per_user and order.customer.used_coupon(self.code)))
        return res
