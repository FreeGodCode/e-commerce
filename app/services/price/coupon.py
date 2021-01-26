# -*- coding: utf-8  -*-
# @Author: ty
# @File name: coupon.py 
# @IDE: PyCharm
# @Create time: 1/26/21 5:34 PM
# @Description: 优惠卷
from app.config.enum import COUPON_TYPES


class CouponConflict(Exception):
    pass


class CouponList(object):
    """implement some ugly validations for coupon usage"""
    # 冲突对
    CONFLICT_PAIRS = ((COUPON_TYPES.FREE_SHIPPING, COUPON_TYPES.SHIPPING_DEDUCTION),)

    def __init__(self):
        self.coupons = []
        self.types = []
        self.codes = []
        self.conflicts = []

    def add(self, coupon):
        if coupon.code in self.codes:
            raise CouponConflict('优惠卷已存在')

        coupon_type = coupon.coupon_type
        if coupon_type in self.conflicts:
            raise CouponConflict()
        if coupon_type == COUPON_TYPES.PERCENT_DEDUCTION and COUPON_TYPES.AMOUNT_DEDUCTION in self.types:
            i = self.types.index(COUPON_TYPES.AMOUNT_DEDUCTION)
            self.coupons.insert(i, coupon)
            self.types.insert(i, coupon_type)
        else:
            self.coupons.append(coupon)
            self.types.append(coupon_type)

        self.codes.add(coupon.code)
        for pair in self.CONFLICT_PAIRS:
            if coupon_type in pair:
                self.conflicts |= set(pair)

    def __iter__(self):
        return self.coupons.__iter__()

    def __len__(self):
        return len(self.coupons)

    def __getitem__(self, item):
        return self.coupons[item]

    def __delitem__(self, key):
        del self.coupons[key]

    def __add__(self, other):
        return self.coupons + other.coupons
