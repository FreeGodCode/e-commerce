# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/9/21 5:05 PM
# @Description:
from app.models import inventory, reward, content
from app.models.cart import cart
from app.models.coupon import coupon
from app.models.log import log
from app.models.order import order
from app.models.permission import permission
from app.models.user import user


def all():
    """

    :return:
    """
    result = []
    models = [user, permission, cart, coupon, inventory, order, reward, content, log]
    for model in models:
        result += model.__all__
    return result


__all__ = all()
