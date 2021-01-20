# -*- coding: utf-8  -*-
# @Author: ty
# @File name: log.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:37 PM
# @Description: 物流
from app.models.log import log


def all():
    result = []
    models = [log]
    for model in models:
        result += model.__all__

    return result


__all__ = all()
