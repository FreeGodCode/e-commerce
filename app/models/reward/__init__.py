# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/17/21 5:52 PM
# @Description:
from app.models.reward import coin


def all():
    result = []
    models = [coin]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
