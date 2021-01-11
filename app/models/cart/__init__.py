# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:25 PM
# @Description: 购物车
from app.models.cart import cart


def all():
    result = []
    models = [cart]
    for model in models:
        result += model.__all__
    return result


__all__ = all()
