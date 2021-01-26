# -*- coding: utf-8  -*-
# @Author: ty
# @File name: user.py 
# @IDE: PyCharm
# @Create time: 1/11/21 3:58 PM
# @Description:
import hashlib
import datetime

from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer

from app import db, bcrypt
from app.config.enum import USER_GENDER, USER_ROLE, NOTIFICATION_TYPE

__all__ = ['User', 'UserInformation', 'UserAccount', 'FavorAction', 'SocialOAuth']

from app.models.cart.cart import Cart
from app.models.coupon.wallet import CouponWallet

from app.models.order.order import Order

from app.models.reward.coin import CoinWallet


class FavorAction(object):
    """

    """
    # fields
    num_favors = db.IntField(default=0, min_value=0)
    favor_items = db.ListField(db.StringField())

    def mark_favored(self, item):
        if item.id not in self.favor_items:
            item.update(inc__num_favors=1, push__favor_items=item.id)
            Signals.mark_favor.send(self, item_id=str(item.id))

    def unmark_favored(self, item):
        if item.id in self.favor_items:
            item.update(dec__num_favors=1)
            self.update(dec__num_favors=1, pull__favor_items=item.id)

    def mark_like(self, post):
        post.update(inc__num_favors=1)
        self.update(inc__num_post_likes=1)

    def mark_unlike(self, post):
        post.update(dec__num_likes=1)
        self.update(dec__num_post_likes=1)


class User(db.Document, UserMixin, FavorAction):
    """"""
    meta = {
        'indexes': ['name', 'account.created_at', 'roles', 'level', 'account.email', 'account.is_email_verified',
                    'is_deleted'],
        'ordering': ['-account.created_at']
    }
    name = db.StringField(required=True)
    account = db.EmbeddedDocumentField('UserAccount')
    information = db.EmbeddedDocumentField('UserInformation')
    avatar_url = db.URLField(default='http://assets.maybe.cn/logo/panda.jpg')
    # level
    # 0: normal user
    # 1: normal member
    # 2: advance member
    # 3: premium member
    # 4: VIP member
    level = db.IntField(default=0)
    roles = db.ListField(db.StringField())
    address = db.ListField(db.ReferenceField('Address'))
    default_address = db.ReferenceField('Address')
    # followers
    num_followers = db.IntField(default=0, min_value=0)
    num_followings = db.IntField(default=0, min_value=0)
    followers = db.ListField(db.ReferenceField('User'))
    followings = db.ListField(db.ReferenceField('User'))

    subscribed_mp = db.BooleanField(default=False)

    # favor related (item_ids)
    num_favors = db.IntField(default=0, min_value=0)
    favor_items = db.ListField(db.IntFidld())

    # favor related (post_ids)
    num_post_likes = db.IntField(default=0, min_value=0)
    like_posts = db.ListField(db.IntField())

    # shopping cart
    cart = db.ReferenceField('Cart')

    # wallet
    wallet = db.ReferenceField('CouponWallet')

    is_deleted = db.BooleanField(default=False)
    deleted_date = db.DateTimeField()

    def __unicode__(self):
        # return '%s' % str(self.id)
        return '{}'.format(self.name)

    @property
    def coin_wallet(self):
        return CoinWallet.get_or_create(user=self)

    @property
    def lucky_money(self):
        return LuckymoneyWallet.by_user(user=self)

    @property
    def orders(self):
        return Order.objects(customer_id=self.id, is_paid=True)

    @property
    def avatar_thumb(self):
        return self.avatar_url[:23] + 'avarat_thumbs/80x80/' + self.avatar_url[23:]

    def used_coupon(self, code):
        return bool(Order.objects(customer_id=self.id, is_paid=True, coupon_codes__contains=code))

    @db.queryset_manager
    def active(doc_cls, queryset):
        return queryset.filter(is_deleted=False)

    @property
    def is_admin(self):
        return USER_ROLE.ADMIN in self.roles

    def follow(self, other):
        if self not in other.followers:
            other.followers.append(self)
            other.num_followers += 1

        if other not in self.followings:
            self.followings.append(other)
            self.num_followings += 1

        self.save()
        other.save()

        signals.site_message.send(self, dest=other.id, source=self, imgs=[self.avatar_url],
                                  noti_type=NOTIFICATION_TYPE.FOLLOW, title='')

    def unfollow(self, other):
        if self in other.followers:
            other.followers.remove(self)
            other.num_followers -= 1

        if other in self.followings:
            self.followings.remove(other)
            self.num_followings -= 1

        self.save()
        other.save()

    def is_following(self, other):
        return other in self.followings

    def to_json(self):
        data = dict(
            name=self.name,
            avatar_url=self.avatar_url,
            avatar_thumb=self.avatar_thumb,
            num_followers=self.num_followers,
            num_followings=self.num_followings,
            created_at=str(self.account.created_at),
            id=str(self.id),
        )
        return data

    @classmethod
    def authenticate(cls, email=None, password=None):
        if email:
            user = cls.active(account__email=email.lower()).first()
        else:
            user = None
        if user:
            authenticated = user.account.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    def generate_auth_token(self, expires_in=604800):
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=expires_in)
        return serializer.dumps({'id': str(self.id)}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except:
            return None

        return User.objects(id=data['id']).first()

    @classmethod
    def create(cls, email, password, name, mobile_number=None):
        # init user account
        cart = Cart()
        cart.save()

        wallet = CouponWallet()
        wallet.save()

        # account
        account = UserAccount(email=email.lower(), mobile_number=mobile_number, is_email_verified=True)
        account.password = password

        user = User(name=name, roles=[USER_ROLE.MEMBER], information=UserInformation(), cart=cart, wallet=wallet,
                    account=account)
        user.save()
        signals.user_signup.send('system', user=user)
        return user

    def mark_deleted(self):
        if self.is_deleted:
            return
        SocialOAuth.objects(user=self).delete()
        self.is_deleted = True
        self.deleted_date = datetime.datetime.utcnow()
        self.save()


class UserAccount(db.EmbeddedDocument):
    """"""
    created_at = db.DateTimeField(default=datetime.datetime.utcnow, required=True)

    # login related
    email = db.EmailField(required=True, unique=True)
    mobile_number = db.StringField()
    is_email_verified = db.BooleanField(default=False)
    _password = db.StringField(max_length=256)
    activate_key_expire_date = db.DateTimeField()

    # password
    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = bcrypt.generate_password_hash(password).decode('utf-8')
        print(self._password)

    def check_password(self, password):
        if self.password is None:
            return False
        return bcrypt.check_password_hash(self.password, password)

    def to_json(self):
        return dict(created_at=str(self.created_at), email=self.email)


class UserInformation(db.EmbeddedDocument):
    """"""
    gender = db.StringField(max_length=1, choices=USER_GENDER)


class SocialOAuth(db.Document):
    """"""
    meta = {
        'indexes': ['site', 'user', ('site_uid', 'site'), 'unionid']
    }
    app = db.StringField(choices=['IOS', 'MOBILEWEB'], default='MOBILEWEB')
    site = db.StringField(max_length=256, required=True)
    site_uid = db.StringField(max_length=256, required=True, unique_with='site')
    unionid = db.StringField()
    user = db.ReferenceField('User')

    site_uname = db.StringField(max_length=256)
    access_token = db.StringField(required=True)
    expire_date = db.DateTimeField()
    refresh_token = db.StringField()

    can_refresh = db.BooleanField(default=True)
    last_active_date = db.DateTimeField()

    def to_json(self):
        return dict(site=self.site, site_uname=self.site_uname)

    @classmethod
    def create(cls, site, site_uid, site_uname, access_token, expires_in=0, refresh_token=None, email=None,
               mobile_number=None, gender=None, password=None, unionid=None, app='MOBILEWEB', is_email_verified=False):
        oauth = cls(site=site, site_uid=site_uid, site_uname=site_uname, access_token=access_token,
                    refresh_token=refresh_token, unionid=unionid, app=app)
        if not email:
            email = '{}-{}@maybe.cn'.format(site, hashlib.md5(app + site + site_uid).encode('utf-8')).hexdigest()

        # create an user
        user = User.create(email=email, mobile_number=mobile_number, password=password or site_uname, name=site_uname)
        user.account.is_email_verified = is_email_verified
        user.information.gender = gender
        if site == 'wechat':
            user.subscribed_mp = True
        user.save()

        oauth.user = user
        oauth.save()
        oauth.update_token(access_token, expires_in)
        return oauth

    def update_token(self, access_token, expires_in=0):
        expire_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in))
        self.update(set__access_token=access_token, set__expire_date=expire_date)

    def re_auth(self, access_token, expires_in, refresh_token=None, unionid=None):
        self.update_token(access_token, expires_in)
        self.update(set__refresh_token=refresh_token)
        if unionid:
            self.update(set__unionid=unionid)

    def update_avatar(self, url):
        self.user.update(set__avatar_url=url)

    @classmethod
    def get_user(cls, site, site_uid):
        obj = cls.objects(site=site, site_uid=site_uid).first()
        return obj.user if obj else None

    @classmethod
    def refresh_active(cls, site, site_uid, dt):
        cls.objects(site=site, site_uid=site_uid).update_one(set__last_active_date=dt)
