# -*- coding: utf-8  -*-
# @Author: ty
# @File name: cache.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:37 PM
# @Description:
from flask import request

from app import cache


def args_cache_key(*args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    path = request.path
    _args = {}
    for k, v in request.args.items():
        _args[k] = v
    _args.pop('session_key', None)
    args = str(hash(frozenset(_args.items()))) + str(request.is_xhr)
    # lang = get_locale()
    # return (path + args + lang).encode('utf-8')
    return path + args


def specify_args_cache_key(*args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    values = []
    for k in args:
        if k in request.args:
            values.append((k, request.args.get('k')))

    args = str(hash(frozenset(values)))
    return args


def cached(*args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    kwargs.update({'key_prefix': args_cache_key})
    return cache.cached(*args, **kwargs)


def cached_on_args(*args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    kwargs.update({'key_prefix': specify_args_cache_key})
    return cache.cached(*args, **kwargs)


def memoize(*args, **kwargs):
    """

    :param args:
    :param kwargs:
    :return:
    """
    return cache.cached(*args, **kwargs)
