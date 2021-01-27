# -*- coding: utf-8  -*-
# @Author: ty
# @File name: models.py 
# @IDE: PyCharm
# @Create time: 1/19/21 11:09 AM
# @Description:
from app import admin
from app.models.cart.cart import Cart, EntrySpec
from app.models.content.board import Board
from app.models.content.post import Post, PostComment, PostLike, PostActivity, PostFeedback, PostTag
from app.models.coupon.coupon import Coupon
from app.models.coupon.wallet import CouponWallet
from app.models.inventory.brand import Brand
from app.models.inventory.category import Category
from app.models.inventory.item import Item, ItemSpec
from app.models.inventory.price import PriceHistory, ForexRate
from app.models.inventory.tag import Tag
from app.models.inventory.vendor import Vendor
from app.models.order.entry import OrderEntry
from app.models.order.order import Payment, Order, TransferOrderCode, OrderExtra
from app.models.order.partner import LogisticProvider, ChannelProvider, Partner
from app.models.permission.permission import BackendPermission, Role
from app.models.reward.coin import CoinWallet, CoinTrade
from app.models.user.address import Address
from app.models.user.guest import GuestRecord
from app.models.user.user import User, SocialOAuth
from app.views.admin import MBModelView


class UserView(MBModelView):
    """"""
    form_subdocuments = {
        'account': {
            'form_columns': ('email', 'mobile_number', 'activation_key', 'activation_key_expire_date')
        },
    }


class LoginView(MBModelView):
    """"""
    can_create = False
    column_default_sort = ('created_at', True)
    column_filters = ('log_type',)


admin.add_view(MBModelView(BackendPermission, category='Admin'))
admin.add_view(MBModelView(Role, category='Admin'))

admin.add_view(UserView(User, category='User', endpoint='usermodel'))
admin.add_view(MBModelView(SocialOAuth, category='User'))
admin.add_view(MBModelView(Cart, category='User', endpoint='cartmodel'))
admin.add_view(MBModelView(EntrySpec, category='User'))
admin.add_view(MBModelView(Coupon, category='User'))
admin.add_view(MBModelView(CouponWallet, category='User'))
admin.add_view(MBModelView(OrderEntry, category='User'))
admin.add_view(MBModelView(CoinWallet, category='User'))
admin.add_view(MBModelView(CoinTrade, category='User'))
admin.add_view(MBModelView(Address, category='User', endpoint='addressmodel'))
admin.add_view(MBModelView(GuestRecord, category='User'))

admin.add_view(MBModelView(Item, category='Inventory', endpoint='itemmodel'))
admin.add_view(MBModelView(ItemSpec, category='Inventory'))
admin.add_view(MBModelView(Brand, category='Inventory'))
admin.add_view(MBModelView(Category, category='Inventory'))
admin.add_view(MBModelView(Tag, category='Inventory'))
admin.add_view(MBModelView(Vendor, category='Inventory'))
admin.add_view(MBModelView(PriceHistory, category='Inventory'))
admin.add_view(MBModelView(ForexRate, category='Inventory'))

admin.add_view(MBModelView(Payment, category='Order', endpoint='paymentmodel'))
admin.add_view(MBModelView(LogisticProvider, category='Logistics'))
admin.add_view(MBModelView(ChannelProvider, category='Logistics'))
admin.add_view(MBModelView(Partner, category='Logistics'))
admin.add_view(MBModelView(Order, category='Order'))
admin.add_view(MBModelView(TransferOrderCode, category='Order'))
admin.add_view(MBModelView(OrderExtra, category='Order'))

admin.add_view(MBModelView(Board, category='Content'))
admin.add_view(MBModelView(Post, category='Content'))
admin.add_view(MBModelView(PostComment, category='Content'))
admin.add_view(MBModelView(PostLike, category='Content'))
admin.add_view(MBModelView(PostActivity, category='Content'))
admin.add_view(MBModelView(PostFeedback, category='Content'))
admin.add_view(MBModelView(PostTag, category='Content'))
