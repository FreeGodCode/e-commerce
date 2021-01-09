# -*- coding: utf-8  -*-
# @Author: ty
# @File name: init_log.py
# @IDE: PyCharm
# @Create time: 1/9/21 6:34 PM
# @Description:
import logging
import os
from logging.handlers import SMTPHandler


def init_logging(app):
    """
    日志文件和日志邮件
    :param app:
    :return:
    """
    # 跳过测试和调试模式
    if app.debug or app.testing:
        return

    app.logging.setLevel(logging.INFO)
    info_log = os.path.join(app.root_path, '..', 'logs', 'app-info.log')
    # 日志文件
    info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=1048576, backupCount=20)
    info_file_handler.setLevel(logging.INFO)
    # 格式化器
    info_file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s : %(message)s [in %(pathname)s : %(lineno)d]'))
    # 处理器
    app.logger.addHandler(info_file_handler)

    ADMINS = ['thechosenone_ty@163.com']
    mail_handler = SMTPHandler(app.config['MAIL_SERVER'], app.config['MAIL_USERNAME'], ADMINS,
                               '0_ops...%s failed!' % app.config['PROJECT'],
                               (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathnames)s: %(lineno)d]'))
    app.logger.addHandler(mail_handler)