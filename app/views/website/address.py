# -*- coding: utf-8  -*-
# @Author: ty
# @File name: address.py 
# @IDE: PyCharm
# @Create time: 1/21/21 5:03 PM
# @Description:
from flask import Blueprint, jsonify, request
from flask_babel import gettext
from flask_login import login_required, current_user

from app.models.user.address import Address

address = Blueprint('address', __name__, url_prefix='/api/address', static_folder='../../../static',
                    template_folder='../../../templates')


@address.route('/contries', methods=['GET'])
@cached(21600)
def get_countries():
    """
    国家
    :return:
    """
    return jsonify(message='OK', countries=list(REGION_HIERARCHY.keys()))


@address.route('/countries/<country>', methods=['GET'])
@cached(21600)
def get_regions(country):
    """
    种族
    :param country:
    :return:
    """
    regions = REGION_HIERARCHY.get(country)
    return jsonify(message='OK', regions=regions)


@address.route('/default', methods=['GET'])
@login_required
def default_address():
    """

    :return:
    """
    addresses = current_user.addresses
    if len(addresses) > 0:
        return jsonify(message='OK', address=addresses[0].to_json())
    return jsonify(message='OK', address=None)


@address.route('/get/<addr_id>', methods=['GET'])
@login_required
def get_address(addr_id):
    """

    :param addr_id:
    :return:
    """
    address = Address.objects(id=addr_id).first()
    if address not in current_user.addresses:
        return jsonify(message='Failed', error=gettext('invaild address id for current user'))

    return jsonify(message='OK', address=address.to_json())


@address.route('/all', methods=['GET'])
@login_required
def user_addresses():
    """
    获取所有地址信息
    :return:
    """
    addresses = current_user.addresses
    return jsonify(message='OK', addresses=[a.to_json() for a in addresses])


@address.route('/add', methods=['POST'])
@login_required
def add_address():
    """

    :return:
    """
    data = request.json
    address = Address(state=data['state'], city=data['city'], country=data['country'], street=data['street'],
                      postcode=data['postcode'], receiver=data['receiver'], mobile_number=data['mobile_number'])
    address.save()
    current_user.addresses.insert(0, address)
    current_user.save()
    return jsonify(message='OK', address_id=str(address.id))


@address.route('/del/<addr_id>', methods=['GET'])
@login_required
def del_address(addr_id):
    """
    删除地址信息
    :param addr_id:
    :return:
    """
    address = Address.objects(id=addr_id).first_or_404()
    if address not in current_user.addresses:
        return jsonify(message='Failed', error=gettext('invalid address id for current user'))

    current_user.update(pull__addresses=address)
    address.delete()
    return jsonify(message='OK')


@address.route('/update/<addr_id>', methods=['POST'])
@login_required
def update_address(addr_id):
    """

    :param addr_id:
    :return:
    """
    address = Address.objects(id=addr_id).first_or_404()
    if address not in current_user.addresses:
        return jsonify(message='Failed', error=gettext('invalid address id for current user'))

    data = request.json
    try:
        address.state = data['state']
        address.city = data['city']
        address.country = data['country']
        address.street = data['street']
        address.postcode = data['postcode']
        address.receiver = data['receiver']
        address.mobile_number = data['mobile_number']
    except KeyError:
        return jsonify(message='Failed', error=gettext('invalid data'))

    address.save()
    return jsonify(message='OK', address_id=str(address.id))
