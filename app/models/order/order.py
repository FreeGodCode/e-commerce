# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order.py 
# @IDE: PyCharm
# @Create time: 1/12/21 11:30 AM
# @Description:
import datetime
import random
from copy import deepcopy

from flask import abort, current_app
import mongoengine
from flask_login import current_user
from mongoengine import queryset_manager, Q
from paypalrestsdk import Refund

from app import db, mongo_inventory
from app.config.enum import ORDER_TYPE, ORDER_STATUS, ORDER_SOURCES, PAYMENT_STATUS, PAYMENT_TYPE, LOG_STATUS
from app.models.cart.cart import CartEntry
from app.models.inventory.item import Item, ItemSpec
from app.models.inventory.price import ForexRate
from app.models.order.entry import OrderEntry
from app.models.order.logistic import LogisticDetail, payment_received, order_logistic_status_changed, \
    order_status_changed, order_created
from app.models.reward.coin import Trade
from app.models.user.address import Address
from app.models.user.user import User

__all__ = ['Order', 'Payment', 'TransferOrderCode', 'OrderExtra']

from app.services.notification import notification_order
from app.services.price import cal_order_price_and_apply, cal_order_tax
from app.utils import format_date


def check_availability_and_update_stock(item_id, sku, quantity):
    """

    :param item_id:
    :param sku:
    :param quantity:
    :return:
    """
    item = mongo_inventory.db.item.find_one({'_id': item_id})
    if not item['availability']:
        return False
    if quantity <= 0:
        return False

    spec = mongo_inventory.db.item_spec.find_one({'_id': sku, 'stock': -1})
    if spec:
        return spec['availability']

    spec = mongo_inventory.db.item_spec.find_and_modify(
        query={'_id': sku, 'stock': {'$gt': quantity - 1}, 'availability': True},
        update={'$inc': {'stock': -quantity}},
        new=True
    )
    if not spec:
        return False

    if spec['stock'] == 0:
        spec['availability'] = False
        mongo_inventory.db.item_spec.save(spec)
        update_item_availability(item_id)

    return True


def update_item_availability(item_id):
    """

    :param item_id:
    :return:
    """
    item = Item.objects(item_id=item_id, availability=True).first()
    if not item:
        return None
    for spec in item.specs:
        if spec.availability:
            return

    item.update(set__availability=False, set__status='DEL')


class Order(db.Document):
    """"""
    meta = {
        'db_alias': 'db_order',
        'ordering': ['-created_at'],
        'indexes': ['customer_id', 'status', 'address', 'amount', 'final', 'order_type', 'is_paid',
                    'is_payment_abnormal', 'refund_entries'],
    }
    created_at = db.DateTimeField(default=datetime.datetime.utcnow, required=True)
    order_type = db.StringField(choices=ORDER_TYPE, default=ORDER_TYPE.COMMODITY)
    # one day
    expired_in = db.IntField(default=1440)  # in minutes
    payment_expired_in = db.IntField(default=1440)
    short_id = db.SequenceField(required=True, unique=True)
    is_vip = db.BooleanField(default=False)
    status = db.StringField(max_length=256, required=True, choices=ORDER_STATUS, default=ORDER_STATUS.PAYMENT_PENDING)
    status_modified = db.DateTimeField()
    source = db.StringField(choices=ORDER_SOURCES)
    is_rewards_given = db.BooleanField(default=False)

    # order detail
    amount_usd = db.FloatField(default=0)
    amount = db.FloatField(default=0)

    discount = db.ListField(db.DictField())
    # 优惠卷兑换码
    coupon_codes = db.ListField(db.StringField())
    coin = db.IntField()
    lucky_money = db.IntField()
    cash = db.IntField()
    final = db.FloatField(required=True)
    # 库存
    logistic_provider = db.StringField()
    # 预估退税
    estimated_tax = db.FloatField(default=0)
    real_tax = db.FloatField(default=-1)
    paid_tax = db.FloatField(default=-1)

    # for internal usage
    # 汇率
    forex = db.FloatField()
    real_shipping = db.FloatField()
    cn_shipping = db.FloatField(default=0)
    address = db.ReferenceField('Address')
    customer_id = db.ObjectIdField(required=True)
    is_new_customer = db.BooleanField(default=False)
    entries = db.ListField(db.ReferenceField('OrderEntry', reverse_delete_rule=mongoengine.PULL))
    extra = db.StringField()

    logistics = db.ListField(db.ReferenceField('Logistic'))  # 库存
    closed_logistics = db.ListField(db.ReferenceField('Logistic'))

    is_paid = db.BooleanField(default=False)  # 是否支付
    is_payment_abnormal = db.BooleanField(default=False)  # 是否支付异常
    paid_date = db.DateTimeField()  # 支付时间
    pay_tax_deadline = db.DateTimeField()  # 支付税截至时间

    refund_entries = db.ListField(db.ReferenceField('OrderEntry', reverse_delete_rule=mongoengine.PULL))
    refund_amount = db.FloatField(default=0)
    is_test = db.BooleanField(default=False)

    fields_to_log = {
        'status', 'amount', 'coin', 'final', 'estimated_tax', 'real_tax', 'paid_tax', 'real_shipping', 'is_paid',
    }
    # 处理中的状态
    PROCESSING_STATUS = [ORDER_STATUS.PAYMENT_RECEIVED, ORDER_STATUS.SHIPPING]
    # 异常状态
    ABNORMAL_STATUS = [ORDER_STATUS.CANCELLED, ORDER_STATUS.ABNORMAL, ORDER_STATUS.ORDER_DELETE, ORDER_STATUS.EXPIRED,
                       ORDER_STATUS.REFUNDED]

    def __unicode__(self):
        return '%s' % self.sid

    def __str__(self):
        return '{}'.format(self.id)

    @classmethod
    def get_order_or_404(cls, order_id, check_user=True):
        try:
            order = cls.objects(id=order_id).first_or_404()
        except mongoengine.ValidationError:
            try:
                short_id = int(order_id)
            except (ValueError, TypeError):
                abort(404)
            order = cls.objects(short_id=short_id).first_or_404()

        if check_user and str(order.customer_id) != str(current_user.id):
            abort(404)

        return order

    @queryset_manager
    def commodities(doc_cls, queryset):
        return queryset.filter(order_type=ORDER_TYPE.COMMODITY, status__nin=doc_cls.ABNORMAL_STATUS)

    @queryset_manager
    def transfer(doc_cls, queryset):
        return queryset.filter(order_type=ORDER_TYPE.TRANSFER, status__nin=doc_cls.ABNORMAL_STATUS)

    @queryset_manager
    def processing(doc_cls, queryset):
        return queryset.filter(status__in=doc_cls.PROCESSING_STATUS)

    @queryset_manager
    def payment_pending(doc_cls, queryset):
        return queryset.filter(status=ORDER_STATUS.PAYMENT_PENDING)

    @queryset_manager
    def abnormal(doc_cls, queryset):
        return queryset.filter(Q(status__in=doc_cls.ABNORMAL_STATUS) | Q(refund_entries__0__exists=True) & Q(
            status__in=doc_cls.PROCESSING_STATUS + [ORDER_STATUS.RECEIVED]))

    @queryset_manager
    def received(doc_cls, queryset):
        return queryset.filter(status=ORDER_STATUS.RECEIVED)

    @queryset_manager
    def is_processing(self):
        return self.status in self.PROCESSING_STATUS

    @queryset_manager
    def is_payment_pending(self):
        return self.status == ORDER_STATUS.PAYMENT_PENDING

    @queryset_manager
    def is_abnormal(self):
        if self.status in self.ABNORMAL_STATUS:
            return True
        if self.status in self.PROCESSING_STATUS or self.status == ORDER_STATUS.RECEIVED:
            return len(self.refund_entries) > 0
        return False

    def has_refund_entries(self):
        if self.status in (self.PROCESSING_STATUS + [ORDER_STATUS.RECEIVED, ORDER_STATUS.REFUNDED]):
            return len(self.refund_entries) > 0
        return False

    @property
    def tax(self):
        if self.real_tax == -1:
            return self.estimated_tax
        else:
            return self.real_tax

    @property
    def shipping(self):
        return self.cn_shipping

    @property
    def estimated_weight(self):
        return sum(float(entry.item_snapshot.weight) * entry.quantity for entry in self.entries)

    @property
    def pay_tax_remain_days(self):
        if self.pay_tax_deadline:
            time_remain = self.pay_tax_deadline.date() - datetime.date.today()
            if time_remain.days > 0:
                return time_remain.days

    @property
    def latest_logistic(self):
        attr = LogisticDetail.attr_by_log_status.get(self.status)
        if not attr:
            return None
        return max(self.logistics, key=lambda l: getattr(l.detail, attr))

    @classmethod
    def create_transfer(cls, customer_id, entries, logistic_provider, coupon_codes, coin=0, cash=0, address=None,
                        **kwargs):
        order = cls(customer_id=customer_id, entries=entries, logistic_provider=logistic_provider,
                    coupon_codes=coupon_codes, coin=coin, cash=cash, **kwargs)
        if not order.forex:
            order.forex = ForexRate.get()

        order.update_amount()
        order.reload()
        if address:
            order.set_address(address)

        order_created.send('system', order=order)

        return order

    @classmethod
    def create_from_skus(cls, customer_id, skus, logistic_provider, coupon_codes, coin=0, cash=0, address=None,
                         **kwargs):
        entries = []
        for s in skus:
            availability = check_availability_and_update_stock(s['item_id'], s['sku'], s['quantity'])
            if not availability:
                return s
            spec = ItemSpec.objects(sku=s['sku']).first()
            item = Item.objects(item_id=['item_id']).first()
            entry = OrderEntry(spec=spec, item=item, quantity=s['quantity']).save()
            entries.append(entry)

        order = cls(customer_id=customer_id, entries=entries, logistic_provider=logistic_provider,
                    coupon_codes=coupon_codes, coin=coin, cash=cash, **kwargs)
        if not order.forex:
            order.forex = ForexRate.get()

        order.update_amount()
        order.reload()
        # 简介
        for e in order.entries:
            e.create_snapshot()

        if address:
            order.set_address(address)

        order_created.send('system', order=order)
        return order

    @classmethod
    def create(cls, customer_id, entries, logistic_provider, coupon_codes, coin=0, cash=0, address=None, **kwargs):
        order_entries = []
        for entry in entries:
            availability = check_availability_and_update_stock(entry.item_snapshot.item_id,
                                                               entry.item_spec_snapshot.sku, entry.quantity)
            if not availability:
                return entry
            if isinstance(entry, (CartEntry, OrderEntry)):
                e = deepcopy(entry)
                e.__class__ = OrderEntry
                e.id = None
                order_entries.append(e.save())

        order = cls(customer_id=customer_id, entries=order_entries, logistic_provider=logistic_provider,
                    coupon_codes=coupon_codes, coin=coin, cash=cash, **kwargs)
        if not order.forex:
            order.forex = ForexRate.get()

        order.update_amount()
        order.reload()
        for e in order.entries:
            e.create_snapshot()

        if address:
            order.set_address(address)

        order_created.send('system', order=order)
        return order

    @property
    def item_changed(self):
        res = False
        for e in self.entries:
            res = res and e.item_changed
            if res:
                return res
            return res

    def __get__(self, *args, **kwargs):
        order = super(Order, self).__get__(*args, **kwargs)
        if (not order.is_paid) and order.item_changed:
            order.update_entry()
            return order

    def update_entry(self):
        if self.is_paid:
            return
        map(lambda e: e.update_snapshot(), self.entries)
        self.update_amount()

    def set_address(self, addr):
        if not isinstance(addr, Address):
            addr = Address.objects(id=addr).first()
        if not addr:
            return False
        addr_snapshot = deepcopy(addr)
        addr_snapshot.id = None
        addr_snapshot.order_id = self.id
        addr_snapshot.save()
        if self.address:
            self.address.delete(w=1)
        self.address = addr_snapshot
        self.save()
        return True

    @property
    def customer(self):
        return User.objects(id=self.customer_id).first()

    def create_payment(self, ptype, trader):
        ptype = ptype.upper()
        self.update_entry()
        self.reload()
        if self.order_type != ORDER_TYPE.TRANSFER:
            is_available = self.check_entries_avaliable()
            if not is_available or self.status in ['CANCELLED', 'ABNORMAL', 'ORDER_DELETED', 'EXPIRED']:
                return None

        new_payment = Payment(order=self, ptype=ptype, trader=trader).save()
        return new_payment

    def get_payment(self, ptype):
        ptype = ptype.upper()
        payments = Payment.objects(order=self, ptype=ptype).order_by('-created_at')
        paid_payments = payments.filter(status=PAYMENT_STATUS.PAID)
        if paid_payments:
            return paid_payments.first()
        else:
            return payments.first()

    @property
    def goods_payment(self):
        return self.get_payment(PAYMENT_TYPE.WITHOUT_TAX)

    @property
    def tax_payment(self):
        return self.get_payment(PAYMENT_TYPE.WITH_TAX)

    @property
    def refunds(self):
        return Refund.objects(order=self)

    def check_entries_avaliable(self):
        availability = all(map(lambda e: e.is_available or e.item_spec_snapshot.stock != -1, self.entries))
        if not availability:
            self.status = ORDER_STATUS.EXPIRED
            self.save()
        return availability

    def set_paid(self):
        if self.is_paid:
            return
        self.is_new_customer = not bool(Order.objects(custom_id=self.customer_id, is_paid=True))
        self.is_paid = True
        self.status = ORDER_STATUS.PAYMENT_RECEIVED
        self.paid_date = datetime.datetime.utcnow()
        self.save()
        payment_received(self)

    def update_payment(self, paid_type, paid_amount, trader):
        if paid_type == PAYMENT_TYPE.WITHOUT_TAX and not self.is_paid and self.status in [ORDER_STATUS.PAYMENT_PENDING,
                                                                                          ORDER_STATUS.W]:
            if paid_amount == self.final and trader == PAYMENT_TRADERS.PAYPAL:
                self.set_paid()
            elif paid_amount == float('%.2f' % (self.final * self.forex)) and trader == PAYMENT_TRADERS.WEIXIN:
                self.set_paid()
            else:
                current_app.logger.error(
                    'error at updating payment. trader: {}; ptype: {}; amount: {} order id: {}'.format(trader,
                                                                                                       paid_type,
                                                                                                       paid_amount,
                                                                                                       self.id))
                self.is_payment_abnormal = True
        else:
            current_app.logger.error(
                'error at updating payment. trader: {}; ptype: {}; amount: {};  order id: {}'.format(trader, paid_type,
                                                                                                     paid_amount,
                                                                                                     self.id))
            self.is_payment_abnormal = True
        self.save()

    @property
    def coin_trades(self):
        return Trade.objects(reason_id=str(self.id))

    def update_logistic_status(self):
        if self.logistics:
            log_status = map(lambda m: m.detail.status, self.logistics)
            new_status = min(log_status, key=lambda l: LOG_STATUS.index(1))
            self._change_status(new_status)

    def _change_status(self, new_status):
        if self.status == new_status:
            return
        self.status = new_status
        self.status_modified = datetime.datetime.utcnow()
        self.save()

        if new_status in LOG_STATUS:
            notification_order(self, new_status)
            order_logistic_status_changed.send('Order.Logistic.Status.Changed', order=self,
                                                       new_status=new_status)
        else:
            order_status_changed.send('order_status_changed', order=self, new_status=new_status)

    def delete_order(self):
        for l in self.logistics:
            l.delete(w=1)

        for entry in self.entries:
            entry.delete(w=1)

        if self.goods_payment:
            self.goods_payment.delete(w=1)
        self.delete(w=1)

    def cancel_order(self, reason, status=None):
        """

        :param reason:
        :param status:
        :return:
        """
        for l in self.logistics:
            l.close(reason)

        self.extra = reason
        self.save()

        if not status:
            status = ORDER_STATUS.ABNORMAL
        self._change_status(status)
        for entry in self.entries:
            try:
                if entry.spec.stock != -1:
                    entry.spec.update(inc__stock=entry.quantity, set__availability=True)
                    entry.item.update(set__availability=True, set__status='MOD')

            except AttributeError:
                pass

    def update_amount(self):
        for e in self.entries:
            e.update_amount()
        cal_order_price_and_apply(self)
        self.estimated_tax = cal_order_tax(self)
        self.save()

    @property
    def sid(self):
        return self.short_id

    def to_json(self, include_logistic=False, replace_entries_to_refunded=False):
        if not self.is_paid:
            self.update_amount()
            self.reload()

        entries_json = []
        if replace_entries_to_refunded and self.has_refund_entries():
            for e in self.refund_entries:
                entries_json.append(e.to_json())
        else:
            for e in self.entries:
                entries_json.append(e.to_json())

        refund_entries_json = []
        for e in self.refund_entries:
            refund_entries_json.append(e.to_json())

        result = dict(
            id=str(self.id),
            short_id=str(self.sid),
            status=self.status,
            customer_id=str(self.customer_id),
            amount=self.amount,
            cn_shipping=self.cn_shipping,
            coin=self.coin,
            lucky_money=self.lucky_money,
            discount=self.discount,
            final=self.final,
            estimated_tax=self.estimated_tax,
            payment_status='PAID' if self.is_paid else 'UNPAID',
            payment_ref_number=[p.ref_number for p in Payment.objects(order=self)],
            created_at=format_date(self.created_at),
            entries=entries_json,
            refund_entries=refund_entries_json,
            refund_amount=self.refund_amount,
            real_tax=self.real_tax,
        )
        if self.address:
            result.update({'address': self.address.to_json()})
        if include_logistic:
            result.update(logistics=[l.to_json() for l in self.logistics])

        return result

    def to_grouped_json(self):
        """

        :return:
        """
        res = dict(
            estimated_weight=self.estimated_weight,
            amount=self.amount,
            cn_shipping=self.cn_shipping,
            coin=self.coin,
            lucky_money=self.lucky_money,
            discount=self.discount,
            final=self.final,
            extimated_tax=self.extimated_tax,
        )
        res['sid'] = self.id
        res['status'] = self.status
        if self.address:
            res.update(dict(address=self.address.to_json()))
        return res


class TransferOrderCode(db.Document):
    """"""
    order_id = db.ObjectIdField()
    code = db.StringField()

    @classmethod
    def set_order(cls, order_id):
        code = random.randint(100000, 999999)
        cls.objects(order_id=order_id).update_one(set__order_id=order_id, set__code=code, upsert=True)


class OrderExtra(db.Document):
    """"""
    meta = {
        'indexes': ['order', 'paid_date', 'device_id', 'client', 'version', 'client_channel']
    }
    order = db.ReferenceField('Order', unique=True)
    paid_date = db.DateTimeField()
    client = db.StringField()
    version = db.StringField()
    device_id = db.StringField()
    client_channel = db.StringField()


class Payment(db.Document):
    """"""
    meta = {
        'db_alias': 'db_order',
        'indexes': ['order', 'ptype', '-created_at'],
    }

    created_at = db.DateTimeField(default=datetime.datetime.utcnow(), required=True)
    order = db.ReferenceField('Order')
    logistic = db.ReferenceField('Logistic')

    other_reason = db.StringField()
    ptype = db.StringField(required=True, choices=PAYMENT_TYPE)
    status = db.StringField(max_length=256, required=True, choices=PAYMENT_STATUS, default=PAYMENT_STATUS.UNPAID)

    # transaction reference number from alipay/bank
    ref_number = db.StringField(max_length=128)
    paid_amount = db.FloatField()
    foreign_amount = db.FloatField()
    currency = db.StringField()
    buyer_id = db.StringField(max_length=50)
    trader = db.StringField(choices=PAYMENT_TRADERS)
    trade_type = db.StringField(choices=TRADE_TYPE)
    trade_status = db.StringField()
    trader_msg = db.StringField()
    extra = db.StringField()
    modified = db.DateTimeField()
    redirect_url = db.StringField()

    @property
    def is_paid(self):
        return self.status == PAYMENT_STATUS.PAID

    @property
    def amount(self):
        if self.ptype == PAYMENT_TYPE.WITHOUT_TAX:
            return self.order.final
        if self.ptype == PAYMENT_TYPE.WITH_TAX:
            return self.order.final + self.order_tax

    def mark_paid(self, data):
        if self.is_paid:
            return
        self.update(set__status=PAYMENT_STATUS.PAID)
        kwargs = {'set__' + key: value for key, value in data.items()}
        self.update(**kwargs)
        self.reload()
        paid_amount = float(data.get('paid_amount', 0))
        if self.ptype == PAYMENT_TYPE.WITHOUT_TAX:
            self.order.update_payment(self.ptype, paid_amount, self.trader)

    def to_json(self):
        return dict(id=self.id, ref_num=self.ref_number, status=self.status, type=self.type, amount=self.amount)
