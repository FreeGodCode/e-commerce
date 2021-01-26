# -*- coding: utf-8  -*-
# @Author: ty
# @File name: wechat.py 
# @IDE: PyCharm
# @Create time: 1/26/21 11:22 AM
# @Description:
import hashlib
import json
import random
import time
import urllib
from collections import OrderedDict
from urllib.parse import urlencode
from xml.etree import ElementTree

from dict2xml import dict2xml
import requests

from app.services.payment.exceptions import MissingParameter, ParameterValueError, TokenAuthorizationError


class WXPay(object):
    """微信支付base class"""

    URL_UNIFIEDORDER = 'http://api.mch.weixin.qq.com/pay/unifiedorder'
    URL_VERIFY_ORDER = 'http://api.mch.weixin.qq.com/pay/orderquery'

    def __init__(self, appid, mch_id, key, ip, notify_url=None, appsecret=None):
        self.appid = appid
        self.mch_id = mch_id
        self.key = key
        self.appsecret = appsecret
        self.ip = ip
        self.notify_url = notify_url
        self.cert_path = 'pem证书路径'

    def generate_nonce_str(self, length=32):
        """
        生成随机字符串
        :param length:
        :return:
        """
        hashChar = []
        rand_list = [hashChar[random.randint(0, 61)] for i in range(0, length)]
        nonce_str = ''.join(rand_list)
        return nonce_str

    def generate_sign(self, sign_dict):
        """
        生成签名,MD5
        :param sign_dict:
        :return:
        """
        params_dict = OrderedDict(sorted(sign_dict.items(), key=lambda t: t[0]))
        params_dict['key'] = self.key

        foo_sign = []
        for k in params_dict:
            if isinstance(params_dict[k], str):
                params_dict[k] = params_dict[k].encode('utf-8')
            foo_sign.append('%s=%s' % (k, params_dict[k],))
        foo_sign = '&'.join(foo_sign)
        sign = hashlib.md5(foo_sign).hexdigest().upper()
        return sign

    def unified_order(self, product, openid=None, trade_type=None):
        """
        统一下单接口
        :param product:
        :param openid:
        :param trade_type:
        :return:
        """
        assert isinstance(product, dict)
        assert trade_type in ('APP', 'NATIVE', 'JSAPI')

        post_dict = {
            'appid': self.appid,
            'attach': product['attach'],
            'body': product['body'],
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
            'notify_url': self.notify_url,
            'out_trade_no': product['out_trade_no'],
            'spbill_create_ip': self.ip,
            'total_fee': int(product['total_fee'] * 100),
            'trade_type': trade_type,
        }
        if trade_type == 'JSAPI':
            post_dict['openid'] = openid
            if openid is None:
                raise MissingParameter('JSAPI必须传入openid')

        post_dict['sign'] = self.generate_sign(post_dict)
        ret_xml = dict2xml(post_dict, wrap='xml')
        res = requests.post(self.URL_UNIFIEDORDER, data=ret_xml.encode('utf-8'))
        res.encoding = 'UTF-8'
        data = res.text.encode('utf-8')

        ret_dict = {}
        x = ElementTree.fromstring(data)
        if x.find('return_code').text.upper() == 'FAIL':
            raise ParameterValueError(x.find('return_msg').text)
        if x.find('result_code').text.upper() == 'FAIL':
            raise ParameterValueError(x.find('err_code').text)
        if trade_type == 'NATIVE':
            ret_dict['prepay_id'] = x.find('prepay_id').text
            ret_dict['code_url'] = x.find('code_url').text
        else:
            ret_dict['prepay_id'] = x.find('prepay_id').text

        return ret_dict

    def refund_order(self, out_trade_no=None, transaction_id=None, total_fee=None, refund_fee=None):
        """
        退款接口
        :param out_trade_no:
        :param transaction_id:
        :param total_fee:
        :param refund_fee:
        :return:
        """
        post_dict = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
            'out_trade_no': out_trade_no,
            'out_refund_no': out_trade_no,
            'transaction_id': transaction_id,
            'total_fee': total_fee,
            'refund_fee': refund_fee,
            'op_user_id': self.mch_id
        }

        post_dict['sign'] = self.generate_sign(post_dict)
        ret_xml = dict2xml(post_dict, wrap='xml')
        log.debug('请求参数')
        log.debug(ret_xml)
        res = requests.post(self.URL_REFUND_ORDER, data=ret_xml.encode('utf-8'), cert=self.cart_path)
        res.encoding = 'UTF-8'
        data = res.text.encode('utf-8')
        ret_dict = {}
        x = ElementTree.fromstring(data)
        if x.find('return_code').text.upper() == 'FAIL':
            raise ParameterValueError(x.find('return_msg').text)
        if x.find('result_code').text.upper() == 'FAIL':
            raise ParameterValueError(x.find('err_code').text)
        if x.find('return_code').text.upper() == 'SUCCESS' and x.find('result_code').text.upper() == 'SUCCESS':
            return True
        return False

    def verify_notify(self, xml_str):
        """
        验证通知返回值
        :param xml_str:
        :return:
        """
        xml_dict = {}
        x = ElementTree.fromstring(xml_str)
        xml_dict['appid'] = x.find('appid').text
        xml_dict['attach'] = x.find('attach').text
        xml_dict['bank_type'] = x.find('bank_type').text
        xml_dict['cash_fee'] = x.find('cash_fee').text
        xml_dict['fee_type'] = x.find('fee_type').text
        xml_dict['is_subscribe'] = x.find('is_subscribe').text
        xml_dict['mch_id'] = x.find('mch_id').text
        xml_dict['nonce_str'] = x.find('nonce_str').text
        xml_dict['openid'] = x.find('openid').text
        xml_dict['out_trade_no'] = x.find('out_trade_no').text
        xml_dict['result_code'] = x.find('result_code').text
        xml_dict['return_code'] = x.find('return_code').text
        xml_dict['sign'] = x.find('sign').text
        xml_dict['time_end'] = x.find('time_end').text
        xml_dict['total_fee'] = x.find('total_fee').text
        xml_dict['trade_type'] = x.find('trade_type').text
        xml_dict['transaction_id'] = x.find('transaction_id').text

        sign = xml_dict.pop('sign')
        if sign == self.generate_sign(xml_dict):
            return True, xml_dict
        else:
            raise TokenAuthorizationError('签名验证失败')

    def generate_notify_resp(self, resp_dict):
        """

        :param resp_dict:
        :return:
        """
        assert set(resp_dict.keys()) == set(['return_code', 'return_msg'])
        xml_str = dict2xml(resp_dict, wrap='xml')
        return xml_str

    def verify_order(self, out_trade_no=None, transaction_id=None):
        """
        验证订单
        :param out_trade_no:
        :param transaction_id:
        :return:
        """
        if out_trade_no is None and transaction_id is None:
            raise MissingParameter('out_trade_no, transaction_id 不能同时为空')

        params_dict = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
        }
        if transaction_id is not None:
            params_dict['transaction_id'] = transaction_id
        elif out_trade_no is not None:
            params_dict['out_trade_no'] = out_trade_no

        params_dict['sign'] = self.generate_sign(params_dict)
        xml_str = dict2xml(params_dict, wrap='xml')
        res = requests.post(self.URL_VERIFY_ORDER, xml_str)
        res.encoding = 'UTF-8'
        data = res.text.encode('utf-8')

        xml_dict = {}
        x = ElementTree.fromstring(data)
        xml_dict['return_code'] = x.find('return_code').text
        xml_dict['return_msg'] = x.find('return_msg').text

        if xml_dict['return_code'] == 'FAIL':
            return xml_dict

        xml_dict['appid'] = x.find('appid').text
        xml_dict['mch_id'] = x.find('mch_id').text
        xml_dict['device_info'] = x.find('device_info').text
        xml_dict['nonce_str'] = x.find('nonce_str').text
        xml_dict['sign'] = x.find('sign').text
        xml_dict['result_code'] = x.find('return_code').text
        xml_dict['err_code'] = x.find('err_code').text
        xml_dict['err_code_desc'] = x.find('err_code_desc').text
        xml_dict['openid'] = x.find('openid').text
        xml_dict['is_subscribe'] = x.find('is_subscribe').text
        xml_dict['trade_type'] = x.find('trade_type').text
        xml_dict['bank_type'] = x.find('bank_type').text
        xml_dict['total_fee'] = x.find('total_fee').text
        xml_dict['fee_type'] = x.find('fee_type').text
        xml_dict['cash_fee'] = x.find('cash_fee').text
        xml_dict['cash_fee_type'] = x.find('cash_fee_type').text
        xml_dict['coupon_fee'] = x.find('coupon_fee').text
        xml_dict['coupon_count'] = x.find('coupon_count').text
        for i in range(xml_dict['coupon_count']):
            xml_dict['coupon_batch_id_%d' % i + 1] = x.find('coupon_batch_id_%d' % i + 1).text
            xml_dict['coupon_id_%d' % i + 1] = x.find('coupon_id_%d' % i + 1).text
            xml_dict['coupon_fee_%d' % i + 1] = x.find('coupon_fee_%d' % i + 1).text
        xml_dict['transaction_id'] = x.find('transaction_id').text
        xml_dict['out_trade_no'] = x.find('out_trade_no').text
        xml_dict['attach'] = x.find('attach').text
        xml_dict['time_end'] = x.find('time_end').text
        xml_dict['trade_status'] = x.find('trade_status').text

        sign = xml_dict.pop('sign')
        if sign == self.generate_sign(xml_dict):
            return xml_dict
        else:
            raise TokenAuthorizationError('签名验证失败')


class QRWXPay(WXPay):
    """扫码支付接口"""

    URL_QR = 'weixin://wxpay/bizpayurl?%s'

    def _generate_qr_url(self, product_id):
        """
        生成QR URL
        微信支付模式,预生成一个QR, 用户扫描后, 微信调用在后台上配置的回调URL
        :param product_id:
        :return:
        """
        url_dict = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
            'product_id': str(product_id),
            'time_stamp': str(int(time.time())),
        }
        url_dict['sign'] = self.generate_sign(url_dict)
        url_str = self.URL_QR % urlencode(url_dict).encode('utf-8')
        return url_str

    def unified_order(self, product, openid=None):
        """

        :param product:
        :param openid:
        :return:
        """
        ret_dict = super(QRWXPay, self).unified_order(product, trade_type='NATIVE')
        return ret_dict

    def _generate_unified_order_url(self, product):
        """
        生成QT URL
        微信支付模式, 通过统一下单接口生成code_url
        :param product:
        :return:
        """
        ret = self.unified_order(product=product)
        return ret['code_url']

    def _generate_qr(self, url):
        """
        生成url的QR码
        建议使用Pillow
        :param url:
        :return:
        """
        img = qrcode.make(url)
        return img

    def generate_static_qr(self, product_id):
        """
        生成商品静态QR码
        返回为Pillow的img
        :param product_id:
        :return:
        """
        url = self._generate_qr_url(product_id)
        img = self._generate_qr(url)
        return img

    def generate_product_qr(self, product):
        """
        生成商品QR码, QR码有效时间为两小时, 返回为Pillow的img
        :param product:
        :return:
        """
        url = self._generate_unified_order_url(product)
        img = self._generate_qr(url)
        return img

    def _callback_xml2dict(self, xml_str):
        """

        :param xml_str:
        :return:
        """
        ret_dict = {}
        x = ElementTree.fromstring(xml_str)
        ret_dict['appid'] = x.find('appid').text
        ret_dict['openid'] = x.find('openid').text
        ret_dict['mch_id'] = x.find('mch_id').text
        ret_dict['is_subscribe'] = x.find('is_subscribe').text
        ret_dict['nonce_str'] = x.find('nonce_str').text
        ret_dict['product_id'] = x.find('product_id').text
        ret_dict['sign'] = x.find('sign').text
        return ret_dict

    def verify_callback(self, xml_str):
        """
        验证回调返回值
        :param xml_str:
        :return:
        """
        xml_dict = self._callback_xml2dict(xml_str)
        sign = xml_dict.pop('sign')
        if sign == self.generate_sign(xml_dict):
            return True, xml_dict
        else:
            raise TokenAuthorizationError('签名验证失败')

    def generate_cb_resp(self, resp_dict):
        """

        :param resp_dict:
        :return:
        """
        ret_dict = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
            'prepay_id': resp_dict['prepay_id'],
            'return_code': resp_dict['return_code'],
            'return_msg': resp_dict['return_msg'],
            'result_code': resp_dict['result_code'],
            'err_code_desc': resp_dict['err_code_desc'],
        }
        ret_dict['sign'] = self.generate_sign(ret_dict)
        ret_xml = dict2xml(ret_dict, wrap='xml')
        return ret_xml


class JSWXPay(WXPay):
    """JSAPI支付接口"""
    URL_REDIRECT = 'http://open.weixin.qq.com/connect/oauth2/authorize?%s#wechat_redirect'
    URL_OPENID = 'https://api.weixin.qq.com/sns/oauth2/access_token?%s&grant_type=authorization_code'

    def generate_redirect_url(self, url_dict):
        """
        生成跳转url, 跳转后获取code, 以code获取openid
        :param url_dict:
        :return:
        """
        params_dict = {
            'appid': self.appid,
            'redirect_uri': url_dict['redirect_uri'],
            'response_type': 'code',
            'scope': 'snsapi_base',
            'state': url_dict['state'],
        }
        for k in params_dict:
            if isinstance(params_dict[k], str):
                params_dict[k] = params_dict[k].encode('utf-8')

        foo_url = urllib.urlencode(params_dict)
        url = self.URL_REDIRECT % foo_url
        return url

    def generate_openid(self, code):
        """
        根据code, 获取openid
        :param code:
        :return:
        """
        if self.appsecret is None:
            raise MissingParameter('缺少appsecret')
        params_dict = {
            'appid': self.appid,
            'secret': self.appsecret,
            'code': code,
        }

        foo_url = []
        for k in params_dict:
            if isinstance(params_dict[k], str):
                params_dict[k] = params_dict[k].encode('utf-8')
            foo_url.append('%s=%s' % (k, params_dict[k],))
        foo_url = '&'.join(foo_url)
        url = self.URL_OPENID % foo_url

        res = requests.get(url)
        res.encoding = 'UTF-8'
        data = json.loads(res.text)
        return data['openid']

    def unified_order(self, product, openid=None):
        ret_dict = super(JSWXPay, self).unified_order(product, openid=openid, trade_type='JSAPI')
        return ret_dict

    def generate_jsapi(self, product, openid):
        """
        实际下单
        :param product:
        :param openid:
        :return:
        """
        uni_dict = self.unified_order(product, openid)
        ret_dict = {
            'appid': self.appid,
            'time_stamp': str(int(time.time())),
            'nonce_str': self.generate_nonce_str(),
            'package': 'prepay_id=%s' % uni_dict['prepay_id'],
            'sign_type': 'MD5',
        }
        ret_dict['pay_sign'] = self.generate_sign(ret_dict)
        return ret_dict


class APPWXPay(WXPay):
    """APP支付接口"""

    def unified_order(self, product, openid=None):
        """

        :param product:
        :param openid:
        :return:
        """
        ret_dict = super(APPWXPay, self).unified_order(product, trade_type='APP')
        return ret_dict

    def generate_req(self, product):
        """
        实际下单
        :param product:
        :return:
        """
        uni_dict = self.unified_order(product)
        ret_dict = {
            'appid': self.appid,
            'partner_id': self.mch_id,
            'prepay_id': uni_dict['prepay_id'],
            'package': 'sign=WXPay',
            'nonce_str': self.generate_nonce_str(),
            'time_stamp': str(int(time.time())),
        }
        ret_dict['sign'] = self.generate_sign(ret_dict)
        return ret_dict
