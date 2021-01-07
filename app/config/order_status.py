# -*- coding: utf-8  -*-
# @Author: ty
# @File name: order_status.py 
# @IDE: PyCharm
# @Create time: 1/7/21 11:24 AM
# @Description:订单状态
# 下单->未付款->付款成功->核验清单->入库->准备发货->快递中->包裹签收->退货->退款
ORDER_STATUS_DESCRIPTION = {
    'PAYMENT_PENDING': '未付款',
    'PAYMENT_RECEIVED': '下单成功',#成功支付
    'PENDING_REVIEW': '核验清单',
    'TRANSFER_APPROVED': '跟踪快递',#Express
    'WAREHOUSE_IN': '入库称重',
    'CANCELLED': '取消订单',
    'ABNORMAL': '订单异常',
    'DELETE': '删除订单',
    'EXPIRED': '订单过期',
    'REFUNDED': '已退款',
    'PROCESSING': '准备发货',
    'SHIPPING': '正在运送',
    'PORT_ARRIVED': '航班到港',
    'RECEIVED': '包裹签收',
    'PENDING_RETURN': '退款中',
    'RETURNING': '退款中',
    'RETURNED': '已退款',
}

SHIPPING_HISTORY = {
    'PAYMENT_RECEIVED': '您已成功支付,请等待系统确认',
    'PENDING_REVIEW': '您的订单已提交,将在12小时内为您核验清单',
    'TRANSFER_APPROVED': '您的订单商品已通过审核',
    'WAREHOUSE_IN': '您的商品已入库',
    'PROCESSING': '您的订单已确认,仓库正在撿货,等待发货',
    'SHIPPING': '您的订单已发货, 请留意物流信息',
    'PORT_ARRIVED': '您的包裹已抵达港口',
    'RECEIVED': '您的包裹已签收',
    'PENDING_RETURN': '取消订单,申请退款',
    'RETURNING': '退货中',
    'RETURNED': '已退货',
}

ROUTES = {
    'DEFAULT': ['PAYMENT_RECEIVED', 'PROCESSING', 'SHIPPING', 'PORT_ARRIVED', 'RECEIVED'],
    'TRANSFER': ['PENDING_REVIEW', 'TRANSFER_APPROVED', 'WAREHOUSE_IN', 'PAYMENT_RECEIVED', 'SHIPPING', 'PORT_ARRIVED', 'RECEIVED']
}