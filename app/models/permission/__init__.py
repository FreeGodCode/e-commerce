# -*- coding: utf-8  -*-
# @Author: ty
# @File name: permission.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:45 PM
# @Description:
from app.models.permission import permission


def all():
    result = []
    models = [permission]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
