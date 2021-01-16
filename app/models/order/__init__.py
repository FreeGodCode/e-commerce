# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:25 PM
# @Description: 订单
from app.models.order import entry, express, logistic, order, order_status, partner, snapshot


def all():
    result = []
    models = [entry, express, logistic, order, order_status, partner, snapshot]
    for model in models:
        result += model.__all__
    return result


__all__ = all()
