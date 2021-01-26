# -*- coding: utf-8  -*-
# @Author: ty
# @File name: forex.py 
# @IDE: PyCharm
# @Create time: 1/26/21 5:34 PM
# @Description: 汇率
import decimal

import requests


class OpenExchangeRatesClientException(requests.exceptions.RequestException):
    pass


class OpenExchangeRatesClient(object):
    BASE_URL = 'http://openexchangerates.org/api'
    ENDPOINT_LATEST = BASE_URL + '/latest.json'
    ENDPOINT_CURRENCIES = BASE_URL + '/currencies.json'
    ENDPOINT_HISTORICAL = BASE_URL + '/historical/%s.json'

    def __init__(self, api_key):
        self.client = requests.Session()
        self.client.params.update({'app_id': api_key})

    def latest(self, base='USD'):
        """
        fetches latest exchange rate data from service
        :param base:
        :return:
        """
        try:
            resp = self.client.get(self.ENDPOINT_LATEST, params={'base': base})
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise OpenExchangeRatesClientException(e)
        return resp.json(parse_int=decimal.Decimal, parse_float=decimal.Decimal)

    def currencies(self):
        """
        fetches current currency data of the service
        :return:
        """
        try:
            resp = self.client.get(self.ENDPOINT_CURRENCIES)
        except requests.exceptions.RequestException as e:
            raise OpenExchangeRatesClientException(e)

        return resp.json()

    def historical(self, date, base='USD'):
        """
        fetches historical exchange rate data from service
        :param date:
        :param base:
        :return:
        """
        try:
            resp = self.client.get(self.ENDPOINT_HISTORICAL % date.strftime('%Y-%m-%d'), params={'base': base})
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise OpenExchangeRatesClientException(e)
        return resp.json(parse_int=decimal.Decimal, parse_float=decimal.Decimal)
