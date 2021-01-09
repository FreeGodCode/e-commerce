# -*- coding: utf-8  -*-
# @Author: ty
# @File name: init_hook.py
# @IDE: PyCharm
# @Create time: 1/9/21 7:13 PM
# @Description:
def init_hook(app, name):
    @app.before_request
    def before_request():
        pass