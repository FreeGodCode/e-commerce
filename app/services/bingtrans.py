# -*- coding: utf-8  -*-
# @Author: ty
# @File name: bingtrans.py 
# @IDE: PyCharm
# @Create time: 1/23/21 10:20 PM
# @Description:
import json
import re
import time

import requests
from flask import request


class AuthenticationFailed(Exception):
    """身份验证失败"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ArgumentException(Exception):
    """结果异常类"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class MSTranslate():
    """微软翻译"""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ''

    def access_token(self):
        """

        :return:
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'http://api.microsofttranslator.com',
            'grant_type': 'client_credentials'
        }
        r = request.post('https://datamarket.accesscontrol.windows.net/v2/OAuth2-13/', data=data)
        result = json.loads(r.text)
        if 'error_description' in result:
            raise AuthenticationFailed(result['access_token'])
        else:
            self.access_token = result['access_token']
            self.time = time.time()

    def translate(self, text, to_lang, from_lang=None):
        """

        :param text:
        :param to_lang:
        :param from_lang:
        :return:
        """
        if not self.access_token:
            self.access_token()
        elif int(time.time() - self.time) > 550:
            self.access_token()
        auth_token = 'Bearer' + self.access_token
        headers = {'Authorization': auth_token}
        params = {'text': text, 'form': from_lang, 'to': to_lang}
        result = requests.get('http://api.microsofttranslator.com/v2/Http.svc/Translate', params=params, headers=headers)

        if 'Argument Exception' in result.text:
            error = re.search(r'<p>Message: (.*?)</p>', result.text.replace('\n', '')).group(1)
            raise ArgumentException(error)
        else:
            return result.text[68: -9]
