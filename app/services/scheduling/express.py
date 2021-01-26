# -*- coding: utf-8  -*-
# @Author: ty
# @File name: express.py 
# @IDE: PyCharm
# @Create time: 1/26/21 10:29 PM
# @Description:
from app.models.order.logistic import Logistic
from app.services import celery


@celery.task
def check_kuaidi():
    logistics = Logistic.objects(is_closed=False, detail__cn_tracking_no__ne='', detail__cn_logistic_name__ne='',
                                 detail__status__in=['SHIPPING', 'PORT_ARRIVED'])
    for logistic in logistics:
        jobs.express.kuai_request(logistic.detail.cn_logistic_name, logistic.detail.cn_logistic_no)
