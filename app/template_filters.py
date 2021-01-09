# -*- coding: utf-8  -*-
# @Author: ty
# @File name: template_filters.py 
# @IDE: PyCharm
# @Create time: 1/9/21 7:14 PM
# @Description:
def init_template_filters(app):
    """

    :param app:
    :return:
    """
    from flask_login import current_user
    app.jinja_env.globals['current_user'] = current_user
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    app.jinja_env.globals['hasattr'] = hasattr
    filters = app.jinja_env.filters
    filters['timesince'] = timesince
    filters['timeuntil'] = timeuntil
    filters['format_date'] = format_date