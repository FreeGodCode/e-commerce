# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:26 PM
# @Description: 优惠卷
from app.models.coupon import coupon, wallet


def all():
    result = []
    models = [coupon, wallet]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
