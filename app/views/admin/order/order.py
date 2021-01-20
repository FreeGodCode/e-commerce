# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order.py 
# @IDE: PyCharm
# @Create time: 1/20/21 12:12 PM
# @Description:
from flask import request, url_for, redirect, jsonify
from flask_admin import expose
from flask_babel import gettext

from app.models.order.logistic import Logistic
from app.models.order.order import Order
from app.models.user.address import Address
from app.utils.utils import Pagination
from app.views.admin import AdminView


class OrderView(AdminView):
    """"""
    _permission = 'order'

    @expose('/<tab>/')
    @expose('/')
    def index(self, tab='all'):
        """
        展示首页
        :param tab:
        :return:
        """
        page = request.args.get('page', 1)
        if tab == 'all':
            orders = Order.commodities(is_paid=True, status__nin=['ABNORMAL', 'CANCELLED', 'REFUNDED'], is_test=False)
        elif tab == 'test':
            orders = Order.commodities(is_paid=True, status__nin=['ABNORMAL', 'CANCELLED', 'REFUNDED'], is_test=True)
        elif tab == 'transfer':
            orders = Order.transfer()
        elif tab == 'unpaid':
            orders = Order.commodities(is_paid=False)
        elif tab == 'irregularity':
            orders = Order.commodities(status__in=['ABNORMAL', 'CANCELLED', 'REFUNDED'])
        elif tab == 'payment_abnormal':
            orders = Order.objects(is_payment_abnormal=True)
        else:
            orders = Order.commodities(is_paid=True)

        orders = orders.order_by('-paid_date', '-created_at')
        data = Pagination(orders, int(page), 10)
        return self.render('admin/order/orders.html', tab=tab, page=page, orders=data, section='orders')

    @expose('/search/<page>')
    @expose('/search')
    def search(self, page=1):
        """
        搜索
        :param page:
        :return:
        """
        name = request.args.get('name', '')
        if name.isdigit():
            orders = Order.objects(short_id=int(name))
        else:
            addrs = Address.objects(receiver=name).distinct('id')
            orders = Order.commodities(address__in=addrs)
        if len(name) > 15:
            orders = Order.objects(id=name)

        data = Pagination(orders, int(page), 10)
        return self.render('admin/order/orders.html', name=name, orders=data, page=page, section='search')

    @expose('/<order_id>/cancel')
    def cancel_order(self, order_id):
        """
        取消订单
        :param order_id:
        :return:
        """
        order = Order.objects(id=order_id).first_or_404()
        reason = request.args.get('reason')
        order.cancel_order(reason=reason or 'cancelled from content page')
        return redirect(url_for('.index'))

    @expose('/mail_info', methods=['GET', 'POST'])
    def edit_mail_info(self):
        """
        编辑邮件信息
        :return:
        """
        if not request.is_xhr:
            return jsonify({'message': 'FAILED'})

        if request.method == 'GET':
            logistic_id = request.args.get('id')
            logistic = Logistic.objects(id=logistic_id).first()
            return jsonify({'remark': logistic.detail.extra, 'id': str(logistic.id)})

        if request.method == 'POST':
            logistic_id = request.form.get('lid')
            logistic = Logistic.objects(id=str(logistic_id)).first()
            logistic.detail.extra = request.form.get('remark')
            return jsonify({'remark': logistic.detail.extra, 'message': 'OK'})


admin.add_view(OrderView(name=gettext('Order'), category=gettext('Order'), menu_icon_type='fa', menu_icon_value='bar-chart-o'))
