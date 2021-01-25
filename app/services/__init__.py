# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:33 PM
# @Description:
from app.ext_celery import make_celery

celery = make_celery()