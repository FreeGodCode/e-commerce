# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order.py 
# @IDE: PyCharm
# @Create time: 1/25/21 5:05 PM
# @Description:
import itertools
import re

from app.config.enum import ORDER_TYPE
from app.config.order_status import ORDER_STATUS_DESCRIPTION, ROUTES
from app.models.order.express import ExpressTracking
from app.models.order.order import Payment
from app.models.order.partner import LogisticProvider
from app.services.json_templ.entry import transfer_entry_json, entry_json
from app.utils.utils import format_date


def simple_order_json(order):
    """

    :param order:
    :return:
    """
    if not order.is_paid:
        order.update_amount()
        order.reload()

    entries_json = []
    for entry in order.entries:
        if order.order_type == ORDER_TYPE.TRANSFER:
            entries_json.append(transfer_entry_json(entry))
        else:
            entries_json.append(entry_json(entry))

    refund_entries_json = []
    for entry in order.refund_entries:
        refund_entries_json.append(entry.to_json())

    result = dict(
        id=str(order.id),
        short_id=str(order.id),
        current_status=ORDER_STATUS_DESCRIPTION.get(order.status, ''),
        status=order.status,
        customer_id=str(order.customer_id),
        amount=order.amount,
        amount_usd=order.amount_usd,
        cn_shipping=order.cn_shipping,
        coin=order.coin,
        lucky_money=order.lucky_money,
        discount=order.discount,
        final=order.final,
        payment_status='PAID' if order.is_paid else 'UNPAID',
        payment_ref_number=[p.ref_number for p in Payment.objects(order=order)],
        created_at=format_date(order.created_at),
        entries=entries_json,
        refund_entries=refund_entries_json,
        refund_amount=order.refund_amount,
    )

    return result


def order_json(order):
    """

    :param order:
    :return:
    """
    if not order.is_paid:
        order.update_amount()
        order.reload()

    entries_json = []
    for entry in order.entries:
        if order.order_type == ORDER_TYPE.TRANSFER:
            entries_json.append(transfer_entry_json(entry))
        else:
            entries_json.append(entry_json(entry))

    refund_entries_json = []
    for entry in order.refund_entries:
        refund_entries_json.append(entry.to_json())

    provider_json = LogisticProvider.objects.get(name=order.logistic_provider, country=order.address.country).to_json()

    result = dict(
        id=str(order.id),
        short_id=str(order.id),
        status=order.status,
        customer_id=str(order.customer_id),
        amount=order.amount,
        amount_usd=order.amount_usd,
        cn_shipping=order.cn_shipping,
        coin=order.coin,
        lucky_money=order.lucky_money,
        discount=order.discount,
        final=order.final,
        estimated_tax=order.estimated_tax,
        payment_status='PAID' if order.is_paid else 'UNPAID',
        payment_ref_number=[p.ref_number for p in Payment.objects(order=order)],
        created_at=format_date(order.created_at),
        entries=entries_json,
        refund_entries=refund_entries_json,
        refund_amount=order.refund_amount,
        real_tax=order.real_tax,
        provider=provider_json,
        address='',
    )
    if order.address:
        result.update(dict(address=order.address.to_json()))

    if order.logistics:
        result.update(logistics=[logistic_json(logistic, order.order_type) for logistic in order.logistics])

    return result


def logistic_json(logistic, order_type):
    """

    :param logistic:
    :param order_type:
    :return:
    """
    if order_type == ORDER_TYPE.TRANSFER:
        entries = [transfer_entry_json(entry) for entry in logistic.entries]
    else:
        entries = [entry_json(entry) for entry in logistic.entries]

    all_status = [{'status': status, 'desc': ORDER_STATUS_DESCRIPTION.get(status, '')} for status in
                  ROUTES.get(logistic.detail.route, 'DEFAULT')]
    current_status = logistic.detail.status

    history = []
    for status in LOGISTIC_SATAUS:
        detail_field = logistic.detail.attr_by_log_status[status]
        value = getattr(logistic.detail, detail_field)
        if not value:
            continue
        history.append(dict(desc=SHIPPING_HISTORY[status], time=format_date(value) if value else '', ))
        if status == 'TRANSFER_APPROVED':
            history.append(dict(desc='', time=''))
        if status == 'WAREHOUSE_IN' and logistic.detail.real_weight > 0:
            history.append(dict(desc='包裹总总量: %s kg' % str(logistic.detail.real_weight / 1000), time='', ))

        # tracking information
        tracking = None
        if status == LOGISTIC_STATUS.SHIPPING and logistic.detail.cn_logistic_name:
            history.append(dict(desc='国际快递公司: %s' % logistic.detail.cn_logistic_name.upper(),
                                time='国际快递单号: %s' % logistic.detail.cn_tracking_no, ))
            tracking = ExpressTracking.find(company=logistic.detail.n_logistic_name,
                                            number=logistic.detail.cn_tracking_no)
        for d in (reversed(tracking.data) if tracking else []):
            desc = re.sub(r'\s{2, }', ' ', d.get('context', ''))
            history.append(dict(desc=desc, time=d.get('time', ''), ))

        if status == current_status:
            break

    if current_status in ['PENDING_RETURN', 'RETURNING', 'RETURNED']:
        current_status = 'PAYMENT_RECEIVED'

    return {
        'id': str(logistic.id),
        'entries': entries,
        'all_status': all_status,
        'current_status': current_status,
        'history': history,
        'partner_tracking_no': logistic.detail.partner_tracking_no,
    }


def order_price_json(order):
    """

    :param order:
    :return:
    """
    return dict(
        coin=getattr(order, 'coin', None) or 0,
        lucky_money=getattr(order, 'lucky_money', None) or 0,
        coupon_codes=order.coupon_codes,
        amount_usd=round(order.amount_usd, ndigits=2),
        cn_shipping=order.cn_shipping,
        discount=order.discount + list(itertools.chain.from_iterable(entry.discount for entry in order.entries)),
        final=round(order.final, ndigits=2),
    )


def transfer_order_price_json(order):
    entries_json = []
    for entry in order.entries:
        entries_json.append(transfer_entry_json(entry))

    provider_json = LogisticProvider.objects.get(name=order.logistic_provider, country=order.address.country).to_json()

    result = dict(
        id=str(order.id),
        short_id=str(order.sid),
        status=order.status,
        customer_id=str(order.customer_id),
        amount=order.amount,
        amount_usd=order.amount_usd,
        cn_shipping=order.cn_shipping,
        coin=order.coin,
        lucky_money=order.lucky_money,
        discount=order.discount,
        final=order.final,
        estimated_tax=order.estimated_tax,
        payment_status='PAID' if order.is_paid else 'UNPAID',
        created_at=format_date(order.created_at),
        entries=entries_json,
        refund_amount=order.refund_amount,
        real_tax=order.real_tax,
        provider=provider_json,
        address='',
    )

    if order.address:
        result.update(dict(address=order.address.to_json()))

    if order.logistics:
        result.update(dict(logistics=[logistic_json(logistic, order.order_type) for logistic in order.logistics]))

    return result
