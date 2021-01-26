# -*- coding: utf-8  -*-
# @Author: ty
# @File name: exceptions.py 
# @IDE: PyCharm
# @Create time: 1/26/21 11:22 AM
# @Description:
class WXPayException(Exception):
    """base alipay exception"""
    pass


class MissingParameter(WXPayException):
    """raised when create payment url process is missing some parameters needed ot continue"""
    pass


class ParameterValueError(WXPayException):
    """raised when parameter value is incorrect"""
    pass


class TokenAuthorizationError(WXPayException):
    """The error occurred when getting token"""
    pass
