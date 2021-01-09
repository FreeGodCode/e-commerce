# -*- coding: utf-8  -*-
# @Author: ty
# @File name: init_admin.py
# @IDE: PyCharm
# @Create time: 1/9/21 7:14 PM
# @Description:
from app import admin


def init_admin(app):
    """
    # 初始化后台
    :param app:
    :return:
    """
    # flask-admin
    admin.name = 'Maybe后台'
    admin.base_template = 'admin/master.html'
    admin.template_mode = 'bootstrap3'
    admin.init_app(app)
    admin.index_view = IndexView(name='Dashboard')