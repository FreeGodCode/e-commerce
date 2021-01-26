# -*- coding: utf-8  -*-
# @Author: ty
# @File name: 4px.py 
# @IDE: PyCharm
# @Create time: 1/25/21 11:57 PM
# @Description:
from app.config.settings import BING_APPSECRET, BING_APPID
from app.services.bingtrans import MSTranslate


class FourPX(object):
    TOOL_SERVICE_URL = 'http://api.4px.com/OrderOnlineToolService.dll?wsdl'
    ORDER_SERVICE_URL = 'http://api.4px.com/OrderOnlineService.dll?wsdl'

    def __init__(self, token):
        """
        初始化客户端实例
        :param token:
        """
        self.token = token

    def create_order(self, logistic):
        """
        创建订单
        :param logsitic:
        :return:
        """
        address = logistic.order.address
        client = Client(self.ORDER_SERVICE_URL)
        order = client.factory.create('createOrderRequest')
        order.order_no = logistic.detail.partner_tracking_no
        order.product_code = logistic.detail.channel or 'A1'
        order.initial_country_code = 'CN'
        order.destination_country_code = address.country == 'United States' and 'US' or ''
        order.pieces = str(sum(entry.quantity for entry in logistic.entries))
        order.customer_weight = str(logistic.estimated_weight / 1000)
        order.shipping_company_name = 'maybe tech'
        order.shipping_name = ''
        order.shipping_address = ''
        order.shipping_telephone = ''
        order.consignee_name = address.receiver
        order.street = address.street + '' + str(address.street) or ''
        order.city = address.city
        order.state_or_province = address.state
        order.consignee_postcode = address.postcode

        translator = MSTranslate(BING_APPID, BING_APPSECRET)

        for entry in logistic.entries:
            item = client.factory.create('declareInvoice')
            item.eName = translator.translate(entry.item_snapshot.title, 'en', 'zh')
            item.name = entry.item_snapshot.title
            item.declare_unit_code = 'PCE'
            item.declare_pieces = entry.quantity
            item.unit_price = entry.unit_price
            order.declare_invoice.append(item)

        res = client.service.create_order_service(self.token, order)
        return res

    def query_express(self, no):
        """
        查询轨迹
        :param no:
        :return:
        """
        client = Client(self.TOOL_SERVICE_URL)
        res = client.service.cargo_tracking_service(self.token, no)
        return res

    def cal_fee(self, country, weight):
        """
        查询运费
        :param country:
        :param weight:
        :return:
        """
        client = Client(self.TOOL_SERVICE_URL)
        charge = client.factory.create('chargeCalculateRequest')
        charge.country_code = country
        charge.weight = weight
        res = client.service.charge_calculate_service(self.token, charge)
        return res
