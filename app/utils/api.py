# -*- coding: utf-8  -*-
# @Author: ty
# @File name: api.py 
# @IDE: PyCharm
# @Create time: 1/17/21 9:45 PM
# @Description:
from functools import wraps

from flask import Response, g, render_template, make_response, jsonify, request, current_app, abort


def returns_json(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        res = func(*args, **kwargs)
        return Response(res, content_type='application/json; charset=utf-8')

    return decorated_function


def replace_func_with(func, version_specs, patch=False):
    """
    if any of the version_specs matched, the original func will be replaced.
    :param func: the function to replace the original function
    :param version_specs:  a list of version_specs.
    {'client': 'ios', 'gte': (2, 10)}
    {'client': 'android', 'gt': (1, 12), 'lte': (2, 10)}
    :param patch:
    :return:
    """

    def outer(origin_func):
        @wraps(origin_func)
        def decorated_function(*args, **kwargs):
            version = (g.get('version_major'), g.get('version_minor'))
            client = g.get('client')
            if not any(match_spec(client, version, spec) for spec in version_specs):
                return origin_func(*args, **kwargs)

            if isinstance(func, basestring):
                new_func = get_func_from_str(func, args)
                new_args = args[1:]
            else:
                new_func = func
                new_args = args
            if not new_func:
                return origin_func(*args, **kwargs)
            if patch:
                return new_func(origin_func(*args, **kwargs))
            return new_func(*new_args, **kwargs)

        return decorated_function

    return outer


def get_func_from_str(func, args):
    """

    :param func:
    :param args:
    :return:
    """
    if not args:
        return
    first_arg = args[0]
    try:
        return getattr(first_arg, func)
    except AttributeError:
        return


def patch_func_with(func, version_specs):
    """

    :param func:  the function to patch the original function.
        Called after the original function is called.
    :param version_specs: a list of version_spec.if any of the version_spec matched. the original func will be patch.
    :return:
    """

    def outer(origin_func):
        @wraps(origin_func)
        def decorated_function(*args, **kwargs):
            version = (g.get('version_major'), g.get('version_minor'))
            client = g.get('client')
            if any(match_spec(client, version, spec) for spec in version_specs):
                return func(origin_func(*args, **kwargs))
            else:
                return origin_func(*args, **kwargs)

        return decorated_function

    return outer


def match_spec(client, version, version_spec):
    """

    :param client:
    :param version:
    :param version_spec:
    :return:
    """
    if client != version_spec.get('client', ''):
        return False
    return all(match_version(k, v, version) for k, v in version_spec.items() if k != 'client')


def match_version(k, v, version):
    """

    :param k:
    :param v:
    :param version:
    :return:
    """
    return any((
        (k == 'gt' and version > v),
        (k == 'lt' and version < v),
        (k == 'eq' and version == v),
        (k == 'get' and version >= v),
        (k == 'lte' and version <= v),
    ))


def render_api_template(filename, *args, **kwargs):
    """

    :param filename:
    :param args:
    :param kwargs:
    :return:
    """
    filename = (g.get('client') or 'android') + '/' + filename
    return render_template(filename, *args, **kwargs)


def cache_control(*directives):
    """
    insert a cache-control header with the given directives.
    :param directives:
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # invoke the wrapped function
            rv = func(*args, **kwargs)
            # convert the returned value to a response object
            rv = make_response(rv)
            # insert the Cache-Control header and return response
            rv.headers['Cache-Control'] = ', '.join(directives)
            return rv

        return wrapped

    return decorator


def no_cache(func):
    """
    insert a no-cache directive in the response. this decorator just invokes the cache-control decorator with the specific directives.
    :param func:
    :return:
    """
    return cache_control('private', 'no-cache', 'no-store', 'max-age=0')(func)


def open_json(func):
    """
    generate a json response from a database model or a python dictionary.
    :param func:
    :return:
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        # invoke the wrapped function.
        rv = func(*args, **kwargs)
        # the wrapped function can return the dictionary alone, or can also include a status code and / or headers. here we separate all these items.
        status = None
        headers = None
        if isinstance(rv, tuple):
            rv, status, headers = rv + (None,) * (3 - len(rv))
        if isinstance(status, (dict, list)):
            headers, status = status, None

        if rv is None:
            rv = jsonify({'status': 416, 'error': 'not match', 'message': 'object does not exist'})
            rv.status_code = 416
            return rv

        # if the response was a database model, then convert it to a dictionary
        if not isinstance(rv, dict):
            rv = rv.to_open_json()

        # generate the json response
        rv = jsonify(rv)
        if status is not None:
            rv.status_code = status
        if headers is not None:
            rv.headers.extend(headers)
        return rv

    return wrapped


def paginate(collection, max_per_page=25):
    """

    :param collection:
    :param max_per_page:
    :return:
    """

    def decorator(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            # 函数引用
            query = function(*args, **kwargs)
            # 获取参数
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', max_per_page, type=int), max_per_page)
            # run the query with flask-mongoengine's pagination
            p = query.paginate(page, per_page)
            # build the pagination collection as a dictionary
            pages = {'page': page, 'per_page': per_page, 'total': p.total, 'pages': p.pages}
            # generate the paginated collection as a dictionary
            results = [item.to_open_json() for item in p.items]
            # return a dictionary as a response
            return {collection: results, 'meta': pages}

        return wrapped

    return decorator


def rate_limit(limit, per, scope_func=lambda: request.remote_addr):
    """
    limits the rate at which clients can send requests to 'limit' requests per 'period' seconds.
    once a client goes over the limit all requests are answered with a status code 429 too many requests for the remaining of that period.
    :param limit:
    :param per:
    :param scope_func:
    :return:
    """

    # 限流
    # 装饰器
    def decorator(function):
        # 包装函数
        @wraps(function)
        def wrapped(*args, **kwargs):
            if current_app.config['USER_RATE_LIMITS']:
                key = 'rate-limit/%s/%s/' % (function.__name__, scope_func())
                limiter = RateLimit(key, limit, per)
                if not limiter.over_limit:
                    rv = function(*args, **kwargs)
                else:
                    rv = jsonify(
                        {'status': 429, 'error': 'too many requests', 'message': 'you have exceeded your request rate'})
                    rv.status_code = 429
                    return rv
                # rv = make_response(rv)
                g.headers = {
                    'X-RateLimit-Remaining': str(limiter.remaining),
                    'X-RateLimit-Limit': str(limiter.limit),
                    'X-RateLimit-Reset': str(limiter.reset),
                }
                return rv
            else:
                return function(*args, **kwargs)

        return wrapped

    return decorator


def permission(function):
    """
    权限
    :param function:
    :return:
    """

    @wraps(function)
    def wrapped(*args, **kwargs):
        api_granted = function.__name__ in g.user.permissions
        if not api_granted:
            abort(405)

        params = filter(lambda p: p.api == function.__name__, g.user.permissions)[0].allowed_params
        if params:
            if not request.args.keys():
                abort(403)
            for k in request.args.keys():
                param = params.get(k)
                if param and request.args.get(k) not in param:
                    abort(403)

        if set(request.args.keys()).intersection(['page', 'pages']) and not set(request.args.keys()).intersection(
                params.keys()):
            abort(403)

        rv = function(*args, **kwargs)
        return rv

    return wrapped
