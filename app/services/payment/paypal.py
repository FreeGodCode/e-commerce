# -*- coding: utf-8  -*-
# @Author: ty
# @File name: paypal.py 
# @IDE: PyCharm
# @Create time: 1/26/21 11:23 AM
# @Description:
import datetime

import paypalrestsdk as paypalrestsdk
from flask import url_for, current_app, abort

from app.services.payment.config import PAYPAL_LIVE


def init_paypal():
    """

    :return:
    """
    paypalrestsdk.configure(**PAYPAL_LIVE)
    return paypalrestsdk


def create_webprofile():
    """

    :return:
    """
    paypalapi = init_paypal()
    web_profile = paypalapi.WebProfile({
        'name': 'maybe',
        'presentation': {
            'brand_name': 'maybe shop',
            'logo_image': 'http://assets.maybe.cn/logo/maybe.jpg',
            'locale_code': 'zh-CN',
        },
        'input_fields': {
            'allow_note': False,
            'no_shipping': 1,
            'address_override': 1
        },
    })
    if web_profile.create():
        print('Web Profile[%s] created successfully' % (web_profile.id))
        return web_profile.id
    else:
        print('web_profile.error')
        return None


def paypal_checkout(order, ptype):
    """

    :param order:
    :param ptype:
    :return:
    """
    subject = 'maybe order %s ' % str(order.short_id)

    paypalapi = init_paypal()
    payment = paypalapi.Payment({
        'intent': 'sale',
        'experience_profile_id': '',
        'payer': {
            'payment_method': 'paypal',
        },
        'redirect_urls': {
            'return_url': url_for('payment.paypal_success', _external=True),
            'cancel_url': url_for('payment.paypal_cancel', _external=True),
        },
        'transaction': [{
            'amount': {
                'total': '%.2f' % order.final,
                'currency': 'USD',
            },
            'description': subject,
        }]
    })
    if payment.create():
        print('Payment [%s] created successfully' % (payment.id))
        obj = create_payment(order.ptype, payment)
    else:
        print('Error while creating payment:')
        print(payment.error)
        current_app.logger.error(payment.error)

    return payment, obj


def create_payment(order, ptype, payment):
    """
    redirect the user to given approval url
    :param order:
    :param ptype:
    :param payment:
    :return:
    """
    for link in payment.links:
        if link.method == 'REDIRECT':
            redirect_url = str(link.href)
            print('redirect for approval: %s' % redirect_url)

        obj = order.create_payment(ptype, PAYMENT_TRADERS.PAYPAL)
        obj.redirect_url = redirect_url
        obj.ref_number = payment.id
        obj.save()
        return obj


def paypal_update_payment(pending_payment, payer_id):
    """

    :param pending_payment:
    :param payer_id:
    :return:
    """
    try:
        paypalapi = init_paypal()
        payment = paypalapi.Payment.find(pending_payment.ref_number)
    except paypalrestsdk.exceptions.ResourceNotFound:
        abort(404)

    if payment.status == 'approved' and pending_payment.ref_number == payment.id:
        pay_date = datetime.datetime.utcnow()
        data = dict(
            paid_amount=float(payment.transactions[0].amount.total),
            currency=payment.transactions[0].amount.currency,
            buyer_id=payment.payer.payer_info.email,
            trade_status=payment.status.upper(),
            modified=pay_date,
        )
        pending_payment.mark_paid(data)
        return True
    else:
        current_app.logger.error(payment.error)
        return False
