# -*- coding: utf-8  -*-
# @Author: ty
# @File name: forex.py 
# @IDE: PyCharm
# @Create time: 1/26/21 10:33 PM
# @Description:
from app.config.settings import OPENEXCHANGERATES_APPID
from app.models.inventory.price import ForexRate
from app.services import celery
from app.services.price.forex import OpenExchangeRatesClient


@celery.task
def record_latest_forex_rate():
    client = OpenExchangeRatesClient(OPENEXCHANGERATES_APPID)
    res = client.latest()
    usd_to_cny = res['rates']['CNY']
    ForexRate.put(usd_to_cny)
