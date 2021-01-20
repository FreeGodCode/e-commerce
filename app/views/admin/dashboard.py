# -*- coding: utf-8  -*-
# @Author: ty
# @File name: dashboard.py 
# @IDE: PyCharm
# @Create time: 1/19/21 11:09 AM
# @Description:
from flask import url_for, redirect
from flask_admin import AdminIndexView, expose
from flask_login import current_user


class IndexView(AdminIndexView):
    """"""
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('frontend.login'))

    def is_accessible(self):
        return current_user.is_authenticated

    @expose('/')
    def index(self):
        return self.render('admin/index.html')