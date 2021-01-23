# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:36 PM
# @Description:
from app.config.enum import ORDER_TYPE, COIN_TYPE
from app.models.order.order import Order


def payment_received(order):
    """

    :param order:
    :return:
    """
    if order.order_type != ORDER_TYPE.TRANSFER:
        order = logistic_provider_dispatcher(order)
    else:
        for logistic in order.logistics:
            logistic.update_logistic({'status': 'PAYMENT_RECEIVED'})

    jobs.order_status.update_user_status(user_id=order.customer_id)
    notification_order(order, 'PAYMENT_RECEIVED')
    signals.payment_received.send('received', order=order)

@signals.payment_received.connect
def post_payment_ops(sender, order):
    coin_wallet = order.customer.coin_wallet
    wallet = order.customer.wallet
    if order.coin:
        coin_wallet.pay(order, order.coin, coin_type=COIN_TYPE.COIN)
        coin_wallet.reload()
    if order.cash:
        coin_wallet.pay(order, order.cash, coin_type=COIN_TYPE.CASH)
        coin_wallet.reload()
    for code in order.coupon_codes:
        wallet.user_consumable_coupon(code)
        wallet.reload()

    for order in Order.objects(customer_id=str(order.customer_id),)


