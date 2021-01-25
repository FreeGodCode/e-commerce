# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order_status.py 
# @IDE: PyCharm
# @Create time: 1/25/21 11:56 AM
# @Description:
from app.models.order.order import Order
from app.models.order.order_status import OrderStatus
from app.services import celery


@celery.task
def update_user_status(user_id):
    """

    :param user_id:
    :return:
    """
    status, created = OrderStatus.objects.get_or_create(user_id=user_id)

    all_orders = Order.objects(customer_id=user_id)
    status.num_orders = all_orders.count()
    status.total = all_orders.sum('final')

    received_orders = Order.received(customer_id=user_id)
    status.received = received_orders.sum('final')

    status.num_unpaid = Order.payment_pending(customer_id=user_id).count()

    processing = Order.processing(customer_id=user_id)
    status.num_waiting = processing.count()

    status.save()
