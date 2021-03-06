# -*- coding: utf-8  -*-
# @Author: ty
# @File name: price.py 
# @IDE: PyCharm
# @Create time: 1/26/21 5:34 PM
# @Description: 价格
from flask_login import current_user

from app.config.enum import ORDER_SOURCES, ORDER_TYPE
from app.config.price import PRICE_FN
from app.models.inventory.item import ItemSpec, Item
from app.models.inventory.price import ForexRate
from app.models.order.partner import LogisticProvider, ChannelProvider


class FakeEntry(object):
    def __init__(self, spec, item, quantity):
        """
        WTF
        :param spec:
        :param item:
        :param quantity:
        """
        self.id = '{}-{}-{}'.format(item.item_id, spec.sku, quantity)
        self.spec = spec
        self.item = item
        self.item_snapshot = item
        self.item_spec_snapshot = spec
        self.quantity = quantity
        self.unit_price = self.spec.price
        self.amount_usd = self.unit_price * self.quantity
        self.amount = self.unit_price * self.quantity * ForexRate.get()
        self.discount = []

    def update_amount(self):
        return

    def save(self):
        return

    def reload(self):
        return


class FakeCart(object):
    """"""

    def __init__(self, entries_info, user=None, logistic_provider=None, address=None):
        entries = []
        for info in entries_info:
            spec = ItemSpec.objects(sku=info['sku'].first())
            if not spec or not spec.availability:
                continue

            item = Item.objects(item_id=info['item_id']).first()
            if not item or not item.availability:
                continue

            entry = FakeEntry(spec=spec, item=item, quantity=info['quantity'])
            entries.append(entry)
        for entry in entries:
            entry.update_amount()

        self.entries = entries
        self.customer = user
        self.logistic_provider = logistic_provider
        self.address = address
        self.coupon_codes = []
        self.coin = 0
        self.cash = 0
        self.id = 'fakecart'


def cal_order_price_and_apply(order):
    """

    :param order:
    :return:
    """
    order_proxy = cal_order_price(order, apply=True)


def cal_order_price(order, apply=True):
    for entry in order.entries:
        entry.update_amount()

    o = get_price_eval(order)

    for coupon in o.entry_coupons:
        cal_entries_discount(o, coupon)

    if apply:
        for entry in o.entries:
            entry.save()

    if not (hasattr(o, 'source') and order.source == ORDER_SOURCES.MANUALY or order.is_paid):
        o.forex = ForexRate.get()

    # here we get entries from order instand of o, because we need all entries
    o.amount_usd = sum(e.amount_usd for e in order.entries)
    o.amount = sum(e.amount for e in order.entries)

    if o.amount_usd < 79:
        o.cn_shipping = cn_shipping(o)
    else:
        o.cn_shipping = 0

    o.final = PRICE_FN.FINAL.DEFAULT(o.amount_usd, o.cn_shipping)

    if apply:
        o.apply_base_price()

    for coupon in order.coupons:
        field, value, desc = cal_order_discount(o, coupon)
        if value:
            o.discount.append(
                {'field': field, 'value': value, 'desc': desc, 'coupon_code': coupon.code, 'source_type': 'coupon'})

    if getattr(o, 'coin', None):
        set_coin(o, o.coin)
        o.final -= o.coin * 0.02
        o.discount.append(
            {'field': 'final', 'value': o.coin * 0.02, 'source_type': 'coin', 'desc': '使用{}金币'.format(o.coin)})

    if getattr(o, 'cash', None):
        set_cash(o, o.cash)
        o.final -= o.cash
        o.discount.append({'field': 'final', 'value': o.cash, 'source_type': 'cash', 'desc': '使用{}现金'.format(o.cash)})

    if current_user and current_user.is_authenticated and USER_ROLE.TESTER in current_user.roles:
        o.final = 0.01
        o.is_test = True

    if apply:
        o.apply_discount()

    return o


def set_coin(order, amount):
    """

    :param order:
    :param amount:
    :return:
    """
    wallet = order.customer.coin_wallet
    amount = min(amount, wallet.balance)
    order.coin = amount
    return amount


def set_cash(order, amount):
    """

    :param order:
    :param amount:
    :return:
    """
    wallet = order.customer.coin_wallet
    amount = min(amount, order.final, wallet.cash)
    order.cash = amount
    return amount


def cn_shipping(order):
    """

    :param order:
    :return:
    """
    address = order.address
    country = address and address.country or 'CN'
    if getattr(order, 'order_type', None) == ORDER_TYPE.TRANSFER:
        weight = sum(logistic.detail.real_weight or 0 for logistic in order.logistics)
        return LogisticProvider.get_provider_shipping(order.logistic_provider, country, weight)
    else:
        return ChannelProvider.get_shipping(order.logistic_provider, country)


def order_weight(order):
    """

    :param order:
    :return:
    """
    return sum(entry_weight(entry) for entry in order.entries)


def entry_weight(entry):
    """

    :param entry:
    :return:
    """
    unit_weight = entry.item_snapshot.weight
    return float(unit_weight) * entry.quantity


def cal_order_discount(order, coupon):
    """

    :param order:
    :param coupon:
    :return:
    """
    field, value = PRICE_FN.ORDER_COUPON[coupon.coupon_type](order, coupon)
    order.final -= value
    return field, value, coupon.description


def cal_entries_discount(order, coupon):
    """

    :param order:
    :param coupon:
    :return:
    """
    for entry in order.entries:
        cal_entry_discount(entry, coupon)


def cal_entry_discount(entry, coupon):
    """

    :param entry:
    :param coupon:
    :return:
    """
    field, value = PRICE_FN.ENTRY_COUPON[coupon.coupon_type](entry, coupon)
    entry.discount.append({'field': field, 'value': value, 'desc': coupon.description})
    if field == 'amount':
        entry.amount -= value
