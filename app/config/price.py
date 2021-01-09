# -*- coding: utf-8  -*-
# @Author: ty
# @File name: price.py 
# @IDE: PyCharm
# @Create time: 1/9/21 4:36 PM
# @Description:
from math import ceil

from app.config.enum import DictEnum, COUPON_TYPES


def with_fx_rate(x, forex=None):
    """

    :param x:
    :param forex:
    :return:
    """
    if forex is None:
        forex = ForexRate.get()
        return ceil(x * forex)


PRICE_FN = DictEnum({
    'ORDER_COUPON': {
        COUPON_TYPES.AMOUNT_DEDUCTION: lambda o, c: ('final', min(o.final, int(c.value))),
        COUPON_TYPES.PERCENT_DEDUCTION: lambda o, c: ('amount_usd', int(o.amount_usd * float(c.value))),
        COUPON_TYPES.FINAL_PERCENT_DEDUCTION: lambda o, c: ('final', int(o.final * float(c.value))),
        COUPON_TYPES.SHIPPING_DEDUCTION: lambda o, c: ('cn_shipping', min(int(c.value), o.cn_shipping)),
    },
    'ENRTY_COUPON': {
        COUPON_TYPES.AMOUNT_DEDUCTION: lambda e, c: ('amount_usd', min(e.amount, float(c.value))),
        COUPON_TYPES.PERCENT_DEDCCTION: lambda e, c: ('amount_usd', e.amount * float(c.value)),
    },
    'FINAL': {
        'DEFAULT': lambda us_sale, cn_shipping: us_sale + cn_shipping,
        'WECHAT': lambda us_sale, shipping: us_sale + shipping,
        'IOS': lambda us_sale, shipping: us_sale + shipping,
    },
    'LOGISTIC': {
        'DEFAULT': lambda weight: 4.99 * float(weight)/500 + 9.99 if weight else 0,
    },
    'WITH_FX_RATE': with_fx_rate
})

# 物流价格
LOGISTIC_RATE = 0.085
# 利润率
MARGIN = 1.12
# 汇率
FOREX_RATE = 6.3

# 物价+物流费
COST_PRICE = lambda china_price, weight: china_price + LOGISTIC_RATE * weight
CURRENT_PRICE = lambda  cost_price: float(str(cost_price/FOREX_RATE * MARGIN).split('.')[0] + '.99')
ORIGIN_PRICE = lambda  price: float(str(price * 1.2).split('.')[0] + '.99')
