# -*- coding: utf-8  -*-
# @Author: ty
# @File name: enum.py 
# @IDE: PyCharm
# @Create time: 1/7/21 11:23 AM
# @Description:
class Enum(list):
    """enumeration 枚举"""

    def __getattr__(self, item):
        if item in self:
            return item
        raise AttributeError

    def __add__(self, other):
        result = super(Enum, self).__add__(other)
        return Enum(result)


class TupleEnum(list):
    """"""

    def __getattr__(self, item):
        keys = [k for k, v in self]
        if item in keys:
            return item
        raise AttributeError

    def __add__(self, other):
        result = super(TupleEnum, self).__add__(other)
        return TupleEnum(result)

    def __contains__(self, item):
        keys = [k for k, v in self]
        return item in keys


class DictEnum(dict):
    """"""
    __getattr__ = lambda self, k: DictEnum(self.get(k)) if type(self.get(k)) is dict else self.get(k)


# user
USER_GENDER = Enum(['M', 'F'])
USER_ROLE = Enum(['MEMBER', 'ADMIN', 'CUSTOMER_SERVICE', 'OPERATION', 'MARKETING', 'TESTER', 'LOGISTIC'])
USER_STATUS = Enum(['ACTIVE', 'INACTIVE', 'NEW'])

# item
ITEM_STATUS = Enum(['NEW', 'MOD', 'DEL'])
SEX_TAG = Enum(['MEN', 'WOMEN', 'GIRLS', 'BOYS', 'INFANTS', 'TODDLERS', 'MOMS', 'UNCLASSIFIED', 'UNKNOWN'])

# order
# 商品订单, 运输订单两类
ORDER_TYPE = Enum(['COMMODITY', 'TRANSFER'])
PAYMENT_METHODS = Enum(['WEIXIN', 'PAYPAL'])
PAYMENT_TYPE = Enum(['WITHOUT_TAX', 'WITH_TAX'])
PAYMENT_STATUS = Enum(['UNPAID', 'PAID'])
LOG_STATUS = Enum(['PENDING_REVIEW', 'TRANSFER_APPROVED', 'WAREHOUSE_IN', 'PAYMENT_RECEIVED', 'PROCESSING', 'SHIPPING',
                   'PORT_ARRIVED', 'RECEIVED', 'PENDING_RETRUN', 'RETURNED'])
ORDER_STATUS = Enum(['PAYMENT_PENDING', 'CANCELLED', 'ABNORMAL', 'DELETE', 'EXPIRED', 'REFUNDED'] + LOG_STATUS)
ORDER_SOURCES = Enum(['WECHAT', 'IOS', 'ANDROID', 'MANUALLY'])  # 人工
CURRENCY = Enum(['USD', 'HKD', 'CNY'])

# coupon
COUPON_SCOPE = Enum(['ORDER', 'ENTRY'])
COUPON_TYPES = Enum(['NORMAL', 'AMOUNT_DEDUCTION', 'PERCENT_DEDUCTION', 'FINAL_PERCENT_DEDUCTION', 'FREE_SHIPPING',
                     'SHIPPING_DEDUCTION', ])
COUPON_APPLY = Enum(['AUTO', 'BY_CODE', 'BY_DISPLAY_ID'])

# tags
TAG_TYPES = TupleEnum([
    ('CATEGORY', ''),
    ('MATERIAL', ''),
    ('ELEMENT', ''),
    ('STYLE', ''),
])

# coin
COIN_ONETIME_TASK = Enum(['VERIFIED_ID'])
COIN_REPEAT_TASK = Enum(['SHARED', 'SECOND_SHARED', 'SHARED_ORDER', 'ORDER'])
COIN_TASK = COIN_REPEAT_TASK + COIN_ONETIME_TASK
COIN_TRADE_REASON = Enum(
    ['PAY', 'OTHER', 'CANCEL', 'WITHDRAW', 'CUSTOMS', 'SHIPPING_FEE', 'PROMOTE', 'REFUND', 'CONVERT'] + COIN_TASK)
COIN_TRADE_TYPE = Enum(['INCOME', 'OUTCOME'])
COIN_TYPE = Enum(['COIN', 'CASH'])

# notification通知
NOTIFICATION_TYPE = Enum(
    ['SYSTEM', 'COMMENT', 'FOLLOW', 'SHIPPING_DELAYED', 'LOGISTIC_DELAYED', 'ORDER_REFUNDED', 'ADMIN_ORDER_PAID',
     'DAILY_ORDER_REPORT', 'USER_SIGNUP', 'POST_LIKED', 'REPLY', ] + ORDER_STATUS)

# notification channels 通知渠道
CHANNELS = Enum(['EMAIL', 'SMS', 'VOICE', 'WECHAT', 'WECHATFORMAL', 'IOS', 'NODEJS'])
QUEUE = Enum(['HIGH', 'NORMAL', 'LOW'])

# refunds 退款
REFUND_TYPE = Enum(['CANCEL', 'RETURN', 'SUBSIDY', 'MANUALLY'])

# report
REPORT_TYPE = Enum(['ORDER', 'LOGISTIC', 'ORDER_SOURCE', 'EXPENDITURE', 'IOS_SIGNUP_SOURCE', 'SHARE_LOG', 'REFUND'])

# post
POST_STATUS = Enum(['NEW', 'MOD', 'DEL'])
ACTIVITY_STATUS = Enum(['PENDING', 'PROCESSING', 'REFUSED'])
POST_TAG_TYPES = Enum(['TRADE', 'SERVICE', 'SHOW', 'UNCLASSIFIED'])
