# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order.py 
# @IDE: PyCharm
# @Create time: 1/21/21 5:03 PM
# @Description:
from flask import Blueprint, jsonify, request
from flask_babel import gettext
from flask_login import login_required, current_user

from app.config.enum import ORDER_SOURCES, ORDER_TYPE, LOG_STATUS
from app.models.order.entry import OrderEntry
from app.models.order.logistic import Logistic
from app.models.order.order import Order, TransferOrderCode
from app.models.user.address import Address

order = Blueprint('orders', __name__, url_prefix='/api/orders', static_folder='../../../static', template_folder='../../../templates')

def unpaid_orders(user_id):
    """
    未支付订单
    :param user_id:
    :return:
    """
    orders = Order.payment_pending(customer_id=user_id)
    return [json.simple_order_json(order) for order in orders]

def logistic_orders(user_id):
    """
    物流订单(在途)
    :param user_id:
    :return:
    """
    orders = Order.processing(customer_id=user_id)
    return [json.simple_order_json(order) for order in orders]

@order.route('/<order_type>', methods=['GET'])
@login_required
def get_orders(order_type):
    """
    获取订单信息
    :param order_type:
    :return:
    """
    if order_type == 'COMMODITIES':
        orders = Order.commidities(customer_id=current_user.id)
    elif order_type == 'TRANSFER':
        orders = Order.transfer(customer_id=current_user.id)
    else:
        return jsonify(message='Failed')
    return jsonify(message='OK', orders=[json.simple_order_json(order) for order in orders])

@order.route('/cal_entries_price', methods=['POST'])
@login_required
def cal_entries_price():
    """
    计算价格
    :return:
    """
    data = request.json
    entries = data.get('entries')
    if not entries:
        return jsonify(message='Failed', error=gettext('please select the item.'))

    address_id = data.get('address_id')
    if address_id:
        address = Address.objects(id=address_id).first_or_404()
    else:
        return jsonify(message='Failed', error=gettext('please select the address.'))

    entries_info = entry_info_from_ids(entries)
    cart = FakeCart(entries_info=entries_info, user=current_user._get_current_object(), address=address)
    cart.logistic_provider = data.get('logistic_provider')
    cart.coupon_codes = data.get('coupon_codes', [])

    price = cal_entries_price(cart)
    result = json.order_price_json(price)
    return jsonify(message='OK', order=result)

@order.route('/get/<order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """

    :param order_id:
    :return:
    """
    order = Order.objects(id=order_id).first_or_404()
    return jsonify(message='OK', order=json.order_json(order))

@order.route('/del/<order_id>', methods=['GET'])
@login_required
def delete_order(order_id):
    """

    :param order_id:
    :return:
    """
    order = Order.objects(id=order_id).first_or_404()
    if order.customer_id != current_user.id or order.is_paid:
        return jsonify(message='Failed', error=gettext('order not found'))

    order.cancel_order('user delete', 'ORDER_DELETED')
    return jsonify(message='OK')

@order.route('/secret/verify_and_move/<int:code>', methods=['GET'])
@login_required
def move_order_to_self(code):
    """

    :param code:
    :return:
    """
    order_code = TransferOrderCode.objects(code=code).first()
    if not order_code:
        return jsonify(message='Failed')

    order = Order.get_order_or_404(order_code.order_id)
    order.customer_id = current_user.id
    order.save()

    order_code.delete()
    return jsonify(message='OK', order=json.order_json(order))

@order.route('/logistics/<logistic_id>', methods=['GET'])
@login_required
def get_logistic(logistic_id):
    """

    :param logistic_id:
    :return:
    """
    logistic = Logistic.objects(id=logistic_id).first_or_404()
    express = logistic.express_tracking
    logistic_obj = {'id': str(logistic.id)}
    logistic_obj['entries'] = [json.entry_json(entry) for entry in logistic.entries]
    logistic_obj['status'] = logistic.detail.status
    logistic_obj['data'] = logistic.to_json()
    logistic_obj['history'] = logistic.shipping_history
    logistic_obj['tracking'] = express.history if express else ''
    logistic_obj['address'] = logistic.order.address.to_json()
    logistic_obj['payment_status'] = logistic.order.goods_payment.status
    return jsonify(message='OK', logistic=logistic_obj)

@order.route('/create_order', methods=['POST'])
@login_required
def create_order():
    """

    :return:
    """
    entries = request.json.get('entries')
    entries_info = entry_info_from_ids(entries)
    user = current_user._get_current_object()
    address_id = request.json.get('address_id')
    if address_id:
        address = Address.objects(id=address_id).first_or_404()
    elif user.addresses:
        address = user.addresses[0]
    else:
        return jsonify(message='Failed', error=gettext('no address'))

    logistic_provider = request.json.get('logistic_provider')
    if not logistic_provider:
        return jsonify(message='Failed', error=gettext('no logistic provider'))

    coin = 0
    cash = 0
    coupon_codes = request.json.get('coupon_codes', [])
    order = Order.create_from_skus(user.id, entries_info, logistic_provider, coupon_codes=coupon_codes, coin=coin, cash=cash, address=address, source=ORDER_SOURCES.WECHAT)
    if not isinstance(order, Order):
        return jsonify(message='Failed', error='编号为{}的商品已售光, 请重新提交'.format(order['item_id']))

    if order.final == 0:
        order.set_paid()

    remove_from_cart([entry.item_spec_snapshot.sku for entry in order.entries], user_id=str(current_user.id))
    return jsonify(message='OK', order_id=str(order.id), order=order.to_grouped_json())

@order.route('/create_transfer_order', methods=['POST'])
@login_required
def create_transfer_order():
    """

    :return:
    """
    data = request.json
    entries = data.get('entries')
    user = current_user._get_current_object()
    address_id = data.get('address_id')
    if address_id:
        address = Address.objects(id=address_id).first_or_404()
    elif user.addresses:
        address = user.addresses[0]
    else:
        return jsonify(message='Failed', error=gettext('no address'))

    coin = 0
    cash = user.coin_wallet.cash if data.get('cash') else 0
    coupon_codes = data.get('coupon_codes', [])

    entries = import_entries(entries)
    order = Order.create_transfer(customer_id=str(user.id), final=0, entries=entries, address=address, source=ORDER_SOURCES.WECHAT, status=LOG_STATUS.PENDING_REVIEW, order_type=ORDER_TYPE.TRANSFER, logistic_provider=data.get('logistic_provider'), coupon_codes=coupon_codes, coin=coin, cash=cash)

    logistic_provider_dispatcher(order)
    return jsonify(message='OK', order_id=str(order.id), order=order.to_grouped_json())

@order.route('/update_transfer_order', methods=['POST'])
@login_required
def update_transfer_order():
    """
    更新运单
    :return:
    """
    data = request.json
    order_id = data.get('order_id')
    order = Order.objects(id=order_id).first_or_404()
    # 入库订单才能修改
    if order.status != 'WAREHOUSE_IN':
        return jsonify(message='Failed', error=gettext('only when order status warehouse_in can be updated'))

    address_id = data.get('address_id')
    user = current_user._get_current_object()
    if address_id:
        address = Address.objects(id=address_id).first_or_404()
    elif user.addresses:
        address = user.addresses[0]
    else:
        return jsonify(message='Failed', error=gettext('no address'))

    order.logistic_provider = data.get('logistic_provider')
    order.coupon_codes = data.get('coupon_codes', [])
    order.address = address
    order.update_amount()
    order.reload()
    result = json.transfer_order_price_json(order)
    return jsonify(message='OK', order=result)

@order.route('/cal_order_price', methods=['POST'])
@login_required
def cal_order_price():
    """
    计算订单价格
    :return:
    """
    data = request.json
    order_id = data.get('order_id')
    address_id = data.get('address_id')
    user = current_user._get_current_object()
    if address_id:
        address = Address.objects(id=address_id).first_or_404()
    elif user.addresses:
        address = user.addresses[0]
    else:
        return jsonify(message='Failed', error=gettext('no address'))

    order = Order.objects(id=order_id).first_or_404()
    order.logistic_provider = data.get('logistic_provider')
    order.coupon_codes = data.get('coupon_codes')
    order.address = address

    price = cal_order_price(order)
    result = json.transfer_order_price_json(price)
    return jsonify(message='OK', order=result)

@order.route('/fill_shipping_info', methods=['POST'])
@login_required
def fill_shipping_info():
    """
    填写货船信息
    :return:
    """
    data = request.json
    entry_id = data.get('entry_id')
    shipping_info = data.get('shipping_info')
    entry = OrderEntry.objects(id=entry_id).first()
    entry.shipping_info = {
        'number': shipping_info.get('number'),
        'is_written': True
    }
    entry.save()
    return jsonify(message='OK')
