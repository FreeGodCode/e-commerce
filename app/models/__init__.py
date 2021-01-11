# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/9/21 5:05 PM
# @Description:
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
