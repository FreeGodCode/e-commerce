# -*- coding: utf-8  -*-
# @Author: ty
# @File name: logistic.py 
# @IDE: PyCharm
# @Create time: 1/25/21 5:05 PM
# @Description:
from app.models.order.partner import ChannelProvider, LogisticProvider


def channel_price(items, country):
    """

    :param items:
    :param country:
    :return:
    """
    total_weight = sum([item.weight * quantity for item, quantity in items])
    weight_desc = '商品总重量{}kg'.format(total_weight / 1000)

    channels_json = []
    channels = ChannelProvider.active(country=country)
    for channel in channels:
        channels_json.append(dict(name=channel.name, display_name=channel.display_name, desc=channel.description,
                                  service_intro=channel.service_intro, cn_shipping=channel.shipping))

    return {'weight': total_weight, 'weight_desc': weight_desc, 'providers': channels_json}


def logistic_provider_prices(items, country, weight=0):
    """

    :param items:
    :param country:
    :param weight:
    :return:
    """
    if weight:
        total_weight = weight
    else:
        total_weight = sum([item.weight * quantity for item, quantity in items])

    weight_desc = '商品总重量{}kg'.format(total_weight / 1000)
    providers_json = []
    providers = LogisticProvider.active(country=country, limited_weight__gte=total_weight)
    for provider in providers:
        shipping = provider.get_shipping(total_weight)
        providers_json.append(dict(
            name=provider.name,
            display_name=provider.display_name,
            desc=provider.description,
            service_intro=provider.service_intro,
            cn_shipping=shipping,
        ))
    return {'weight': total_weight, 'weight_desc': weight_desc, 'providers': providers_json}


def get_display_provider_info(country, total_weight):
    """

    :param country:
    :param total_weight:
    :return:
    """
    weight_desc = '商品总重量{}kg'.format(total_weight / 1000)
    providers_json = []
    providers = LogisticProvider.active(country=country, limited_weight__gte=total_weight)
    for provider in providers:
        shipping = provider.get_shipping(total_weight)
        providers_json.append(dict(
            name=provider.display_name,
            logo=provider.logo,
            init_price=provider.init_price,
            init_weight=provider.init_weight,
            continued_price=provider.continued_price,
            continued_weight=provider.continued_weight,
            desc=provider.description,
            service_intro=provider.service_intro,
            rule_desc=provider.rule_desc,
            cn_shipping=shipping,
        ))
    return {'weight': total_weight, 'weight_desc': weight_desc, 'providers': providers_json}
