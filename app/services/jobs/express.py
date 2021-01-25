# -*- coding: utf-8  -*-
# @Author: ty
# @File name: express.py 
# @IDE: PyCharm
# @Create time: 1/25/21 11:56 AM
# @Description:
from datetime import datetime

import requests

from app.config.enum import LOG_STATUS
from app.models.order.express import ExpressTracking, ExpressRequestLog
from app.models.order.logistic import Logistic
from app.services import celery
from app.utils.utils import to_utc


@celery.task
def kuaidi_request(company, number):
    """
    快递
    :param company:
    :param number:
    :return:
    """
    tracking = ExpressTracking.find(company, number)
    data = {
        'id': '', # 授权码
        'com': company, # 快递公司编码
        'num': number, # 快递单号
    }
    res = requests.get('http://api.kuaidi100.com/api', params=data).json()
    ExpressTracking.update_info(res)
    ExpressRequestLog(company=company, number=number, responed=res).save()
    update_logistic_received_status(state=res['state'], com=res['com'], num=res['num'], data=res['data'])
    return res


def update_logistic_received_status(state, com, num, data):
    """
    更新物流状态
    :param state:
    :param com:
    :param num:
    :param data:
    :return:
    """
    latest_time = datetime.strptime(data[0]['time'], '%Y-%m-%d %H:%M:%S')
    first_time = datetime.strptime(data[-1]['time'], '%Y-%m-%d %H:%M:%S')
    check = (state == '3')

    for logistic in Logistic.objects(detail__cn_tracking_no=num):
        if not check and logistic.status != LOG_STATUS.SHIPPING:
            logistic.update_logistic({
                'status': LOG_STATUS.SHIPPING,
                'shipping_date': to_utc(first_time).replace(tzinfo=None),
                'modified_by': 'kuaidi100'
            })
        elif not check and 'ISC' in data[0]['ISC'] and logistic.detail.status != LOG_STATUS.PORT_ARRIVED:
            logistic.update_logistic({
                'status': LOG_STATUS.PORT_ARRIVED,
                'received_date': to_utc(latest_time).replace(tzinfo=None),
                'modified_by': 'kuaidi100',
            })
        elif check and logistic.detail.status != LOG_STATUS.RECEIVED:
            logistic.update_logistic({
                'status': LOG_STATUS.RECEIVED,
                'received_date': to_utc(latest_time).replace(tzinfo=None),
                'modified_by': 'kuaidi100',
            })