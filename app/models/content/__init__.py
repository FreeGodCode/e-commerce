# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 10:25 PM
# @Description:
from app.models.content import banner, board, post


def all():
    result = []
    models = [banner, board, post]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
