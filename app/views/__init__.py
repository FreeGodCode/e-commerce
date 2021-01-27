# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/9/21 5:05 PM
# @Description:
from app.views import website
from app.views.frontend import frontend

default_blueprints = [
    frontend.frontend,
]

default_blueprints.extend(website.website_blueprints)
