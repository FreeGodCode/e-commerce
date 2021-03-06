# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:58 PM
# @Description:
from app.models.user import user, address, guest


def all():
    result = []
    models = [user, address, guest]
    for model in models:
        result += model.__all__
        return result


__all__ = all()
