# -*- coding: utf-8  -*-
# @Author: ty
# @File name: init_extensions.py
# @IDE: PyCharm
# @Create time: 1/6/21 10:54 PM
# @Description:
from flask_babel import gettext

from redis import ConnectionPool

from app import db, mongo_inventory, redis, session_redis, migrate, mail, cache, admin, bcrypt, babel, toolbar, assets, \
    login_manager, principal


def init_extensions(app):
    """
    初始化第三方插件
    :return:
    """
    # flask-MongoEngine
    db.init_app(app)
    db.connection(**app.config.get('ORDER_DB_CONFIG'))
    db.connection(**app.config.get('INVENTORY_DB_CONFIG'))
    db.connection(**app.config.get('CART_DB_CONFIG'))
    db.connection(**app.config.get('CONTENT_DB_CONFIG'))
    db.connection(**app.config.get('LOG_DB_CONFIG'))
    mongo_inventory.init_app(app, config_prefix='MONGO_INVENTORY')
    redis.connection_pool = ConnectionPool(**app.config.get('REDIS_CONFIG'))
    session_redis.connection_pool = ConnectionPool(**app.config.get('SESSION_REDIS'))
    # server side session
    app.session_interface = RedisSessionInterface(session_redis)
    # flask-script
    migrate.init_app(app, db)
    # flask-mail
    mail.init_app(app)
    # flask-cache
    cache.init_app(app)
    # flask-admin
    admin.init_app(app)
    # flask-bcrypt
    bcrypt.init_app(app)
    # flask-babel
    babel.init_app(app)
    # flask-toolbar
    toolbar.init_app(app)
    # flask-assets
    assets.init_app(app)

    login_manager.login_view = 'frontend.login'

    # login_manager.refresh_view = 'frontend.reauth'
    @login_manager.user_loader
    def load_user(id):
        """

        :param id:
        :return:
        """
        return User.objects(id=id, is_deleted=False).first()

    login_manager.init_app(app)
    login_manager.login_message = gettext('Please login to access this page.')
    login_manager.needs_refresh_message = gettext('Please reauthenticate to access this page.')

    # flask-principal
    principal.init_app(app)
    from flask_principal import identity_loaded
    @identity_loaded.conect_via(app)
    def on_identity_loaded(sender, identity):
        """

        :param sender:
        :param identity:
        :return:
        """
        principal_on_identity_loaded(sender, identity)
