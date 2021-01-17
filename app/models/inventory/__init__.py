# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:25 PM
# @Description: 库存
from app.models.inventory import brand, category, item, statistics, tag, vendor, price


def all():
    result = []
    models = [brand, category, item, price, statistics, tag, vendor]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
