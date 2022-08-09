# -*- coding: utf-8 -*-
# author: 63720750@qq.com
# website: http://appnxt.com
import os
import odoo
from odoo import api, http, SUPERUSER_ID, _, registry
# from odoo.modules.registry import RegistryManager
import werkzeug
import base64
import time
import json
import ast
import logging
import pdb
import re
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from passlib.context import CryptContext

import datetime
import platform
from hashlib import md5

_logger = logging.getLogger(__name__)

default_crypt_context = CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'md5_crypt'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['md5_crypt'],
)
###############################
#
# Odoo Nxt Restful API Method.
#
###############################
import _ast
import re
import csv

try:  # Python 3
    import configparser
    from threading import current_thread
    from xmlrpc.client import Fault, ServerProxy, MININT, MAXINT

    PY2 = False
except ImportError:  # Python 2
    import ConfigParser as configparser
    from threading import currentThread as current_thread
    from xmlrpclib import Fault, ServerProxy, MININT, MAXINT

    PY2 = True

DOMAIN_OPERATORS = frozenset('!|&')
_term_re = re.compile(
    '([\w._]+)\s*'  '(=(?:like|ilike|\?)|[<>]=?|!?=(?!=)'
    '|(?<= )(?:like|ilike|in|not like|not ilike|not in|child_of))'  '\s*(.*)')


# Simplified ast.literal_eval which does not parse operators
def _convert(node, _consts={'None': None, 'True': True, 'False': False}):
    if isinstance(node, _ast.Str):
        return node.s
    if isinstance(node, _ast.Num):
        return node.n
    if isinstance(node, _ast.Tuple):
        return tuple(map(_convert, node.elts))
    if isinstance(node, _ast.List):
        return list(map(_convert, node.elts))
    if isinstance(node, _ast.Dict):
        return dict([(_convert(k), _convert(v))
                     for (k, v) in zip(node.keys, node.values)])
    if hasattr(node, 'value') and str(node.value) in _consts:
        return node.value  # Python 3.4+
    if isinstance(node, _ast.Name) and node.id in _consts:
        return _consts[node.id]  # Python <= 3.3
    raise ValueError('malformed or disallowed expression')


if PY2:
    int_types = int, long


    class _DictWriter(csv.DictWriter):
        """Unicode CSV Writer, which encodes output to UTF-8."""

        def writeheader(self):
            # Method 'writeheader' does not exist in Python 2.6
            header = dict(zip(self.fieldnames, self.fieldnames))
            self.writerow(header)

        def _dict_to_list(self, rowdict):
            rowlst = csv.DictWriter._dict_to_list(self, rowdict)
            return [cell.encode('utf-8') if hasattr(cell, 'encode') else cell
                    for cell in rowlst]
else:  # Python 3
    basestring = str
    int_types = int
    _DictWriter = csv.DictWriter


def literal_eval(expression, _octal_digits=frozenset('01234567')):
    node = compile(expression, '<unknown>', 'eval', _ast.PyCF_ONLY_AST)
    if expression[:1] == '0' and expression[1:2] in _octal_digits:
        raise SyntaxError('unsupported octal notation')
    value = _convert(node.body)
    if isinstance(value, int_types) and not MININT <= value <= MAXINT:
        raise ValueError('overflow, int exceeds XML-RPC limits')
    return value


def searchargs(params, kwargs=None, context=None):
    """Compute the 'search' parameters."""

    if not params:
        return ([],)
    domain = params[0]
    if not isinstance(domain, list):
        return params
    for (idx, term) in enumerate(domain):
        if isinstance(term, basestring) and term not in DOMAIN_OPERATORS:
            m = _term_re.match(term.strip())
            if not m:
                raise ValueError('Cannot parse term %r' % term)
            (field, operator, value) = m.groups()
            try:
                value = literal_eval(value)
            except Exception:
                # Interpret the value as a string
                pass
            domain[idx] = (field, operator, value)
    return domain


def issearchdomain(arg):
    """Check if the argument is a search domain.

    Examples:
      - ``[('name', '=', 'mushroom'), ('state', '!=', 'draft')]``
      - ``['name = mushroom', 'state != draft']``
      - ``[]``
    """
    return isinstance(arg, list) and not (arg and (
        # Not a list of ids: [1, 2, 3]
            isinstance(arg[0], int_types) or
            # Not a list of ids as str: ['1', '2', '3']
            (isinstance(arg[0], basestring) and arg[0].isdigit())))


def check_sign(token, kw):
    data = list(kw.keys())[0].replace('null', '""').replace('true', '""')
    sign = ast.literal_eval(data).get("sign")
    appkey = ast.literal_eval(data).get("appkey")
    timestamp = ast.literal_eval(data).get("timestamp")
    format = ast.literal_eval(data).get("format")
    check_req_str = odoo.tools.config["api_key"] + format + token + str(timestamp) + appkey + odoo.tools.config[
        "api_key"]
    md5_obj = md5()
    md5_obj.update(check_req_str.encode(encoding='utf-8'))
    check_sign_str = md5_obj.hexdigest()
    return check_sign_str == sign


def no_sign():
    rp = {'status': '401', 'result': '', 'success': False, 'message': 'invalid sign!'}
    return json_response(rp)


def no_token():
    rp = {'status': '401', 'result': '', 'success': False, 'message': 'invalid token!'}
    return json_response(rp)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        from datetime import date, datetime
        from decimal import Decimal
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def json_response(rp):
    # rp_ = json.dumps(rp).replace('False','')
    headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}
    return werkzeug.wrappers.Response(json.dumps(rp, ensure_ascii=False, cls=MyEncoder).replace("false", '""'),
                                      mimetype='application/json',
                                      headers=headers)


def authenticate(token):
    try:
        a = 4 - len(token) % 4
        if a != 0:
            token += '==' if a == 2 else '='
        SERVER, db, login, uid, ts = base64.urlsafe_b64decode(str(token).encode()).decode().split(',')
        if int(ts) + 60 * 60 * 24 * 7 * 10 < time.time():
            return False
        cr = registry(db).cursor()
        # = registry.cursor()
        env = api.Environment(cr, int(uid), {})
        request.uid = uid
    except Exception as e:
        return str(e)
    return env


from .controllers_base import Base


class XlCrm(http.Controller, Base):
    def get_attribute_value_ids(self, product):
        """ list of selectable attributes of a product

        :return: list of product variant description
           (variant id, [visible attribute ids], variant price, variant sale price)
        """
        # product attributes with at least two choices
        quantity = product._context.get('quantity') or 1
        product = product.with_context(quantity=quantity)

        visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
            'attribute_id').ids

        attribute_value_ids = []
        for variant in product.product_variant_ids:
            price = variant.website_public_price / quantity
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids if
                                     v.attribute_id.id in visible_attrs_ids]
            attribute_value_ids.append([variant.id, visible_attribute_ids, variant.website_price, price])

        product_attribute = request.env['product.attribute']
        attributes = product_attribute.sudo().search(attribute_value_ids)

        return attributes

    @http.route([
        '/api/v11/getuserlist'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_user_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 5000
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("username"):
                domain.append(('username', 'like', queryFilter.get("username")))
            if queryFilter and queryFilter.get("nickname"):
                domain.append(('nickname', 'like', queryFilter.get("nickname")))
            if queryFilter and queryFilter.get("group_id"):
                domain.append(('group_id', '=', queryFilter.get("group_id")))
            if queryFilter and queryFilter.get("department_id"):
                domain.append(('department_id', '=', queryFilter.get("department_id")))
            if queryFilter and queryFilter.get("status"):
                domain.append(('status', '=', queryFilter.get("status")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if len(domain) == 0:
            domain = [('write_uid', '=', 1)]
        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env["xlcrm.users"].sudo().search_count(domain)
            result = request.env["xlcrm.users"].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env["xlcrm.users"].fields_get()
            for r in result:
                for f in r.keys():
                    # print(f)
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            # print result
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getUserListSelection'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_user_list_selection(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 500
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            result = request.env["xlcrm.users"].sudo().search_read([('status', '=', 1)],
                                                                   ['id', 'parent_ids', 'parent_user_nicknames',
                                                                    'parent_user_names', 'group_id', 'nickname',
                                                                    'username'], 0, 0,
                                                                   order='id desc')
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v10/usergroupstatusupdate'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def user_group_status_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        group_id = ast.literal_eval(list(kw.keys())[0]).get("group_id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if group_id:
                records_ref = env['xlcrm.user.group'].sudo().search([("id", 'in', group_id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/statusupdate/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def status_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        ids = ast.literal_eval(list(kw.keys())[0]).get("ids")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if ids:
                records_ref = env[model].sudo().search([("id", 'in', ids)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/UpdateSortValue/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def update_sort_value(self, model=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        obj_id = ast.literal_eval(list(kw.keys())[0]).get("id")
        sort_value = ast.literal_eval(list(kw.keys())[0]).get("sortValue")
        try:
            if obj_id:
                records_ref = env[model].sudo().search([("id", '=', obj_id)])
                values = {
                    "sort": sort_value,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/userstatusupdate'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def user_status_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        user_id = ast.literal_eval(list(kw.keys())[0]).get("user_id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if user_id:
                records_ref = env['xlcrm.users'].sudo().search([("id", 'in', user_id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/userpsdupdate'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def user_psd_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        user_id = ast.literal_eval(list(kw.keys())[0]).get("user_id")
        password = ast.literal_eval(list(kw.keys())[0]).get("password")
        try:
            if user_id:
                records_ref = env['xlcrm.users'].sudo().search([("id", '=', user_id)])
                values = {
                    "password": self._crypt_context().encrypt(password)
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/setUserPasswordBySelf'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def user_psd_update_by_self(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        user_id = env.uid
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        password_new = data["password"]
        password_old = data["password_old"]
        try:
            if user_id and password_old:
                records_ref = env['xlcrm.users'].sudo().search([("id", '=', user_id)])
                valid_pass = False
                encrypted = records_ref['password']
                valid_pass, replacement = self._crypt_context().verify_and_update(password_old, encrypted)
                if valid_pass:
                    values = {
                        "password": self._crypt_context().encrypt(password_new),
                        # "email_password": data["email_password"]
                    }
                    result = records_ref.sudo().write(values)
                    env.cr.commit()
                    success = True
                    message = 'success!'

                else:
                    success = False
                    message = '原密码不正确！'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/setUserEmailPasswordBySelf'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def user_epsd_update_by_self(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        user_id = env.uid
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        email_password = data["email_password"]
        try:
            if user_id and email_password:
                records_ref = env['xlcrm.users'].sudo().search([("id", '=', user_id)])
                if records_ref:
                    values = {
                        "email_password": data["email_password"]
                    }
                    result = records_ref.sudo().write(values)
                    env.cr.commit()
                    success = True
                    message = 'success!'

                else:
                    success = False
                    message = '帐号不存在！'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/<string:model>',
        '/api/v11/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def read_objects_11(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        domain = []
        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            domain = []
            if queryFilter and queryFilter.get("name"):
                domain.append(('name', 'like', queryFilter.get("name")))
            if queryFilter and queryFilter.get("level_id"):
                domain.append(('level_id', '=', queryFilter.get("level_id")))
            if queryFilter and queryFilter.get("category_id"):
                domain.append(('category_id', '=', queryFilter.get("category_id")))
            if queryFilter and queryFilter.get("region_id"):
                domain.append(('region_id', '=', queryFilter.get("region_id")))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = '操作成功！'
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerList'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            domain = []
            if queryFilter and queryFilter.get("name"):
                domain += ['|']
                domain.append(('name', 'like', queryFilter.get("name")))
                domain += ['|']
                domain.append(('customer_no', 'like', queryFilter.get("name")))
                domain += ['|']
                domain.append(('customer_no_third', 'like', queryFilter.get("name")))
                domain.append(('phone', 'like', queryFilter.get("name")))
            if queryFilter and queryFilter.get("level_id"):
                domain.append(('level_id', '=', queryFilter.get("level_id")))
            if queryFilter and queryFilter.get("category_id"):
                domain.append(('category_id', '=', queryFilter.get("category_id")))
            if queryFilter and queryFilter.get("region_id"):
                domain.append(('region_id', '=', queryFilter.get("region_id")))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("order_field"):
                condition = queryFilter.get("order_field")
                if condition == "create_user_nick_name":
                    condition = 'create_user_id'
                order = condition + " " + queryFilter.get("order_type")

        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]
            count = request.env["xlcrm.customer"].sudo().search_count(domain)
            result = request.env["xlcrm.customer"].sudo().search_read(domain, fields, offset * limit, limit, order)

            model_fields = request.env["xlcrm.customer"].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = '操作成功！'
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerDetailById/<string:model>',
        '/api/v11/getCustomerDetailById/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_detail_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                result = request.env[model].sudo().search_read(domain)
                if result:
                    obj_temp = result[0]
                    if (obj_temp["phone"] == False):
                        obj_temp["phone"] = ''
                    if (obj_temp["owner"] == False):
                        obj_temp["owner"] = ''
                    if (obj_temp["address"] == False):
                        obj_temp["address"] = ''
                    if (obj_temp["email"] == False):
                        obj_temp["email"] = ''
                    if (obj_temp["email"] == False):
                        obj_temp["email"] = ''
                    if (obj_temp["products"] == False):
                        obj_temp["products"] = ''
                    if (obj_temp["customer_no"] == False):
                        obj_temp["customer_no"] = ''
                    if (obj_temp["customer_no_third"] == False):
                        obj_temp["customer_no_third"] = ''
                    if (obj_temp["short_name"] == False):
                        obj_temp["short_name"] = ''
                    if (obj_temp["desc"] == False):
                        obj_temp["desc"] = ''
                    if (obj_temp["record_status"] == False):
                        obj_temp["record_status"] = ''

                    ret_temp = {
                        "id": obj_temp["id"],
                        "name": obj_temp["name"],
                        "short_name": obj_temp["short_name"],
                        "email": obj_temp["email"],
                        "phone": obj_temp["phone"],
                        "owner": obj_temp["owner"],
                        "address": obj_temp["address"],
                        "capital": obj_temp["capital"],
                        "products": obj_temp["products"],
                        "level_id": obj_temp["level_id"],
                        "category_id": obj_temp["category_id"],
                        "status_id": obj_temp["status_id"],
                        "industry_id": obj_temp["industry_id"],
                        "currency_type_id": obj_temp["currency_type_id"],
                        "revenue_id": obj_temp["revenue_id"],
                        "scope_id": obj_temp["scope_id"],
                        "avatar_url": obj_temp["avatar_url"],
                        "avatar_id": obj_temp["avatar_id"],
                        "is_focused": obj_temp["is_focused"],
                        "create_user_name": obj_temp["create_user_name"],
                        "customer_no": obj_temp["customer_no"],
                        "customer_no_third": obj_temp["customer_no_third"],
                        "desc": obj_temp["desc"],
                        "record_status": obj_temp["record_status"]
                    }
                success = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': ret_temp}
        return json_response(rp)

    @http.route([
        '/api/v11/createCustomer',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_customer(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            data["customer_no"] = "CS" + str(env['xlcrm.customer'].get_customer_max_number()).zfill(6)
            create_id = env["xlcrm.customer"].sudo().create(data).id
            result_object = env["xlcrm.customer"].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env["xlcrm.customer"].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''

            operation_log = {
                'name': '新增客户：' + result_object['name'],
                'operator_user_id': env.uid,
                'content': '新增客户：' + result_object['name'],
                'res_id': result_object['id'],
                'res_model': 'xlcrm.customer',
                'res_id_related': result_object['id'],
                'res_model_related': 'xlcrm.customer',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)
            # 邮件知会
            email_uid = env['xlcrm.users'].sudo().search_read([('id', 'in', data['email_notification'])],
                                                              fields=['email'])
            email_user = map(lambda x: x['email'], email_uid) if email_uid else []
            from ..public import send_email
            send_result = True
            for index, em in enumerate(email_user):
                token = get_token(data['email_notification'][index])
                href = request.httprequest.environ["HTTP_ORIGIN"] + '/#/public/crm-customer-list/' + str(
                    create_id) + "/" + json.dumps(token)
                content = """
                            <html lang="en">            
                            <body>
                                <div>
                                    您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;""" + result_object[
                    'create_user_nick_name'] + """创建了""" + result_object['name'] + """客户，请点击
                                    <a href='""" + href + """' ><font color="red">链接</font></a>查看。
                                </div>
                                <div>
                                <br>
                                注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>,用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                                </div>
                            </body>
                            </html>
                            """
                send = send_email.Send_email().send(to=[em], subject='客户创建成功通知', content=content, env=env)
                if send.get('code') == 500:
                    send_result = False
                    break
            success = False
            message = "新增失败！"
            if send_result:
                env.cr.commit()
                success = True
                message = "新增成功！"

        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importCustomerItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_customer_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            if data.has_key('currency_name'):
                objCurrency = env['xlcrm.currency.type'].sudo().search([('name', '=', data['currency_name'])], limit=1)
                if objCurrency:
                    data['currency_type_id'] = objCurrency['id']
            if data.has_key('create_user_name'):
                objCreatedUser = env['xlcrm.users'].sudo().search([('nickname', '=', data['create_user_name'])],
                                                                  limit=1)
                if objCreatedUser:
                    data['create_user_id'] = objCreatedUser['id']
            if not data.has_key('create_user_id'):
                data["create_user_id"] = env.uid
            objCustomer = env['xlcrm.customer'].sudo().search([('name', '=', data['name'])], limit=1)
            if objCustomer:
                # del data['create_user_id']
                env["xlcrm.customer"].sudo().browse(objCustomer['id']).write(data)
            else:
                data["customer_no"] = "CS" + str(env['xlcrm.customer'].get_customer_max_number()).zfill(6)
                create_id = env["xlcrm.customer"].sudo().create(data).id
                operation_log = {
                    'name': '客户导入：' + data['name'],
                    'operator_user_id': env.uid,
                    'content': '客户导入：' + data['name'],
                    'operation_category': '客户导入',
                    'operation_result': 'success',
                    'res_id': create_id,
                    'res_model': 'xlcrm.customer',
                    'res_id_related': create_id,
                    'res_model_related': 'xlcrm.customer',
                    'create_user_id': data["create_user_id"],
                    'operation_level': 0,
                    'operation_type': 0
                }
                env["xlcrm.operation.log"].sudo().create(operation_log)
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importUserItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_user_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            psd = self._crypt_context().encrypt('Sunray2020')
            data['password'] = psd
            data["create_user_id"] = env.uid
            if data.has_key('user_group_name'):
                objGroup = env['xlcrm.user.group'].sudo().search([('name', '=', data['user_group_name'])], limit=1)
                if objGroup:
                    data['group_id'] = objGroup['id']
            if data.has_key('department_name'):
                objDepartment = env['sdo.department'].sudo().search([('name', '=', data['department_name'])], limit=1)
                if objDepartment:
                    data['department_id'] = objDepartment['id']
            if data.has_key('parent_user_names'):
                lstPartents = data['parent_user_names'].split(' ')
                objParentUsers = env['xlcrm.users'].sudo().search([('username', 'in', lstPartents)]).ids
                if objParentUsers:
                    data['parent_ids'] = [[6, 0, objParentUsers]]
            objUser = env['xlcrm.users'].sudo().search([('username', '=', data['username'])], limit=1)
            if objUser:
                pwd = data.pop('password')
                env["xlcrm.users"].sudo().browse(objUser['id']).write(data)
            else:
                create_id = env["xlcrm.users"].sudo().create(data).id
            # username = data['username'].strip()
            # nickname = data['nickname'].strip()
            # user=env['xlcrm.users'].sudo().search_read([('username','=',username)])
            # if user:
            #     env["xlcrm.users"].sudo().browse(user[0]['id']).write({'status':0})
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importProductItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_product_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            if data.has_key('category_name'):
                objCategory = env['sdo.product.category'].sudo().search([('name', '=', data['category_name'])], limit=1)
                if objCategory:
                    data['category_id'] = objCategory['id']
            if data.has_key('brand_name'):
                objBrand = env['sdo.product.brand'].sudo().search([('name', '=', data['brand_name'])], limit=1)
                if objBrand:
                    data['brand_id'] = objBrand['id']
            if data.has_key('department_name'):
                objDep = env['sdo.department'].sudo().search([('name', '=', data['department_name'])], limit=1)
                if objDep:
                    data['department_id'] = objDep['id']
            objProduct = env['sdo.product'].sudo().search([('product_no', '=', data['product_no'])], limit=1)
            if objProduct:
                env["sdo.product"].sudo().browse(objProduct['id']).write(data)
            else:
                create_id = env["sdo.product"].sudo().create(data).id
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importProductCategoryItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_product_category_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            if data.has_key('parent_name'):
                objParentCategory = env['sdo.product.category'].sudo().search([('name', '=', data['parent_name'])],
                                                                              limit=1)
                if objParentCategory:
                    data['parent_id'] = objParentCategory['id']
            objCategory = env['sdo.product.category'].sudo().search([('name', '=', data['name'])], limit=1)
            if objCategory:
                env["sdo.product.category"].sudo().browse(objCategory['id']).write(data)
            else:
                create_id = env["sdo.product.category"].sudo().create(data).id
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importBrandItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_brand_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            objCategory = env['sdo.product.brand'].sudo().search([('name', '=', data['name'])], limit=1)
            if objCategory:
                env["sdo.product.brand"].sudo().browse(objCategory['id']).write(data)
            else:
                create_id = env["sdo.product.brand"].sudo().create(data).id
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerAllInfoById'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_all_info_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                basic_info, level_list, category_list, status_list, industry_list, scope_list, revenue_list \
                    = '', '', '', '', '', '', ''
                result_basic_info = request.env["xlcrm.customer"].sudo().search_read(domain)
                if result_basic_info:
                    obj_temp = result_basic_info[0]
                    if (obj_temp["phone"] == False):
                        obj_temp["phone"] = ''
                    if (obj_temp["owner"] == False):
                        obj_temp["owner"] = ''
                    if (obj_temp["address"] == False):
                        obj_temp["address"] = ''
                    if (obj_temp["email"] == False):
                        obj_temp["email"] = ''
                    if (obj_temp["email"] == False):
                        obj_temp["email"] = ''
                    if (obj_temp["products"] == False):
                        obj_temp["products"] = ''
                    if (obj_temp["customer_no"] == False):
                        obj_temp["customer_no"] = ''
                    if (obj_temp["customer_no_third"] == False):
                        obj_temp["customer_no_third"] = ''
                    if (obj_temp["short_name"] == False):
                        obj_temp["short_name"] = ''
                    if (obj_temp["desc"] == False):
                        obj_temp["desc"] = ''
                    if (obj_temp["record_status"] == False):
                        obj_temp["record_status"] = ''

                    basic_info = {
                        "id": obj_temp["id"],
                        "name": obj_temp["name"],
                        "short_name": obj_temp["short_name"],
                        "email": obj_temp["email"],
                        "phone": obj_temp["phone"],
                        "owner": obj_temp["owner"],
                        "address": obj_temp["address"],
                        "capital": obj_temp["capital"],
                        "capital_currency": obj_temp["capital_currency"],
                        "products": obj_temp["products"],
                        "level_id": obj_temp["level_id"],
                        "category_id": obj_temp["category_id"],
                        "status_id": obj_temp["status_id"],
                        "industry_id": obj_temp["industry_id"],
                        "revenue_id": obj_temp["revenue_id"],
                        "currency_type_id": obj_temp["currency_type_id"],
                        "scope_id": obj_temp["scope_id"],
                        "avatar_url": obj_temp["avatar_url"],
                        "avatar_id": obj_temp["avatar_id"],
                        "hot": obj_temp["hot"],
                        "is_focused": obj_temp["is_focused"],
                        "create_user_name": obj_temp["create_user_name"],
                        "create_user_nick_name": obj_temp["create_user_nick_name"],
                        "customer_no": obj_temp["customer_no"],
                        "customer_no_third": obj_temp["customer_no_third"],
                        "desc": obj_temp["desc"],
                        "record_status": obj_temp["record_status"]
                    }

                level_list = request.env["xlcrm.customer.level"].sudo(). \
                    search_read([('status', '=', '1')], ['id', 'name', 'sort'], 0, 0, order='id desc')
                category_list = request.env["xlcrm.customer.category"].sudo().search_read([('status', '=', '1')],
                                                                                          ['id', 'name', 'sort'], 0, 0,
                                                                                          order='id desc')
                status_list = request.env["xlcrm.customer.status"].sudo().search_read([('status', '=', '1')],
                                                                                      ['id', 'name', 'sort'], 0, 0,
                                                                                      order='id desc')
                industry_list = request.env["xlcrm.customer.industry"].sudo().search_read([('status', '=', '1')],
                                                                                          ['id', 'name', 'sort'], 0, 0,
                                                                                          order='id desc')
                scope_list = request.env["xlcrm.customer.scope"].sudo().search_read([('status', '=', '1')],
                                                                                    ['id', 'name', 'sort'], 0, 0,
                                                                                    order='id desc')
                revenue_list = request.env["xlcrm.customer.revenue"].sudo().search_read([('status', '=', '1')],
                                                                                        ['id', 'name', 'sort'], 0, 0,
                                                                                        order='id desc')
                currency_type_list = request.env["xlcrm.currency.type"].sudo().search_read([('status', '=', '1')],
                                                                                           ['id', 'name', 'sort'], 0, 0,
                                                                                           order='id desc')

                result = {
                    'basic_info': basic_info,
                    'level_list': level_list,
                    'category_list': category_list,
                    'status_list': status_list,
                    'industry_list': industry_list,
                    'scope_list': scope_list,
                    'revenue_list': revenue_list,
                    'currency_type_list': currency_type_list
                }

                success = True
                message = 'success'
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerOptional'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_optional(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            level_list, category_list, status_list, industry_list, scope_list, revenue_list \
                = '', '', '', '', '', ''

            level_list = request.env["xlcrm.customer.level"].sudo(). \
                search_read([('status', '=', '1')], ['id', 'name', 'sort'], 0, 0, order='id desc')
            category_list = request.env["xlcrm.customer.category"].sudo().search_read([('status', '=', '1')],
                                                                                      ['id', 'name', 'sort'], 0, 0,
                                                                                      order='id desc')
            status_list = request.env["xlcrm.customer.status"].sudo().search_read([('status', '=', '1')],
                                                                                  ['id', 'name', 'sort'], 0, 0,
                                                                                  order='id desc')
            industry_list = request.env["xlcrm.customer.industry"].sudo().search_read([('status', '=', '1')],
                                                                                      ['id', 'name', 'sort'], 0, 0,
                                                                                      order='id desc')
            scope_list = request.env["xlcrm.customer.scope"].sudo().search_read([('status', '=', '1')],
                                                                                ['id', 'name', 'sort'], 0, 0,
                                                                                order='id desc')
            revenue_list = request.env["xlcrm.customer.revenue"].sudo().search_read([('status', '=', '1')],
                                                                                    ['id', 'name', 'sort'], 0, 0,
                                                                                    order='id desc')
            currency_type_list = request.env["xlcrm.currency.type"].sudo().search_read([('status', '=', '1')],
                                                                                       ['id', 'name', 'sort'], 0, 0,
                                                                                       order='id desc')
            max_customer_number = env['xlcrm.customer'].get_customer_max_number()
            result = {
                'level_list': level_list,
                'category_list': category_list,
                'status_list': status_list,
                'industry_list': industry_list,
                'scope_list': scope_list,
                'revenue_list': revenue_list,
                'currency_type_list': currency_type_list,
                'default_customer_no': "CS" + str(max_customer_number).zfill(6)
            }
            success = True
            message = 'success'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getDefaultProjectNo'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_default_project_no(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            max_project_number = env['xlcrm.project'].get_project_max_number()
            result = {
                'default_project_no': "PR" + str(max_project_number).zfill(6)
            }
            success = True
            message = 'success'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerContactList'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_contact_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            domain = []
            if queryFilter and queryFilter.get("project_id"):
                domain.append(('project_id', '=', queryFilter.get("project_id")))
            else:
                if queryFilter and queryFilter.get("customer_id"):
                    domain.append(('customer_id', '=', queryFilter.get("customer_id")))

            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")
        if not domain:
            domain = [('write_uid', '=', 1)]
        domain = searchargs(domain)
        try:
            count = request.env["xlcrm.customer.contact"].sudo().search_count(domain)
            result_all = request.env["xlcrm.customer.contact"].sudo().search_read(domain, fields, offset * limit, limit,
                                                                                  order)
            result = []
            if result_all:
                for contact in result_all:
                    province_id, city_id, district_id, province_name, city_name, district_name = '', '', '', '', '', ''
                    if contact['province_id']:
                        province_id = contact['province_id'][0]
                    if contact['city_id']:
                        city_id = contact['city_id'][0]
                    if contact['district_id']:
                        district_id = contact['district_id'][0]
                    if contact['province_name']:
                        province_name = contact['province_name']
                    if contact['city_name']:
                        city_name = contact['city_name']
                    if contact['district_name']:
                        district_name = contact['district_name']
                    result.append({
                        'id': contact['id'],
                        'name': contact['name'],
                        'title': contact['title'],
                        'mobile': contact['mobile'],
                        'phone': contact['phone'],
                        'province_id': province_id,
                        'city_id': city_id,
                        'district_id': district_id,
                        'qq': contact['qq'],
                        'wechat': contact['wechat'],
                        'email': contact['email'],
                        'dingding': contact['dingding'],
                        'is_default': contact['is_default'],
                        'address': contact['address'],
                        'gender': contact['gender'],
                        'birthday': contact['birthday'],
                        'customer_id': contact['customer_id'],
                        'province_name': contact['province_name'],
                        'city_name': contact['city_name'],
                        'district_name': contact['district_name'],
                        'regions': province_name + " " + city_name + " " + district_name,
                        'create_user_name': contact['create_user_name'],
                        "avatar_url": contact["avatar_url"],
                        "avatar_id": contact["avatar_id"]
                    })
            message = '操作成功！'
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectDetailById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_detail_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                result = request.env[model].sudo().search_read(domain)
                if result:
                    obj_temp = result[0]
                    model_fields = request.env[model].fields_get()
                    for f in obj_temp.keys():
                        if model_fields[f]['type'] == 'many2one':
                            if obj_temp[f]:
                                obj_temp[f] = {'id': obj_temp[f][0], 'display_name': obj_temp[f][1]}
                            else:
                                obj_temp[f] = ''
                    obj_stage_change_list = request.env["sdo.project.stage.change"].sudo().search_read(
                        [('id', 'in', obj_temp['stage_change_list_ids'])], ['id', 'stage_id', 'stage_name',
                                                                            'operation_date_time',
                                                                            'operation_user_name', 'duration_effort'],
                        0, 0, order='id desc')
                    reviewers = ast.literal_eval(obj_temp["reviewers"]) if obj_temp["reviewers"] else {}
                    if not reviewers:
                        attend_users = obj_temp["project_attend_user_ids"]
                        for user in attend_users:
                            user_res = env['xlcrm.users'].sudo().search_read([('id', '=', user)])[0]['group_id']
                            reviewers[user_res[1]] = [user]
                    # if not reviewers.get('Manage'):
                    #     reviewers['Manage'] = obj_temp["create_user_id"]
                    ret_temp = {
                        "id": obj_temp["id"],
                        "name": obj_temp["name"],
                        "project_no": obj_temp["project_no"],
                        "application": obj_temp["application"],
                        "stage_id": obj_temp["stage_id"],
                        "category_id": obj_temp["category_id"],
                        "status_id": obj_temp["status_id"],
                        "customer_id": obj_temp["customer_id"],
                        "customer_name": obj_temp["customer_id"]['display_name'],
                        "desc": obj_temp["desc"],
                        "create_user_name": obj_temp["create_user_name"],
                        'stage_change_list': obj_stage_change_list,
                        'record_status': obj_temp["record_status"],
                        'create_user_nick_name': obj_temp["create_user_nick_name"],
                        "customer_price": obj_temp["customer_price"],
                        "customer_price_currency": obj_temp["customer_price_currency"],
                        "cpu": obj_temp["cpu"],
                        "os": obj_temp["os"],
                        "marketing": obj_temp["marketing"],
                        "sdkversion": obj_temp["sdkversion"],
                        "dl_reason": obj_temp["dl_reason"],
                        "volume": obj_temp["volume"],
                        "date_from": obj_temp["date_from"],
                        "date_to": obj_temp["date_to"],
                        "project_document_ids": obj_temp["project_document_ids"],
                        "project_attend_user_ids": obj_temp["project_attend_user_ids"],
                        "cus_city": obj_temp["cus_city"],
                        "socket": obj_temp["socket"],
                        "module": obj_temp["module"],
                        "model_type_id": obj_temp["model_type_id"],
                        "cus_product_type_id": obj_temp["cus_product_type_id"],
                        "reviewers": reviewers,
                        "total_life_cycle": obj_temp["total_life_cycle"],
                        "total_life_price": obj_temp["total_life_price"]
                    }
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': ret_temp}
        return json_response(rp)

    @http.route([
        '/api/v11/getAccountDetailById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_detail_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                result = request.env[model].sudo().search_read(domain)
                if result:
                    obj_temp = result[0]
                    model_fields = request.env[model].fields_get()
                    for f in obj_temp.keys():
                        if model_fields[f]['type'] == 'many2one':
                            if obj_temp[f]:
                                obj_temp[f] = {'id': obj_temp[f][0], 'display_name': obj_temp[f][1]}
                            else:
                                obj_temp[f] = ''
                    from ..public import account_public
                    # 判断signer
                    signer = str(obj_temp["signer"]['id']) if obj_temp["signer"] else obj_temp["signer"]
                    station_no = obj_temp["station_no"]
                    si_station = station_no
                    if station_no and station_no == 28:
                        _station = env['xlcrm.account.partial'].sudo().search_read(
                            [('review_id', '=', int(kw.get("id")))], order='init_time desc',
                            limit=1)
                        _station = _station if _station and _station[0]['sign_over'] == 'N' else ''
                        to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                        sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                            'sign_station'] else []
                        ne_station = list(set(to_station) - set(sign_station))
                        signer = ''
                        for sta in ne_station:
                            sig = env['xlcrm.account.signers'].sudo().search_read(
                                [('review_id', '=', int(kw.get("id"))), ('station_no', '=', int(sta))])
                            if sig:
                                if signer:
                                    signer = signer + ',' + sig[0]['signers']
                                else:
                                    signer = sig[0]['signers']

                                if str(env.uid) in sig[0]['signers'].split(','):
                                    si_station = int(sta)

                    # 判断是否有回签
                    from_station_ = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', int(kw.get("id")))], order='init_time desc', limit=1)
                    from_station = from_station_[0]['from_station'] if from_station_ and from_station_[0][
                        'sign_over'] == 'N' else ''
                    ret_temp = {
                        "id": obj_temp["id"],
                        "review_type": obj_temp["review_type"],
                        "apply_user": obj_temp["apply_user"],
                        "department": obj_temp["department"],
                        "apply_date": obj_temp["apply_date"],
                        "a_company": obj_temp["a_company"],
                        "kc_company": obj_temp["kc_company"],
                        "ke_company": obj_temp["ke_company"],
                        "kw_address": obj_temp["kw_address"],
                        "registered_address": obj_temp["registered_address"],
                        "kf_address": obj_temp["kf_address"],
                        "krc_company": obj_temp["krc_company"],
                        'kre_company': obj_temp["kre_company"],
                        'kpc_company': obj_temp["kpc_company"],
                        'kpe_company': obj_temp["kpe_company"],
                        "de_address": obj_temp["de_address"],
                        "currency": obj_temp["currency"],
                        "c_account": obj_temp["c_account"],
                        "a_account": obj_temp["a_account"],
                        "reconciliation_date": obj_temp["reconciliation_date"],
                        "payment_date": obj_temp["payment_date"],
                        # "reviewers": obj_temp["reviewers"],
                        "station_no": obj_temp["station_no"],
                        "status_id": obj_temp["status_id"],
                        "nowStage": account_public.Stations('帐期额度申请单').getStionsDesc(obj_temp["station_no"]),
                        "account_attend_user_ids": obj_temp["account_attend_user_ids"],
                        "signer": signer,
                        "loguser": env.uid,
                        "dap": obj_temp["dap"],
                        'from_station': from_station if from_station else obj_temp["station_no"],
                        'si_station': si_station,
                        'reviewers': obj_temp['reviewers']
                    }
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': ret_temp}
        return json_response(rp)

    # @http.route([
    #     '/api/v12/getAccountDetailById/<string:model>'
    # ], auth='none', type='http', csrf=False, methods=['GET'])
    # def get_account_detail_by_id12(self, model=None, ids=None, **kw):
    #     success, message, result, ret_temp, count, offset, limit = True, '', '', {}, 0, 0, 25
    #     token = kw.pop('token')
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     domain = []
    #     if kw.get("id"):
    #         domain.append(('id', '=', kw.get("id")))
    #         domain = searchargs(domain)
    #         try:
    #             result = request.env[model].sudo().search_read(domain)
    #             if result:
    #                 obj_temp = result[0]
    #                 model_fields = request.env[model].fields_get()
    #                 for f in obj_temp.keys():
    #                     if model_fields[f]['type'] == 'many2one':
    #                         if obj_temp[f]:
    #                             obj_temp[f] = {'id': obj_temp[f][0], 'display_name': obj_temp[f][1]}
    #                         else:
    #                             obj_temp[f] = ''
    #                 from . import account_public
    #                 ap = account_public.Stations('帐期额度申请单')
    #                 if obj_temp['cs']:
    #                     obj_temp['cs'] = eval(obj_temp['cs'])
    #                 else:
    #                     res_ = {"payment": "", "on_time": ""}
    #                     res_customer = env['xlcrm.account.customer'].sudo().search_read(
    #                         [('review_id', '=', obj_temp['id'])])
    #                     if res_customer:
    #                         customer_ = res_customer[0]
    #                         res_['registered_capital'] = customer_['registered_capital']
    #                         res_['registered_capital_currency'] = customer_['registered_capital_currency']
    #                         res_['paid_capital'] = customer_['paid_capital']
    #                         res_['paid_capital_currency'] = customer_['paid_capital_currency']
    #                         res_['insured_persons'] = customer_['insured_persons']
    #                         res_['on_time'] = customer_['on_time']
    #                         res_['overdue30'] = customer_['overdue30']
    #                         res_['overdue60'] = customer_['overdue60']
    #                         res_['overdue_others'] = customer_['overdue_others']
    #                         res_['payment'] = customer_['payment']
    #                         res_['payment_currency'] = customer_['payment_currency']
    #                         res_['payment_account'] = customer_['payment_account']
    #                         res_['salesment_currency'] = customer_['salesment_currency']
    #                         res_['salesment_account'] = customer_['salesment_account']
    #                         res_['stock'] = customer_['stock']
    #                         res_['guarantee'] = customer_['guarantee']
    #                     obj_temp['cs'] = res_
    #                 if not obj_temp['cs'].get('historys'):
    #                     obj_temp['cs']['historys'] = [{'payment_account': obj_temp['cs'].get('payment_account'),
    #                                                    'payment_currency': obj_temp['cs'].get('payment_currency'),
    #                                                    'salesment_account': obj_temp['cs'].get('salesment_account'),
    #                                                    'salesment_currency': obj_temp['cs'].get('salesment_currency'),
    #                                                    }]
    #                 # 判断signer
    #                 signer = str(obj_temp["signer"]['id']) if obj_temp["signer"] else obj_temp["signer"]
    #                 station_no = obj_temp["station_no"]
    #                 si_station = station_no
    #                 if station_no and station_no == 28:
    #                     _station = env['xlcrm.account.partial'].sudo().search_read(
    #                         [('review_id', '=', int(kw.get("id")))], order='init_time desc',
    #                         limit=1)
    #                     _station = _station if _station and _station[0]['sign_over'] == 'N' else ''
    #                     to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
    #                     sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
    #                         'sign_station'] else []
    #                     ne_station = list(set(to_station) - set(sign_station))
    #                     signer = ''
    #                     for sta in ne_station:
    #                         sig = env['xlcrm.account.signers'].sudo().search_read(
    #                             [('review_id', '=', int(kw.get("id"))), ('station_no', '=', int(sta))])
    #                         if sig:
    #                             if int(sta) in (20, 21, 25, 30):
    #                                 sec = env['xlcrm.account.partial.sec'].sudo().search_read(
    #                                     [('review_id', '=', obj_temp['id']), ('station_no', '=', sta),
    #                                      ('p_id', '=', _station[0]['id'])])
    #                                 if sec:
    #                                     to_brands = sec[0]['to_brand'].split(',')
    #                                     sign_brands = sec[0]['sign_brand'].split(',') if sec[0]['sign_brand'] else []
    #                                     brands = filter(lambda x: x, list(set(to_brands) - set(sign_brands)))
    #                                     products = ast.literal_eval(obj_temp['products']) if obj_temp[
    #                                         'products'] else {}
    #                                     sta_code = ap.getStionsCode(int(sta))
    #                                     for br in brands:
    #                                         sign_br = filter(lambda x: x['brandname'] == br, products)[0] if br else {}
    #                                         sign_username = sign_br.get(sta_code)
    #                                         if sign_username:
    #                                             sign_username = sign_username.split('(')[1].split(')')[0]
    #                                             signer_user = env['xlcrm.users'].sudo().search_read(
    #                                                 [('username', 'like', sign_username)])[0]
    #                                             if signer:
    #                                                 signer = signer + ',' + str(signer_user['id'])
    #                                             else:
    #                                                 signer = str(signer_user['id'])
    #                             elif int(sta) == 45:
    #                                 si = sig[0]['signers']
    #                                 si_temp = ''
    #                                 if '[' in si:
    #                                     si_temp = ','.join(
    #                                         map(lambda x: str(x), eval(si.replace('[', '').replace(']', ''))))
    #                                 signer = signer + ',' + si_temp if signer else si_temp
    #                                 si_station = int(sta)
    #                             else:
    #                                 if signer:
    #                                     signer = signer + ',' + sig[0]['signers']
    #                                 else:
    #                                     signer = sig[0]['signers']
    #
    #                             if str(env.uid) in signer.split(',') and str(env.uid) in sig[0]['signers'].split(','):
    #                                 si_station = int(sta)
    #                 if station_no and station_no in (20, 21, 25, 30, 35, 40):
    #                     signer = env['xlcrm.account.signers'].sudo().search_read(
    #                         [('review_id', '=', int(kw.get("id"))), ('station_no', '=', station_no)])
    #                     if signer:
    #                         signed = map(lambda x: x, signer[0]['signed'].split(',')) if signer[0][
    #                             'signed'] else []
    #                         signer_y = map(lambda x: x, signer[0]['signers'].split(',')) if signer[0][
    #                             'signers'] else []
    #                         signer_n = list(set(signer_y) - set(signed))
    #                         signer = ','.join(signer_n) if signer_n else ''
    #                 if station_no and station_no == 45:
    #                     signer_ = env['xlcrm.account.signers'].sudo().search_read(
    #                         [('review_id', '=', int(kw.get("id"))), ('station_no', '=', station_no)])
    #                     if signer_:
    #                         si = signer_[0]['signers']
    #                         if '[' in si:
    #                             si = eval(si)
    #                             for s in si:
    #                                 if isinstance(si, list):
    #                                     signer = map(lambda x: str(x), si)
    #                                     break
    #                                 if int(signer) == s or int(signer) in s:
    #                                     signer = map(lambda x: str(x), s) if isinstance(s, list) else [str(s)]
    #                                     break
    #                             signer = ','.join(signer)
    #                 products = ast.literal_eval(obj_temp['products']) if obj_temp['products'] else []
    #                 products_sign = products[:]
    #                 if products:
    #                     log_username = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])
    #                     log_username = log_username[0]['nickname'] + '(' + log_username[0]['username'].split('@')[
    #                         0] + ')' if '@' in log_username[0]['username'] else log_username[0]['nickname'] + '(' + \
    #                                                                             log_username[0]['username'] + ')'
    #                     pm_signer = map(lambda x: x.get('PM'), products)
    #                     pur_signer = map(lambda x: x.get('PUR'), products)
    #                     pmm_signer = map(lambda x: x.get('PMM'), products)
    #                     pmins_signer = map(lambda x: x.get('PMins'), products)
    #                     if log_username in pm_signer + pur_signer + pmm_signer + pmins_signer:
    #                         le = len(products) - 1
    #                         for i in range(len(products)):
    #                             if products[le - i].get('PM') != log_username and products[le - i].get(
    #                                     'PUR') != log_username and products[le - i].get('PMM') != log_username and \
    #                                     products[le - i].get('PMins') != log_username and obj_temp['init_user'][
    #                                 'id'] != env.uid:
    #                                 products.pop(le - i)
    #                             if si_station == 20 and products_sign[le - i].get('PM') != log_username:
    #                                 products_sign.pop(le - i)
    #                             if si_station == 21 and products_sign[le - i].get('PMins') != log_username:
    #                                 products_sign.pop(le - i)
    #                             if si_station == 25 and products_sign[le - i].get('PUR') != log_username:
    #                                 products_sign.pop(le - i)
    #                             if si_station == 30 and products_sign[le - i].get('PMM') != log_username:
    #                                 products_sign.pop(le - i)
    #
    #                 # 判断是否有回签
    #                 from_station_ = env['xlcrm.account.partial'].sudo().search_read(
    #                     [('review_id', '=', int(kw.get("id")))], order='init_time desc', limit=1)
    #                 from_station = from_station_[0]['from_station'] if from_station_ and from_station_[0][
    #                     'sign_over'] == 'N' else ''
    #                 current_account_period = []
    #                 if obj_temp['current_account_period']:
    #                     current_account_period = ast.literal_eval(obj_temp['current_account_period'])
    #                 if not current_account_period:
    #                     temp = {}
    #                     temp['kc_company'] = obj_temp['a_company']
    #                     temp['release_time'] = obj_temp['release_time'] if obj_temp['release_time'] else ''
    #                     temp['payment_method'] = obj_temp['payment_method'] if obj_temp['payment_method'] else ''
    #                     telegraphic_days = obj_temp['telegraphic_days'] if obj_temp['telegraphic_days'] else ''
    #                     acceptance_days = obj_temp['acceptance_days'] if obj_temp[
    #                         'acceptance_days'] else ''
    #                     days = '' if temp['payment_method'] == '100%电汇' or not temp['payment_method'] else '天'
    #                     temp['payment_method'] += telegraphic_days + acceptance_days + days
    #                     temp['credit_limit_now'] = obj_temp['credit_limit_now'] if obj_temp[
    #                         'credit_limit_now'] else ''
    #                     current_account_period.append(temp)
    #                 company_res = env['xlcrm.user.ccfnotice'].sudo().search_read(
    #                     [('a_company', '=', obj_temp['a_company'])])
    #                 companycode = company_res[0]['a_companycode'] if company_res else ''
    #                 ret_temp = {
    #                     "id": obj_temp["id"],
    #                     "review_type": obj_temp["review_type"],
    #                     "apply_user": obj_temp["apply_user"],
    #                     "department": obj_temp["department"],
    #                     "apply_date": obj_temp["apply_date"],
    #                     "a_company": obj_temp["a_company"],
    #                     "a_companycode": companycode,
    #                     "kc_company": obj_temp["kc_company"],
    #                     "ccuscode": obj_temp["ccuscode"] if obj_temp["ccuscode"] else '',
    #                     "ke_company": obj_temp["ke_company"],
    #                     "kw_address": obj_temp["kw_address"],
    #                     "kf_address": obj_temp["kf_address"],
    #                     "krc_company": obj_temp["krc_company"],
    #                     'kre_company': obj_temp["kre_company"],
    #                     'kpc_company': obj_temp["kpc_company"],
    #                     'kpe_company': obj_temp["kpe_company"],
    #                     "de_address": obj_temp["de_address"],
    #                     "currency": obj_temp["currency"],
    #                     # "c_account": obj_temp["c_account"],
    #                     # "a_account": obj_temp["a_account"],
    #                     "reconciliation_date": obj_temp["reconciliation_date"],
    #                     "payment_date": obj_temp["payment_date"],
    #                     # "reviewers": obj_temp["reviewers"],
    #                     "station_no": obj_temp["station_no"],
    #                     "status_id": obj_temp["status_id"],
    #                     "nowStage": account_public.Stations('帐期额度申请单').getStionsDesc(obj_temp["station_no"]),
    #                     "account_attend_user_ids": obj_temp["account_attend_user_ids"],
    #                     "signer": signer,
    #                     "loguser": env.uid,
    #                     # "dap": obj_temp["dap"],
    #                     'from_station': from_station if from_station else obj_temp["station_no"],
    #                     'si_station': si_station,
    #                     'reviewers': ast.literal_eval(obj_temp['reviewers']) if obj_temp['reviewers'] else {},
    #                     'products': products,
    #                     'remark': obj_temp['remark'] if obj_temp['remark'] else '',
    #                     'products_sign': products_sign,
    #                     'kehu': obj_temp['kehu'] if obj_temp['kehu'] else '',
    #                     'unit': obj_temp['unit'] if obj_temp['unit'] else '',
    #                     'release_time': obj_temp['release_time'] if obj_temp['release_time'] else '',
    #                     'payment_method': obj_temp['payment_method'] if obj_temp['payment_method'] else '',
    #                     'telegraphic_days': obj_temp['telegraphic_days'] if obj_temp['telegraphic_days'] else '',
    #                     'release_time_apply': obj_temp['release_time_apply'] if obj_temp['release_time_apply'] else '',
    #                     'release_time_applyM': obj_temp['release_time_applyM'] if obj_temp[
    #                         'release_time_applyM'] else '',
    #                     'release_time_applyO': obj_temp['release_time_applyO'] if obj_temp[
    #                         'release_time_applyO'] else '',
    #                     'payment_method_apply': obj_temp['payment_method_apply'] if obj_temp[
    #                         'payment_method_apply'] else '',
    #                     'acceptance_days_apply': obj_temp['acceptance_days_apply'] if obj_temp[
    #                         'acceptance_days_apply'] else '',
    #                     'acceptance_days': obj_temp['acceptance_days'] if obj_temp[
    #                         'acceptance_days'] else '',
    #                     'telegraphic_days_apply': obj_temp['telegraphic_days_apply'] if obj_temp[
    #                         'telegraphic_days_apply'] else '',
    #                     'others_apply': obj_temp['others_apply'] if obj_temp[
    #                         'others_apply'] else '',
    #                     'credit_limit': obj_temp['credit_limit'] if obj_temp[
    #                         'credit_limit'] else '',
    #                     'credit_limit_now': obj_temp['credit_limit_now'] if obj_temp[
    #                         'credit_limit_now'] else '',
    #                     'current_account_period': current_account_period,
    #                     'protocol_code': obj_temp['protocol_code'] if obj_temp[
    #                         'protocol_code'] else '',
    #                     'protocol_detail': obj_temp['protocol_detail'] if obj_temp[
    #                         'protocol_detail'] else '',
    #                     'cs': obj_temp['cs'],
    #                     'affiliates': eval(obj_temp['affiliates']) if obj_temp['affiliates'] else [],
    #                     'payment': eval(obj_temp['payment']) if obj_temp['payment'] else [],
    #                     'overdue': eval(obj_temp['overdue']) if obj_temp['overdue'] else [],
    #                     're_payments': eval(obj_temp['re_payments']) if obj_temp['re_payments'] else [],
    #                     're_overdues': eval(obj_temp['re_overdues']) if obj_temp['re_overdues'] else [],
    #                     'overdue_arrears': obj_temp['overdue_arrears'],
    #                     're_overdue_arrears': obj_temp['re_overdue_arrears'],
    #                     'overdue_payment': obj_temp['overdue_payment'],
    #                     're_overdue_payment': obj_temp['re_overdue_payment'],
    #                 }
    #             message = "success"
    #         except Exception as e:
    #             result, success, message = '', False, str(e)
    #         finally:
    #             env.cr.close()
    #
    #     rp = {'status': 200, 'message': message, 'data': ret_temp}
    #     return json_response(rp)

    @http.route([
        '/api/v11/getProjectReviewById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_review_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                result_temp = request.env["xlcrm.project.review"].sudo().search_read(domain)
                if result_temp:
                    result_temp = result_temp[0]
                    model_fields_review = request.env["xlcrm.project.review"].fields_get()
                    for f in result_temp.keys():
                        if model_fields_review[f]['type'] == 'many2one':
                            if result_temp[f]:
                                result_temp[f] = {'id': result_temp[f][0], 'display_name': result_temp[f][1]}
                            else:
                                result_temp[f] = ''
                    result = {
                        "id": result_temp["id"],
                        "project_id": result_temp["project_id"],
                        "review_title": result_temp["review_title"],
                        "review_target": result_temp["review_target"],
                        "review_duration": result_temp["review_duration"],
                        "review_status_id": result_temp["review_status_id"],
                        "status_id": result_temp["status_id"],
                        "from_stage_id": result_temp["from_stage_id"],
                        "to_stage_id": result_temp["to_stage_id"],
                        "date_begin": result_temp["date_begin"],
                        "date_end": result_temp["date_end"],
                        "review_user_ids": result_temp["review_user_ids"],
                        "desc": result_temp["desc"],
                        "record_status": result_temp["record_status"],
                        "create_user_name": result_temp["create_user_name"],
                        "create_user_nick_name": result_temp["create_user_nick_name"],
                        "review_document_ids": result_temp["review_document_ids"],
                        "pass_count_lv": result_temp["pass_count_lv"]
                    }
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getAccountReviewById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_review_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        filters = ['content', 'update_user', 'update_time']
        result = {}
        id = int(kw.get("id"))
        if id:
            domain.append(('id', '=', id))
            domain = searchargs(domain)
            try:
                main_form = request.env["xlcrm.account"].sudo().search_read(domain)
                station_no = main_form[0]['station_no']
                from_station_ = env['xlcrm.account.partial'].sudo().search_read(
                    [('review_id', '=', int(kw.get("id")))], order='init_time desc', limit=1)
                station_no = from_station_[0]['from_station'] if from_station_ and from_station_[0][
                    'sign_over'] == 'N' else station_no
                signer_id = main_form[0]['signer'][0] if main_form[0]['signer'] else ''
                from ..public import account_public
                account = account_public.Stations('帐期额度申请单')
                dict_model = account.getModelByStaion(station_no)
                base_model = 'xlcrm.account'
                for value in dict_model.values():
                    filters = ['content', 'update_user', 'update_time']
                    if value == "lg":  # 法务部查找栏位多些
                        filters += ['rd_license_q', 'rd_receipt', 'rd_receipt_q', 'rd_receipt_address',
                                    'rd_receipt_address_q', 'rd_agree']
                    if value == 'base':
                        filters.remove('content')
                    tar_model = base_model + '.' + value
                    tar_domain = [('review_id', '=', id)]
                    result[value] = env[tar_model].sudo().search_read(tar_domain, filters)
                    # result_copy=result.deepcopy()
                    if result[value]:
                        signer = [
                            f"{env['xlcrm.users'].sudo().search_read([('id', '=', item['update_user'][0])], ['nickname'])[0]['nickname']} {item['update_time']}"
                            for item in result[value]]
                        # signer='-'.join(signer)
                        # 判断是否回签，回签后是否已签
                        signer_id = [item['update_user'][0] for item in result[value]]
                        re_back_ = env['xlcrm.account.partial'].sudo().search_read(
                            [('review_id', '=', id)], order='init_time desc', limit=1)
                        re_back = re_back_ if re_back_ and re_back_[0]['sign_over'] == 'N' else ''
                        if re_back:
                            sign_station = re_back[0]['sign_station'] if re_back[0]['sign_station'] else ''
                            if str(account.getStaionsReject(value)) + ',' in sign_station:
                                signer_id = []
                        result[value] = result[value][-1]
                        result[value]['init_nickname'] = \
                            env['xlcrm.users'].sudo().search_read([('id', '=', result[value]['update_user'][0])],
                                                                  ['nickname'])[0][
                                'nickname']
                        result[value]['signer'] = signer
                        result[value]['signer_id'] = signer_id
                    else:
                        result[value] = {'id': '', 'signer_id': signer_id}
                message = "success"
                success = True

            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getCommitItemById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_review_commit_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("id"):
            domain.append(('id', '=', kw.get("id")))
            domain = searchargs(domain)
            try:
                result_temp = request.env["xlcrm.review.commit"].sudo().search_read(domain)
                if result_temp:
                    result_temp = result_temp[0]
                    model_fields_review = request.env["xlcrm.review.commit"].fields_get()
                    for f in result_temp.keys():
                        if model_fields_review[f]['type'] == 'many2one':
                            if result_temp[f]:
                                result_temp[f] = {'id': result_temp[f][0], 'display_name': result_temp[f][1]}
                            else:
                                result_temp[f] = ''
                    result = {
                        "id": result_temp["id"],
                        "star_level": result_temp["star_level"],
                        "date_commit": result_temp["date_commit"],
                        "user_id": result_temp["user_id"],
                        "status_id": result_temp["status_id"],
                        "review_comment": result_temp["review_comment"],
                        "review_result_id": result_temp["review_result_id"],

                        "review_id": result_temp["review_id"],
                        "review_title": result_temp["review_title"],
                        "review_date": result_temp["review_date"],
                        "review_create_user_name": result_temp["review_create_user_name"],
                        "review_create_user_nick_name": result_temp["review_create_user_nick_name"],

                        "project_id": result_temp["project_id"],
                        "project_status_id": result_temp["project_status_id"],
                        "customer_id": result_temp["customer_id"],
                        "from_stage_id": result_temp["from_stage_id"],
                        "to_stage_id": result_temp["to_stage_id"],
                    }
                message = ""
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/customerupdate/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def customer_update(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            obj_id = data["id"]
            data["write_user_id"] = env.uid
            result = env[model].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result:
                ret_object = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env[model].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''

                # result_temp = [{"id": ret_object.get("id"),
                #                 "name": ret_object.get("name"),
                #                 "email": ret_object.get("email"),
                #                 "address": ret_object.get("address"),
                #                 "phone": ret_object.get("phone"),
                #                 "email": ret_object.get("email"),
                #                 "capital": ret_object.get("capital"),
                #                 "level_id": ret_object.get("level_id")["id"],
                #                 "industry_id": ret_object.get("industry_id")["id"],
                #                 "category_id": ret_object.get("category_id")["id"],
                #                 "status_id": ret_object.get("status_id")["id"]}]
                message = '更新成功！'
                success = True
        except Exception as e:
            ret_object, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': ret_object}
        return json_response(rp)

    @http.route([
        '/api/v11/setCustomerFocus'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def customer_update_focus(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            obj_id = data["customer_id"]
            is_focused = False
            if data["is_focused"] == 'false':
                is_focused = True
            data["write_user_id"] = env.uid

            data["is_focused"] = is_focused
            result = env["xlcrm.customer"].sudo().browse(215).write(
                {'is_focused': is_focused, 'write_user_id': env.uid})
            env.cr.commit()
            if result:
                ret_object = env["xlcrm.customer"].sudo().search_read([('id', '=', obj_id)])[0]
                ret_object = {
                    'is_focused': ret_object['is_focused']
                }
                message = '更新成功！'
                success = True
        except Exception as e:
            ret_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': ret_object}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            obj_id = data["id"]
            data["write_user_id"] = env.uid
            result = env[model].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result:
                ret_object = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env[model].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''
                message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

    @http.route([
        '/api/v11/objUpdate/reviewCommit/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_review_commit(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            data['status_id'] = 1
            data["write_user_id"] = env.uid
            dtCommit = datetime.datetime.now()
            sysstr = platform.system()
            if sysstr != "Windows":
                dtCommit = datetime.datetime.now() + datetime.timedelta(hours=8)
            data["date_commit"] = dtCommit
            obj_id = data["id"]
            result_temp = env[model].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result_temp:
                result = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env[model].fields_get()
                for f in result.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if result[f]:
                            result[f] = {'id': result[f][0], 'display_name': result[f][1]}
                        else:
                            result[f] = ''

            count_review_commit_to_do = request.env["xlcrm.review.commit"].sudo().search_count(
                [('status_id', '=', 0), ('review_id', '=', data["review_id"])])
            review_status_id_update = ''
            if (count_review_commit_to_do == 0):
                review_status_id_update = {
                    'status_id': 3
                }
            else:
                review_status_id_update = {
                    'status_id': 2
                }
            env["xlcrm.project.review"].sudo().browse(data["review_id"]).write(review_status_id_update)

            if (count_review_commit_to_do == 0):
                count_review_commit_to_do_by_project = request.env["xlcrm.review.commit"].sudo().search_count(
                    [('status_id', '=', 0), ('project_id', '=', result["project_id"]["id"])])
                if (count_review_commit_to_do_by_project == 0):
                    pass_review_lv = request.env["xlcrm.project.review"].sudo().search_count(
                        [('pass_count_lv', '<', 100), ('project_id', '=', result["project_id"]["id"])])
                    if pass_review_lv == 0:
                        project_update = ''
                        obj_project = \
                            env["xlcrm.project"].sudo().search_read([('id', '=', result["project_id"]["id"])])[0]
                        obj_review = env["xlcrm.project.review"].sudo().search_read([('id', '=', data["review_id"])])[0]
                        if (obj_project["stage_id"][0] == obj_review["from_stage_id"][0]):
                            obj_project_stage_id = obj_project["stage_id"][0]
                            obj_project_status_id = obj_project["status_id"][0]
                            isChange = False
                            if (obj_project_stage_id < 4):
                                obj_project_stage_id = obj_project_stage_id + 1
                                isChange = True
                            if (obj_project_status_id < 4):
                                obj_project_status_id = obj_project_status_id + 1
                            project_update = {
                                'stage_id': obj_project_stage_id,
                                'status_id': obj_project_status_id
                            }
                            if isChange:
                                env["xlcrm.project"].sudo().browse(result["project_id"]["id"]).write(project_update)

                                # 计算项目阶段所用时间及记录相关变更操作
                                project_id = result["project_id"]["id"]
                                to_stage_id = obj_project_stage_id
                                duration_effort = 0
                                obj_stage_change_last = \
                                    env["sdo.project.stage.change"].sudo().search_read(
                                        [('project_id', '=', project_id)],
                                        order='id desc')[0]
                                diff = 0
                                if sysstr != "Windows":
                                    dtUpateNow = datetime.datetime.now() + datetime.timedelta(hours=8)
                                    diff = dtUpateNow - obj_stage_change_last['operation_date_time']
                                else:
                                    diff = datetime.datetime.now() - obj_stage_change_last['operation_date_time']

                                duration_effort = round(diff.total_seconds() / 60.0, 2)
                                env["sdo.project.stage.change"].sudo().browse(obj_stage_change_last['id']).write(
                                    {"duration_effort": duration_effort})
                                dataStageChange = {
                                    'operation_user_id': env.uid,
                                    'stage_id': to_stage_id,
                                    'project_id': project_id,
                                    'from_stage_id': to_stage_id - 1,
                                    'to_stage_id': to_stage_id,
                                    'desc': '由系统自动变更项目阶段'
                                }
                                dataStageChange["operation_user_id"] = env.uid
                                dataStageChange["stage_id"] = to_stage_id
                                obj_stage_change_id = env["sdo.project.stage.change"].sudo().create(dataStageChange).id
                                obj_stage_change = \
                                    env["sdo.project.stage.change"].sudo().search_read(
                                        [('id', '=', obj_stage_change_id)])[
                                        0]
                                operation_log = {
                                    'name': '项目状态变更：' + obj_stage_change["project_name"],
                                    'operator_user_id': env.uid,
                                    'content': '项目状态由系统自动变更，从：' + obj_stage_change['from_stage_name'] + ' 到：' +
                                               obj_stage_change['to_stage_name'],
                                    'res_id': obj_stage_change['id'],
                                    'res_model': 'sdo.project.stage.change',
                                    'res_id_related': obj_stage_change['project_id'][0],
                                    'res_model_related': 'xlcrm.project',
                                    'operation_level': 0,
                                    'operation_type': 0
                                }
                                env["xlcrm.operation.log"].sudo().create(operation_log)
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/projectReview/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_review(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            user_ids = data['review_user_ids']
            data['review_user_ids'] = [[6, 0, user_ids]]
            data['from_stage_id'] = data['from_stage_id']["id"]
            data['to_stage_id'] = data['to_stage_id']["id"]
            data['project_id'] = data['project_id']["id"]
            data["write_user_id"] = env.uid
            obj_id = data["id"]
            result = env[model].sudo().browse(obj_id).write(data)
            if result:
                if (data['record_status'] == 1):
                    review_commit_user_ids = env["xlcrm.review.commit"].sudo().search_read([('review_id', '=', obj_id)],
                                                                                           ['user_id'])
                    exist_selected_user_ids = [review_commit_user_ids['user_id'][0] for review_commit_user_ids in
                                               review_commit_user_ids]
                    for new_selected_user_id in user_ids:
                        if new_selected_user_id not in exist_selected_user_ids:
                            review_commit_item = {
                                'review_id': obj_id,
                                'user_id': new_selected_user_id,
                                'create_user_id': env.uid
                            }
                            env["xlcrm.review.commit"].sudo().create(review_commit_item)

                env["xlcrm.review.commit"].sudo().search(
                    [('review_id', '=', obj_id), ('user_id', 'not in', user_ids)]).unlink()
                ret_object = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env[model].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''
                env.cr.commit()
                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': ret_object}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/accountReview/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_account(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
            # id = data.get("id")
            review_id = data.get('review_id')
            station_no = data.get("station_no")
            from ..public import account_public
            account = account_public.Stations('帐期额度申请单')
            record_status = data.get('record_status')
            if station_no == 1:
                review_id = data.get('id')
                data.pop('station_no')
                data['init_nickname'] = ''
                signers = data.get('reviewers', {})
                env[model].sudo().browse(review_id).write(data)
            reject_reason = data.get("backreason")
            station_model = account.getModel(station_no)
            result = env[station_model].sudo().search_read([('review_id', '=', review_id), ('init_user', '=', env.uid)])
            if result:
                data.pop('backreason')
                data.pop('init_nickname')
                data.pop('record_status')
                data["update_user"] = env.uid
                data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                env[station_model].sudo().browse(result[0]['id']).write(data)
            else:
                data['review_id'] = review_id
                data["init_user"] = env.uid
                data["init_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                data["update_user"] = env.uid
                data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                result = env[station_model].sudo().create(data)
            success_email = True
            # send_wechart =True
            if record_status > 0:
                date_main = {}
                from ..public import send_email
                email_obj = send_email.Send_email()
                if record_status == 1:
                    next_signer = ''
                    next_station = 0
                    while not next_signer:
                        # 首先判断下一站是否有签核人
                        next_station = account.getnextstation(station_no)
                        next_signer = request.env['xlcrm.account.signers'].sudo().search_read(
                            ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], ['signers'])
                        if next_signer:
                            next_signer = next_signer[0]['signers']
                        else:
                            next_signer = ''

                        # 判断当前站别是否是多人签核
                        signer = request.env['xlcrm.account.signers'].sudo().search_read(
                            ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)], ['signers'])
                        if signer:
                            signers = signer[0]['signers'].split(',')
                            signers_index = 0
                            if len(signers) > 1:
                                for index, value in enumerate(signers):
                                    if value == str(env.uid):
                                        signers_index = index
                                        break
                                if signers_index < len(signers) - 1:  # 多人签且当前签核人不是多人签中的最后一个时，下一站站别信息不变
                                    next_station = station_no
                                    next_signer = signers[signers_index + 1]

                        # 判断是否回签
                        sign_back = env['xlcrm.account.partial'].sudo().search_read(
                            [('review_id', '=', review_id)], order='init_time desc', limit=1)
                        if sign_back and sign_back[0]['sign_over'] == 'N':
                            if next_station == station_no:  # 说明是多人签核且还有人没有签完
                                next_station = 28
                                next_signer = ''
                                break
                            else:
                                sign_station = sign_back[0]['sign_station'] + str(station_no) + ',' if sign_back[0][
                                    'sign_station'] else '' + str(station_no) + ','
                                env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
                                    {'sign_station': sign_station})

                                ne_station = list(
                                    set(sign_back[0]['to_station'].split(',')) - set(sign_station.split(',')))
                                if not ne_station or ne_station == [str(station_no)]:
                                    next_station = sign_back[0]['from_station']
                                    next_signer = request.env['xlcrm.account.signers'].sudo().search_read(
                                        ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)],
                                        ['signers'])
                                    if next_signer:
                                        next_signer = next_signer[0]['signers']
                                    else:
                                        next_signer = ''
                                else:
                                    next_station = 28
                                    break

                        station_no = next_station
                        if station_no == 99:
                            date_main['status_id'] = 3
                            break
                    date_main['station_no'] = next_station
                    date_main['signer'] = next_signer.split(',')[0]
                    date_main['station_desc'] = account.getStionsDesc(next_station)
                if record_status == 2:  # 驳回
                    # 写入驳回记录表
                    if reject_reason:
                        env['xlcrm.account.reject'].sudo().create({'review_id': review_id,
                                                                   'station_no': station_no,
                                                                   'reason': reject_reason,
                                                                   'init_user': env.uid})
                    create_uid = env["xlcrm.account"].sudo().search_read([("id", "=", review_id)])
                    if create_uid:
                        create_uid = create_uid[0]
                    date_main['signer'] = create_uid["init_user"][0]
                    station_no = 1
                    station_desc = account.getStionsDesc(station_no)
                    date_main['station_no'] = station_no
                    date_main['station_desc'] = station_desc
                    date_main['status_id'] = 1
                    date_main['record_status'] = 0
                    date_main['isback'] = 1

                if date_main['signer']:
                    uid = date_main['signer']
                    # fromaddr = "crm@szsunray.com"
                    # qqCode = "Sunray201911"
                    sbuject = "帐期额度申请单待审核通知"
                    # to = [uid["email"]]
                    # uid_list=str(uid).split(',')
                    # if len(uid_list)>0:
                    #     uid_index=0
                    #     for key,value in enumerate(uid_list):
                    #         if value==str(env.uid):
                    #             uid_index=key+1
                    #
                    #
                    #
                    to = [odoo.tools.config["test_username"]]
                    to_wechart = odoo.tools.config["test_wechat"]
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        user = request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
                        to = [user["email"]]
                        to_wechart = user['nickname'] + '，' + user["email"]
                    token = get_token(uid)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/account-list_new/' + str(
                        review_id) + "/" + json.dumps(token)
                    content = """
                        <html lang="en">            
                        <body>
                            <div>
                                您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
                                <a href='""" + href + """' ><font color="red">PC端链接</font></a>或<a href='""" + url + """' ><font color="red">移动端链接</font></a>进入系统审核
                            </div>
                            <div>
                            <br>
                            注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>,用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                            </div>
                        </body>
                        </html>
                        """
                    msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                    if msg["code"] == 500:  # 邮件发送失败
                        success_email = False
                    # 发微信通知
                    # from . import account_public
                    # account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
                    # url = 'http://crm.szsunray.com/public/account-list_new/%s/%s'%(str(review_id),json.dumps(token))
                    # send_wechart = account_public.sendWechat('账期额度申请单待审核通知',to_wechart,href,'您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',account_result[0]["init_usernickname"],account_result[0]["init_time"])

                date_main["update_user"] = env.uid
                date_main["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                result = env['xlcrm.account'].sudo().browse(review_id).write(date_main)
            result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            # for r in result:
            #     for f in r.keys():
            #         if f == "station_no":
            #             r["station_desc"] = account_public.Stations('帐期额度申请单').getStionsDesc(r[f])
            #     r["review_type"] = account_public.FormType(r["review_type"]).getType()
            #     r["login_user"] = env.uid
            for r in result:
                r["station_desc"] = account.getStionsDesc(r['station_no'])
                r["review_type"] = account_public.FormType(r["review_type"]).getType()
                r["login_user"] = env.uid
                if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
                    r["status_id"] = 0
                if r['station_no'] and r['station_no'] == 28:
                    _station = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', r['id'])], order='init_time desc', limit=1)
                    if _station[0]['sign_over'] == 'N':
                        to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                        sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                            'sign_station'] else []
                        signer_nickname = ''
                        signer = ''
                        ne_station = list(set(to_station) - set(sign_station))
                        for sta in ne_station:
                            sig = env['xlcrm.account.signers'].sudo().search_read(
                                [('review_id', '=', r['id']), ('station_no', '=', sta)])
                            if sig:
                                if signer:
                                    signer = signer + ',' + sig[0]['signers']
                                else:
                                    signer = sig[0]['signers']
                                sta_desc = account.getStionsDesc(int(sta))
                                if signer_nickname:
                                    signer_nickname = signer_nickname + ';' + sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env['xlcrm.users'].sudo().search_read(
                                                [('id', 'in', sig[0]['signers'].split(','))]))) + ')'
                                else:
                                    signer_nickname = sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env[
                                                'xlcrm.users'].sudo().search_read(
                                                [('id', 'in',
                                                  sig[0]['signers'].split(','))]))) + ')'
                        if str(env.uid) in signer.split(','):
                            r['status_id'] = 0
                        r['signer'] = [signer]
                        r['signer_nickname'] = signer_nickname
            if result:
                result = result[0]
                result['type'] = "set"
            if success_email:
                env.cr.commit()
                message = "success"
                success = True
            else:
                # env.cr.commit()
                message = "邮件发送失败"
                success = False
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
        return json_response(rp)

    # @http.route([
    #     '/api/v12/objUpdate/accountReview/<string:model>'
    # ], auth='none', type='http', csrf=False, methods=['POST'])
    # def obj_update_account12(self, model=None, ids=None, **kw):
    #     success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
    #     token = kw.pop('token')
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     if not check_sign(token, kw):
    #         return no_sign()
    #     try:
    #         from . import account_public
    #         account = account_public.Stations('帐期额度申请单')
    #         data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
    #         data.pop('backreason')
    #         if '0' in data.keys():
    #             review_id = data['0'].get('review_id')
    #             for da in data.values():
    #                 dtrue = True
    #                 while dtrue:
    #                     dtrue = account_public.updateAccountReview(model, da, env)
    #                     break
    #
    #         else:
    #             review_id = data.get('id') if data.get('station_no') == 1 else data.get('review_id')
    #             account_public.updateAccountReview(model, data, env)
    #         result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    #         account_public.getSigner(env, result, 'set', 'update')
    #         if result:
    #             result = result[0]
    #
    #     except Exception as e:
    #         result, success, message = '', False, str(e)
    #     finally:
    #         env.cr.close()
    #
    #     rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
    #     return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/project/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_project(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            data_update = {
                "id": data["id"],
                "name": data["name"],
                "project_no": data["project_no"],
                "application": data["application"],
                "stage_id": data["stage_id"],
                "category_id": data["category_id"],
                "status_id": data["status_id"],
                "customer_id": data["customer_id"],
                "record_status": data["record_status"],
                "desc": data["desc"],
                "customer_price": data["customer_price"],
                "customer_price_currency": data["customer_price_currency"],
                "cpu": data["cpu"],
                "os": data["os"],
                "marketing": data["marketing"],
                "sdkversion": data["sdkversion"],
                "dl_reason": data["dl_reason"],
                "volume": data["volume"],
                "date_from": data["date_from"],
                "date_to": data["date_to"],
                "reviewers": data["reviewers"],
                "cus_product_type_id": data.get("cus_product_type_id"),
                "model_type_id": data.get("model_type_id"),
                "cus_city": data["cus_city"],
                "socket": data["socket"],
                "module": data["module"],
                "total_life_cycle": data["total_life_cycle"],
                "total_life_price": data["total_life_price"]
            }
            obj_id = data["id"]
            data_update["write_user_id"] = env.uid
            if data.get('project_attend_user_ids'):
                data_update['project_attend_user_ids'] = [[6, 0, data['project_attend_user_ids']]]
            result_project = env["xlcrm.project"].sudo().browse(obj_id).write(data_update)
            if result_project:
                ret_object = env["xlcrm.project"].sudo().search_read([('id', '=', obj_id)])[0]
                obj_stage_change_list = request.env["sdo.project.stage.change"].sudo().search_read(
                    [('project_id', '=', obj_id)],
                    ['id', 'stage_id', 'stage_name', 'operation_date_time', 'operation_user_name',
                     'duration_effort'], 0, 0, order='id desc')
                model_fields = request.env["xlcrm.project"].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''
                ret_obj_all = {
                    "project": ret_object,
                    "stage_change_list": obj_stage_change_list
                }
                env.cr.commit()
                message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'data': ret_obj_all}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/visit/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_visit(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            data["write_user_id"] = env.uid
            obj_id = data["id"]
            result_temp = env[model].sudo().browse(obj_id).write(data)

            if result_temp:
                result = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env[model].fields_get()
                for f in result.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if result[f]:
                            result[f] = {'id': result[f][0], 'display_name': result[f][1]}
                        else:
                            result[f] = ''
                from ..public import account_public
                account_public.sendVisitEmail(result, env, result['id'])
                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.commit()
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/sendEmail/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def sendEmail_visit(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            obj_id = data["id"]
            result_object = env[model].sudo().search_read([('id', '=', obj_id)])[0]
            from ..public import account_public
            account_public.sendVisitEmail(result_object, env, obj_id)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/GetSelection/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_selection(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 100000
        token = kw.pop('token')
        env = authenticate(token)

        if not env:
            return no_token()

        try:
            domain = [('record_status', '=', 1)]
            # domain = ['&'] + [('record_status', '=', 1)]
            # domain += ['|']
            # domain += [('create_user_id', '=', env.uid)]
            # domain += [('create_user_id', 'child_of', env.uid)]
            result_obj = request.env[model].sudo().search_read(domain, ['id', 'name'], 0, 0,
                                                               order='id desc')
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result_obj}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectList/<string:model>',
        '/api/v11/getProjectList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        try:
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data"))
                order_field = queryFilter.get("order_field")
                auth_sort = True if order_field in ('brandname', 'logtime') else False
                order_by = queryFilter.get("order_type")
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                limit = limit if limit else 10
                if queryFilter and queryFilter.get("name"):
                    domain.append(('name', 'like', queryFilter.get("name")))
                if queryFilter and queryFilter.get("stage_id"):
                    domain.append(('stage_id', '=', queryFilter.get("stage_id")))
                if queryFilter and queryFilter.get("category_id"):
                    domain.append(('category_id', '=', queryFilter.get("category_id")))
                if queryFilter and queryFilter.get("cus_product_type_id"):
                    domain.append(('cus_product_type_id', '=', queryFilter.get("cus_product_type_id")))
                if queryFilter and queryFilter.get("status_id"):
                    domain.append(('status_id', '=', queryFilter.get("status_id")))
                if queryFilter and queryFilter.get("part_no"):
                    part_no = queryFilter.get("part_no")
                    project_ids = env['sdo.product.line'].sudo().search_read([('product_no', 'ilike', part_no)],
                                                                             fields=['project_id'])
                    project_ids = list(map(lambda x: x['project_id'][0], project_ids))
                    domain.append(('id', 'in', project_ids))
                if queryFilter and queryFilter.get("brandname"):
                    brandname = queryFilter.get("brandname")
                    project_ids = env['sdo.product.line'].sudo().search_read([('brandname', 'ilike', brandname)],
                                                                             fields=['project_id'])
                    project_ids = list(map(lambda x: x['project_id'][0], project_ids))
                    domain.append(('id', 'in', project_ids))
                if queryFilter and queryFilter.get("customer"):
                    customer_ids = env['xlcrm.customer'].sudo().search_read(
                        [('name', 'ilike', queryFilter.get("customer"))],
                        fields=['id'])
                    customer_ids = list(map(lambda x: x['id'], customer_ids))
                    domain.append(('customer_id', 'in', customer_ids))
                if order_field:
                    if order_field == "create_user_nick_name":
                        order_field = 'create_user_id'
                    if order_field == "customer_id.display_name":
                        order_field = 'customer_id'
                    order = order_field + " " + order_by

                records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
                if (records_ref.group_id.id != 1):
                    if (len(domain) > 0):
                        domain = ['&'] + domain
                    domain += ['|']
                    domain += [('create_user_id', '=', records_ref.id)]
                    domain += ['|']
                    domain += ['&', ('record_status', '=', 1), ('project_attend_user_ids', 'ilike', records_ref.id)]
                    domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]

                count = request.env[model].sudo().search_count(domain)
                if not auth_sort:
                    result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
                else:
                    result = request.env[model].sudo().search_read(domain, fields)
                model_fields = request.env[model].fields_get()
                for r in result:
                    for f in r.keys():
                        if model_fields[f]['type'] == 'many2one':
                            if r[f]:
                                r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                            else:
                                r[f] = ''
                    product_no = env['sdo.product.line'].sudo().search_read([('project_id', '=', r['id'])])
                    r['part_no'] = ','.join(list(map(lambda x: x['product_no'], product_no)))
                    r['brandname'] = ','.join(list(map(lambda x: x['brandname'] if x['brandname'] else '', product_no)))
                    r['create_date_time'] = datetime.datetime.strftime(r['create_date_time'], '%Y-%m-%d')
                    r['logtime'] = ''
                    r['child_ids_all'] = records_ref.child_ids_all.ids
                    remark_res = env['xlcrm.project.remark'].sudo().search_read([('project_id', '=', r['id'])],
                                                                                order='write_date desc')
                    if remark_res:
                        r['logtime'] = remark_res[0]['update_time']
                        r['logtime'] = datetime.datetime.strftime(r['logtime'], '%Y-%m-%d %H:%M:%S')
                    reviewers = eval(r['reviewers']) if r['reviewers'] else {}
                    manage = r['create_user_nick_name']
                    if reviewers.get('Manage'):
                        m_user = env['xlcrm.users'].sudo().search([('id', '=', reviewers['Manage'])])
                        manage = ','.join(list(map(lambda x: x['nickname'], m_user)))
                    r['Manage'] = manage
                if auth_sort:
                    st = False if order_by == "asc" else True
                    result.sort(key=lambda x: x[order_field], reverse=st)
                    start = offset * limit
                    end = count if count <= offset * limit + limit else offset * limit + limit
                    result = result[start:end]
                if ids and result and len(ids) == 1:
                    result = result[0]

                    # result['prat']
                message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getccfGroup',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_ccf_group(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            result = request.env['xlcrm.user.ccfgroup'].sudo().search_read()
            for r in result:
                r['users'] = ast.literal_eval(r['users']) if r['users'] else []
            message = "success"
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/createccfGroup'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_ccf_group(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            for val in data.values():
                val['create_user_id'] = env.uid
                res = env['xlcrm.user.ccfgroup'].sudo().search_read([('id', '=', val['id'])])
                if res:
                    env['xlcrm.user.ccfgroup'].sudo().browse(val['id']).write(val)
                else:
                    env['xlcrm.user.ccfgroup'].sudo().create(val)
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/createccfNotice'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_ccf_notice(self, model=None, ids=None, **kw):
        success, message, id = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            id = data.get('id')
            if id:
                data['update_user'] = env.uid
                data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                env['xlcrm.user.ccfnotice'].sudo().browse(id).write(data)
            else:
                id = env['xlcrm.user.ccfnotice'].sudo().create(data).id
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'id': id}
        return json_response(rp)

    @http.route([
        '/api/v11/createccfPMinspector'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_ccf_pminspector(self, model=None, ids=None, **kw):
        success, message, id = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            id = data.get('id')
            if id:
                data['update_user'] = env.uid
                data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                env['xlcrm.user.ccfpminspector'].sudo().browse(id).write(data)
            else:
                id = env['xlcrm.user.ccfpminspector'].sudo().create(data).id
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'id': id}
        return json_response(rp)

    @http.route([
        '/api/v11/getccfNotice',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_ccf_notice(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            domain = []
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data"))
                if queryFilter and queryFilter.get('a_company'):
                    domain.append(('a_company', 'ilike', queryFilter.get('a_company')))
            result = request.env['xlcrm.user.ccfnotice'].sudo().search_read(domain=domain)
            from ..public import account_public as pb
            pa = pb.Stations('')
            for r in result:
                r['lg'] = ast.literal_eval(r['lg']) if r['lg'] else []
                r['risk'] = ast.literal_eval(r['risk']) if r['risk'] else []
                r['fd'] = ast.literal_eval(r['fd']) if r['fd'] else []
                r['lg_label'] = ','.join(list(map(lambda x: pa.getusername(env, x), r['lg'])))
                r['risk_label'] = ','.join(list(map(lambda x: pa.getusername(env, x), r['risk'])))
                r['fd_label'] = ','.join(list(map(lambda x: pa.getusername(env, x), r['fd'])))
            message = "success"
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getccfPMinspector',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_ccf_inspector(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            domain = []
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data"))
                if queryFilter and queryFilter.get('pm'):
                    domain.append(('pm', 'ilike', queryFilter.get('pm')))
            result = request.env['xlcrm.user.ccfpminspector'].sudo().search_read(domain=domain)
            message = "success"
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getProductList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_product_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("name"):
                domain += ['|']
                domain.append(('name', 'like', queryFilter.get("name")))
                domain.append(('product_no', 'like', queryFilter.get("name")))
            if queryFilter and queryFilter.get("status"):
                domain.append(('status', '=', queryFilter.get("status")))
            if queryFilter and queryFilter.get("stage_id"):
                domain.append(('stage_id', '=', queryFilter.get("stage_id")))
            if queryFilter and queryFilter.get("category_id"):
                domain.append(('category_id', '=', queryFilter.get("category_id")))
            if queryFilter and queryFilter.get("customer_id"):
                domain.append(('customer_id', '=', queryFilter.get("customer_id")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['|']
                domain += [('create_user_id', 'in', records_ref.child_ids_all.ids)]
                domain += [('department_id', '=', records_ref.department_id.id)]
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProductListForSelection/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_product_list_for_selection(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("name"):
                domain.append(('product_no', 'like', queryFilter.get("name")))
            if queryFilter and queryFilter.get("status"):
                domain.append(('status', '=', queryFilter.get("status")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            domain = [('create_user_id', '=', records_ref.id)]
        domain = searchargs(domain)
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProductLineListByProjectId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_product_line_list_by_project_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("project_id"):
                domain.append(('project_id', '=', queryFilter.get("project_id")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env["sdo.product.line"].sudo().search_count(domain)
            result = request.env["sdo.product.line"].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env["sdo.product.line"].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
                r['brandname'] = request.env['sdo.product'].sudo().search_read([('id', '=', r['product_id']['id'])],
                                                                               fields=['brand_name'])
                r['brandname'] = r['brandname'][0]['brand_name'] if r['brandname'] else ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getRemarksByProjectId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_remarks_by_project_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("project_id"):
                domain.append(('project_id', '=', queryFilter.get("project_id")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env["xlcrm.project.remark"].sudo().search_count(domain)
            result = request.env["xlcrm.project.remark"].sudo().search_read(domain, fields, offset * limit, limit,
                                                                            order)
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getAccountList/<string:model>',
        '/api/v11/getAccountList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields',
                             "['review_type','a_company','kc_company','signer','signer_nickname','status_id','station_no','init_usernickname','init_time','init_user','update_time','update_usernickname','isback','account_attend_user_ids']"))
        order = kw.get('order', "update_time desc")
        if kw.get("data"):
            json_data = kw.get("data").replace('null', 'None')
            queryFilter = ast.literal_eval(json_data)
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("project_id"):
                domain.append(('review_type', '=', queryFilter.get("project_id")))
            if queryFilter and queryFilter.has_key("status_id"):
                if queryFilter.get("status_id") != '':
                    if queryFilter.get("status_id") == 0:  # 0表示待签核人
                        domain.append(('signer', '=', env.uid))
                    else:
                        domain.append(('status_id', '=', queryFilter.get("status_id")))

            if queryFilter and queryFilter.get("sdate"):
                domain.append(('create_date', '>=', queryFilter.get("sdate")))
            if queryFilter and queryFilter.get("edate"):
                domain.append(('create_date', '<=', queryFilter.get("edate")))
            if queryFilter and queryFilter.get("order_field"):
                condition = queryFilter.get("order_field")
                if condition == "init_usernickname":
                    condition = 'init_user'
                    order = condition + " " + queryFilter.get("order_type")
                elif condition == "update_usernickname":
                    condition = 'update_user'
                    order = condition + " " + queryFilter.get("order_type")
                elif condition == "signer_desc":
                    order = "signer " + queryFilter.get("order_type") + ',' + 'station_desc ' + queryFilter.get(
                        "order_type")
                else:
                    order = condition + " " + queryFilter.get("order_type")

        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('init_user', '=', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), '|', ('account_attend_user_ids', 'ilike', records_ref.id)]

                # 财务文丽蔓可以看下辖员工签过的单
                station_sign = ''
                if records_ref['username'] == 'wenlm@szsunray.com':
                    childs = records_ref.child_ids_all.ids
                    station_sign = 35
                    domain += ['|']
                    for index, child in enumerate(childs):
                        # if index % 2 == 0:
                        #     domain += ['|']
                        domain += [('account_attend_user_ids', 'ilike', child)]
                        if index < len(childs) - 1:
                            domain += ['|']
                if records_ref['username'] == 'jinhuihui@szsunray.com':
                    childs = records_ref.child_ids_all.ids
                    station_sign = 25
                    domain += ['|']
                    for index, child in enumerate(childs):
                        # if index % 2 == 0:
                        #     domain += ['|']
                        domain += [('account_attend_user_ids', 'ilike', child)]
                        if index < len(childs) - 1:
                            domain += ['|']
                domain += [('init_user', 'in', records_ref.child_ids_all.ids)]
                if station_sign:
                    domain += [('station_no', '>', station_sign)]

            count = request.env[model].sudo().search_count(domain)
            if queryFilter.get("order_field") and queryFilter.get("order_field") != 'status_id':
                result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            else:
                result = request.env[model].sudo().search_read(domain, fields, order=order)

            from ..public import account_public
            ap = account_public.Stations('帐期额度申请单')
            for r in result:
                r["station_desc"] = ap.getStionsDesc(r["station_no"])
                r["review_type"] = account_public.FormType(r["review_type"]).getType()
                r["login_user"] = env.uid
                if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
                    r["status_id"] = 0
                if r['station_no'] and r['station_no'] == 28:
                    _station = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', r['id'])], order='init_time desc', limit=1)
                    if _station[0]['sign_over'] == 'N':
                        to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                        sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                            'sign_station'] else []
                        signer_nickname = ''
                        signer = ''
                        ne_station = list(set(to_station) - set(sign_station))
                        for sta in ne_station:
                            sig = env['xlcrm.account.signers'].sudo().search_read(
                                [('review_id', '=', r['id']), ('station_no', '=', sta)])
                            if sig:
                                if signer:
                                    signer = signer + ',' + sig[0]['signers']
                                else:
                                    signer = sig[0]['signers']
                                sta_desc = ap.getStionsDesc(int(sta))
                                if signer_nickname:
                                    signer_nickname = signer_nickname + ';' + sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env['xlcrm.users'].sudo().search_read(
                                                [('id', 'in', sig[0]['signers'].split(','))]))) + ')'
                                else:
                                    signer_nickname = sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env[
                                                'xlcrm.users'].sudo().search_read(
                                                [('id', 'in',
                                                  sig[0]['signers'].split(','))]))) + ')'
                        if str(env.uid) in signer.split(','):
                            r['status_id'] = 0
                        r['signer'] = [signer]
                        r['signer_nickname'] = signer_nickname
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        if not queryFilter.get("order_field") or queryFilter.get("order_field") == 'status_id':
            st = False if not queryFilter.get("order_type") or queryFilter.get("order_type") == "asc" else True
            result.sort(key=lambda x: x['status_id'], reverse=st)
            start = offset * limit
            end = count if count <= offset * limit + limit else offset * limit + limit
            result = result[start:end]
        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    # @http.route([
    #     '/api/v12/getAccountList/<string:model>',
    #     '/api/v12/getAccountList/<string:model>/<string:ids>'
    # ], auth='none', type='http', csrf=False, methods=['GET'])
    # def get_account_list12(self, model=None, ids=None, **kw):
    #     success, message, result, count, offset, limit = True, '', '', 0, 0, 25
    #     token = kw.pop('token')
    #     # token = token if token else get_token(1).pop('token').pop('token')
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     domain = []
    #     fields = eval(kw.get('fields', "[]"))
    #     order = kw.get('order', "update_time desc")
    #     order_field, order_type = '', ''
    #     if kw.get("data"):
    #         json_data = kw.get("data").replace('null', 'None')
    #         queryFilter = ast.literal_eval(json_data)
    #         order_field = queryFilter.get('order_field') if queryFilter.get('order_field') else 'status_id'
    #         order_type = queryFilter.get('order_type') if queryFilter.get('order_type') else 'asc'
    #         offset = queryFilter.pop("page_no") - 1
    #         limit = queryFilter.pop("page_size")
    #         if queryFilter and queryFilter.get("project_id"):
    #             domain.append(('review_type', '=', queryFilter.get("project_id")))
    #         if queryFilter and queryFilter.get("status_id"):
    #             domain.append(('status_id', '=', queryFilter.get("status_id")))
    #         if queryFilter and queryFilter.get("sdate"):
    #             domain.append(('create_date', '>=', queryFilter.get("sdate")))
    #         if queryFilter and queryFilter.get("edate"):
    #             domain.append(('create_date', '<=', queryFilter.get("edate")))
    #         if queryFilter and queryFilter.get("usdate"):
    #             domain.append(('station_no', '=', 99))
    #             domain.append(('update_time', '>=', queryFilter.get("usdate")))
    #         if queryFilter and queryFilter.get("uedate"):
    #             domain.append(('station_no', '=', 99))
    #             domain.append(('update_time', '<=', queryFilter.get("uedate")))
    #         if queryFilter and queryFilter.get("a_company"):
    #             domain.append(('a_company', 'ilike', queryFilter.get("a_company")))
    #         if queryFilter and queryFilter.get("department"):
    #             domain.append(('department', 'ilike', queryFilter.get("department")))
    #         if queryFilter and queryFilter.get("kc_company"):
    #             domain.append(('kc_company', 'ilike', queryFilter.get("kc_company")))
    #         if queryFilter and queryFilter.get("init_usernickname"):
    #             domain.append(('init_usernickname', '=', queryFilter.get("init_usernickname")))
    #         if order_field:
    #             condition = order_field
    #             if condition == "init_usernickname":
    #                 condition = 'init_user'
    #                 order = condition + " " + order_type
    #             elif condition == "update_usernickname":
    #                 condition = 'update_user'
    #                 order = condition + " " + order_type
    #             elif condition == "signer_desc":
    #                 order = "signer " + order_type + ',' + 'station_desc ' + order_type
    #             else:
    #                 order = condition + " " + order_type
    #
    #     try:
    #         records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
    #         if records_ref.group_id.id != 1 and env.uid not in (165, 166):
    #             if len(domain) > 0:
    #                 domain = ['&'] + domain
    #             domain += ['|']
    #             domain += [('init_user', '=', records_ref.id)]
    #             domain += ['&', ('record_status', '=', 1), '|', ('account_attend_user_ids', 'ilike', records_ref.id)]
    #
    #             # 财务文丽蔓可以看下辖员工签过的单
    #             station_sign = ''
    #             if records_ref['username'] == 'wenlm@szsunray.com':
    #                 childs = records_ref.child_ids_all.ids
    #                 station_sign = 35
    #                 domain += ['|']
    #                 for index, child in enumerate(childs):
    #                     domain += [('account_attend_user_ids', 'ilike', child)]
    #                     if index < len(childs) - 1:
    #                         domain += ['|']
    #             if records_ref['username'] == 'jinhuihui@szsunray.com':
    #                 childs = records_ref.child_ids_all.ids
    #                 station_sign = 25
    #                 domain += ['|']
    #                 for index, child in enumerate(childs):
    #                     # if index % 2 == 0:
    #                     #     domain += ['|']
    #                     domain += [('account_attend_user_ids', 'ilike', child)]
    #                     if index < len(childs) - 1:
    #                         domain += ['|']
    #             domain += [('init_user', 'in', records_ref.child_ids_all.ids)]
    #             if station_sign:
    #                 domain += [('station_no', '>=', station_sign)]
    #
    #         if env.uid == 4:
    #             domain = [('signer', '=', 4)]
    #         count = request.env[model].sudo().search_count(domain)
    #         if not order_field or order_field != 'status_id':
    #             result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
    #         else:
    #             result = request.env[model].sudo().search_read(domain, fields, order=order)
    #         from . import account_public
    #         ap = account_public.Stations('帐期额度申请单')
    #         for r in result:
    #             if queryFilter.get("export"):
    #                 current_account_period = []
    #                 profit = []
    #                 if r['current_account_period']:
    #                     current_account_period = ast.literal_eval(r['current_account_period'])
    #                 r['current_account_period'] = current_account_period
    #                 if r['cs']:
    #                     cs_ = eval(r['cs'])
    #                     r['registered_captial'] = cs_['registered_capital'] + cs_[
    #                         'registered_capital_currency']
    #                     r['paid_capital'] = cs_['paid_capital'] + cs_['paid_capital_currency']
    #                     r['insured_persons'] = cs_['insured_persons']
    #                 else:
    #                     res_customer = env['xlcrm.account.customer'].sudo().search_read([('review_id', '=', r['id'])])
    #                     if res_customer:
    #                         res_customer = res_customer[0]
    #                         r['registered_captial'] = res_customer['registered_capital'] + res_customer[
    #                             'registered_capital_currency']
    #                         r['paid_capital'] = res_customer['paid_capital'] + res_customer['paid_capital_currency']
    #                         r['insured_persons'] = res_customer['insured_persons']
    #                 res_fdm = env['xlcrm.account.fd'].sudo().search_read(
    #                     [('review_id', '=', r['id']), ('station_no', '=', 36)])
    #                 if res_fdm:
    #                     res_fdm = res_fdm[0]
    #                     r['factoring'] = res_fdm['factoring_limit'] if res_fdm['factoring'] == '有' else res_fdm[
    #                         'factoring']
    #                 res_lg = env['xlcrm.account.lg'].sudo().search_read([('review_id', '=', r['id'])])
    #                 if res_lg:
    #                     res_lg = res_lg[0]
    #                     r['consignee'] = res_lg['consignee']
    #                 res_pm = env['xlcrm.account.pm'].sudo().search_read([('review_id', '=', r['id'])],
    #                                                                     fields=['brandname', 'profit'])
    #                 if res_pm:
    #                     profit = res_pm
    #                 r['brand_profit'] = profit
    #                 res_csvp = env['xlcrm.account.csvp'].sudo().search_read([('review_id', '=', r['id'])])
    #                 if res_csvp:
    #                     res_csvp = res_csvp[0]
    #                     r['others'] = res_csvp['content']
    #             if datetime.datetime.strptime(r['init_time'], '%Y-%m-%d %H:%M:%S') > datetime.datetime.strptime(
    #                     '2020-10-24',
    #                     '%Y-%m-%d'):
    #                 account_public.getSigner(env, [r], 'set', 'update')
    #             else:
    #                 account_public.getaccountlistold(r, env, ap)
    #         if ids and result and len(ids) == 1:
    #             result = result[0]
    #         message = "success"
    #     except Exception as e:
    #         result, success, message = '', False, str(e)
    #     finally:
    #         env.cr.close()
    #
    #     if order_field == 'status_id':
    #         st = False if not order_type or order_type == "asc" else True
    #         result.sort(key=lambda x: x['status_id'], reverse=st)
    #         start = offset * limit
    #         end = count if count <= offset * limit + limit else offset * limit + limit
    #         result = result[start:end]
    #
    #     rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
    #           'per_page': limit}
    #     return json_response(rp)

    @http.route([
        '/api/v11/changeStop',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def changestop(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            review_id = data.get('id')
            stop_status = data.get('stop_status', 0)
            env['xlcrm.account'].sudo().browse(review_id).write({'stop_status': stop_status})
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectReviewList/<string:model>',
        '/api/v11/getProjectReviewList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_review_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            domain = []
            if queryFilter and queryFilter.get("project_name"):
                project_ids = [app['id'] for app in request.env['xlcrm.project'].sudo().search_read(
                    [('name', 'like', queryFilter.get("project_name"))], ['id'])]
                if project_ids:
                    domain.append(('project_id', 'in', project_ids))
            if queryFilter and queryFilter.get("from_stage_id"):
                domain.append(('from_stage_id', '=', queryFilter.get("from_stage_id")))
            if queryFilter and queryFilter.get("to_stage_id"):
                domain.append(('to_stage_id', '=', queryFilter.get("to_stage_id")))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("project_id"):
                domain.append(('project_id', '=', queryFilter.get("project_id")))
            if queryFilter and queryFilter.get("review_title"):
                domain.append(('review_title', 'like', queryFilter.get("review_title")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), ('review_user_ids', '=ilike', records_ref.id)]
            count = request.env[model].sudo().search_count(domain)
            result = env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            if result:
                for reviewItem in result:
                    if reviewItem['review_commit_ids']:
                        commits = request.env['xlcrm.review.commit'].sudo().search(
                            [('id', 'in', reviewItem['review_commit_ids'])])
                        ret_commits = []
                        for commit_item in commits:
                            ret_commits.append({
                                'id': commit_item.id,
                                'star_level': commit_item.star_level,
                                'review_result_id': commit_item.review_result_id,
                                'review_comment': commit_item.review_comment,
                                'date_commit': commit_item.date_commit,
                                'user_id': {
                                    'id': commit_item.user_id.id,
                                    'username': commit_item.user_id.username
                                }
                            })
                        reviewItem['review_commits'] = ret_commits
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCommitListByReviewId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_commit_list_by_review_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if kw.get("review_id"):
            review_id = kw.get("review_id")
            try:
                records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
                canCommit = 0
                count_no_commit_child = request.env["xlcrm.review.commit"].sudo().search_count(
                    [('review_result_id', '=', 0),
                     ('review_id', '=', int(review_id)),
                     ('user_id', 'in', records_ref.child_ids_all.ids),
                     ('user_id', '!=', env.uid)])
                if count_no_commit_child == 0:
                    canCommit = 1
                review_ref = env['xlcrm.project.review'].sudo().search([("id", '=', review_id)])
                if review_ref['review_commit_ids']:
                    commits = request.env['xlcrm.review.commit'].sudo().search(
                        [('id', 'in', review_ref['review_commit_ids'].ids)])
                    ret_commits = []
                    for commit_item in commits:
                        ret_commits.append({
                            'id': commit_item.id,
                            'star_level': commit_item.star_level,
                            'review_result_id': commit_item.review_result_id,
                            'review_comment': commit_item.review_comment,
                            'date_commit': commit_item.date_commit,
                            'user_id': {
                                'id': commit_item.user_id.id,
                                'username': commit_item.user_id.username,
                                'nickname': commit_item.user_id.nickname
                            },
                            'canCommit': canCommit
                        })
                    result = ret_commits
                success = True
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count}
        return json_response(rp)

    # @http.route([
    #     '/api/v11/getCommitListByAccountId'
    # ], auth='none', type='http', csrf=False, methods=['GET'])
    # def get_commit_list_by_account_id(self, model=None, ids=None, **kw):
    #     success, message, result, count, offset, limit = True, '', '', 0, 0, 25
    #     token = kw.pop('token')
    #     env = authenticate(token)
    #     result = []
    #     rejects_result = []
    #     if not env:
    #         return no_token()
    #     if kw.get("review_id"):
    #         review_id = int(kw.get("review_id"))
    #         try:
    #             from account_public import Stations
    #             account = Stations("帐期额度申请单")
    #             current_sta = env['xlcrm.account'].sudo().search([("id", '=', review_id)])
    #             if current_sta:
    #                 current_sta = current_sta[0]
    #                 current_station = current_sta["station_no"]
    #                 records_ref = env['xlcrm.account.signers'].sudo().search_read([("review_id", '=', review_id)])
    #                 if records_ref:
    #                     for item in records_ref:
    #                         station_no = item["station_no"]
    #                         signer_model = account.getModel(station_no)
    #                         domain = [("review_id", '=', review_id), ('station_no', '=', station_no)]
    #                         signer_info = env[signer_model].sudo().search_read(domain)
    #                         uid = item["signers"]
    #                         station_desc = account.getStionsDesc(station_no)
    #                         timestamp = ''
    #                         signed = False
    #                         if current_station == 28:
    #                             back = env['xlcrm.account.partial'].sudo().search_read([('review_id', '=', review_id)],
    #                                                                                    order='init_time desc',
    #                                                                                    limit=1)
    #                             if back and back[0]['from_station'] > station_no:
    #                                 signed = True
    #                         elif current_station > station_no:
    #                             signed = True
    #                         if signer_info:
    #                             # if station_no == 45:
    #                             #     uid =
    #                             if '[' in str(uid):
    #                                 uid = eval(str(uid))
    #                                 uid = [uid] if isinstance(uid, list) else list(uid)
    #                             else:
    #                                 uid = str(uid).split(',')
    #
    #                             for item in signer_info:
    #                                 uid_a = item["update_user"][0]
    #                                 signer = env['xlcrm.users'].sudo().search([("id", '=', uid_a)])
    #                                 description = signer[0]['nickname'] + ' (' + station_desc + ')'
    #                                 if current_station == station_no:
    #                                     if item["update_time"].split(':')[:-1] == current_sta['update_time'].split(':')[
    #                                                                               :-1]:
    #                                         signed = True
    #                                     else:
    #                                         signed = False
    #                                 if signed:
    #                                     timestamp = item["update_time"]
    #                                 result.append(
    #                                     {"station_no": station_no, "description": description, "timestamp": timestamp,
    #                                      "signed": signed})
    #                                 if isinstance(uid[0], str):
    #                                     if str(uid_a) in uid:
    #                                         uid.remove(str(uid_a))
    #                                     if uid_a in uid:
    #                                         uid.remove(uid_a)
    #                                 elif isinstance(uid[0], list) or isinstance(uid, list):
    #                                     if uid_a == uid[0] or uid_a in uid[0]:
    #                                         uid.remove(uid[0])
    #
    #                                 if station_no == 40 or (station_no == 35 and len(signer_info) < 2):
    #                                     uid = []
    #                             for u in uid:
    #                                 signed = False
    #                                 signer = env['xlcrm.users'].sudo().search([("id", '=', u)])
    #                                 description = signer[0]['nickname'] + ' (' + station_desc + ')'
    #                                 result.append(
    #                                     {"station_no": station_no, "description": description, "timestamp": '',
    #                                      "signed": signed})
    #                         else:
    #                             if station_no == 45:
    #                                 uid = eval(uid) if '[' in str(uid) else str(uid).split(',')
    #                                 for ui in uid:
    #                                     dom = [('id', 'in', filter(lambda x: x, uid))] if isinstance(uid, list) else [
    #                                         ('id', 'in', filter(lambda x: x, ui))] if isinstance(ui, list) else [
    #                                         ('id', '=', ui)]
    #
    #                                     nickname = ','.join(
    #                                         map(lambda x: x['nickname'], env['xlcrm.users'].sudo().search_read(dom)))
    #                                     if nickname:
    #                                         description = nickname + ' (' + station_desc + ')'
    #                                     result.append(
    #                                         {"station_no": station_no, "description": description,
    #                                          "timestamp": timestamp,
    #                                          "signed": signed})
    #                                     if isinstance(uid, list):
    #                                         break
    #                             else:
    #                                 uid = list(set(str(uid).split(',')))
    #                                 nickname = ','.join(
    #                                     map(lambda x: x['nickname'], env['xlcrm.users'].sudo().search_read(
    #                                         [('id', 'in', filter(lambda x: x, uid))])))
    #                                 if nickname:
    #                                     description = nickname + ' (' + station_desc + ')'
    #                                     result.append(
    #                                         {"station_no": station_no, "description": description,
    #                                          "timestamp": timestamp,
    #                                          "signed": signed})
    #                 init_user = env["xlcrm.users"].sudo().search_read([("id", "=", current_sta["init_user"]["id"])])[0][
    #                     "nickname"]
    #                 init_time = current_sta["init_time"]
    #                 # result.append(
    #                 #     {"station_no": 1, "description": str(init_user) + " (送出)", "timestamp": init_time})
    #             rejects = env['xlcrm.account.reject'].sudo().search_read([('review_id', '=', review_id)])
    #             if rejects:
    #                 for reject in rejects:
    #                     station_desc = account.getStionsDesc(reject['station_no']).replace('签核', '')
    #                     reason = [reject['reason']]
    #                     init_user = env["xlcrm.users"].sudo().search_read([("id", "=", reject["init_user"][0])])[0][
    #                         "nickname"]
    #                     init_time = reject["init_time"]
    #                     rejects_result.append(
    #                         {"description": station_desc + ' ' + init_user + " (驳回)", "timestamp": init_time,
    #                          'reason': reason})
    #             partials = env['xlcrm.account.partial'].sudo().search_read([('review_id', '=', review_id)])
    #             if partials:
    #                 for partial in partials:
    #                     station_desc = account.getStionsDesc(partial['from_station']).replace('签核', '')
    #                     init_user = env["xlcrm.users"].sudo().search_read([("id", "=", partial["init_user"][0])])[0][
    #                         "nickname"]
    #                     init_time = partial["init_time"]
    #                     reason = []
    #                     to_station = partial["to_station"].split(',')[:-1]
    #                     a = -1
    #                     for i in range(len(to_station)):
    #                         desc = account.getStionsDesc(int(to_station[i])).replace('签核', '')
    #                         if int(to_station[i]) in (20, 21, 25, 30):
    #                             sec = env['xlcrm.account.partial.sec'].sudo().search_read(
    #                                 [('review_id', '=', review_id), ('station_no', '=', int(to_station[i])),
    #                                  ('p_id', '=', partial['id'])])
    #                             if sec:
    #                                 sec = sec[0]
    #                                 brandname = sec['to_brand'].split(',')[:-1]
    #                                 brand_remark = sec["remark"].split("\p")[:-1]
    #                                 for j in range(len(brandname)):
    #                                     desc = '%s(品牌：%s)' % (desc, brandname[j])
    #                                     reason.append(desc + '::--->' + brand_remark[j])
    #                         else:
    #                             a += 1
    #                             remark = partial["remark"].split("\p")[:-1]
    #                             reason.append(desc + '::--->' + remark[a])
    #                         # if not reason:
    #                         #     reason = desc + '  ' + remark[i]
    #                         # else:
    #                         #     reason = reason + '<br/>' + desc + '  ' + remark[i]
    #                     rejects_result.append(
    #                         {"description": station_desc + ' ' + init_user + " (部分驳回)", "timestamp": init_time,
    #                          'reason': reason})
    #
    #             success = True
    #             message = "success"
    #         except Exception as e:
    #             result, success, message = '', False, str(e)
    #         finally:
    #             env.cr.close()
    #     result.sort(key=lambda x: x["station_no"])
    #     rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'rejects_data': rejects_result,
    #           'total': count}
    #     return json_response(rp)

    @http.route([
        '/api/v11/getReviewCommitList/<string:model>',
        '/api/v11/getReviewCommitList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_review_commit_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            domain = []
            if queryFilter and queryFilter.get("project_name"):
                project_ids = [app['id'] for app in request.env['xlcrm.project'].sudo().search_read(
                    [('name', 'like', queryFilter.get("project_name"))], ['id'])]
                if project_ids:
                    domain.append(('project_id', 'in', project_ids))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("review_result_id") != '':
                domain.append(('review_result_id', '=', queryFilter.get("review_result_id")))
            if queryFilter and queryFilter.get("order_field"):
                order_field = queryFilter.get("order_field")
                if order_field == 'user_nick_name':
                    order_field = 'user_id'
                order = order_field + " " + queryFilter.get("order_type")

            is_me = queryFilter.get("isMe") or '0'

        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                if (is_me == '0' and records_ref.child_ids_all.ids):
                    domain += ['|']
                    domain += [('user_id', '=', records_ref.id)]
                    domain += [('user_id', 'in', records_ref.child_ids_all.ids)]
                else:
                    domain += [('user_id', '=', records_ref.id)]
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            for commit in result:
                commit["can_do_commit"] = 0
                if commit["user_id"]["id"] == env.uid:
                    count_no_commit_child = request.env["xlcrm.review.commit"].sudo().search_count(
                        [('review_result_id', '=', 0),
                         ('review_id', '=', commit["review_id"]["id"]),
                         ('user_id', 'in', records_ref.child_ids_all.ids),
                         ('user_id', '!=', env.uid)])
                    if count_no_commit_child == 0:
                        commit["can_do_commit"] = 1
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getReviewCommitListToDo'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_review_commit_list_to_do(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 5
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                result = request.env['xlcrm.review.commit'].sudo().search_read(
                    [('&'), ('review_result_id', '=', 0), ('|'), ('user_id', '=', records_ref.id),
                     ('user_id', 'in', records_ref.child_ids_all.ids)], fields, offset * limit, limit, order)
            else:
                result = request.env['xlcrm.review.commit'].sudo().search_read([('review_result_id', '=', 0)], fields,
                                                                               offset * limit, limit, order)

            model_fields = request.env['xlcrm.review.commit'].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            for commit in result:
                commit["can_do_commit"] = 0
                if commit["user_id"]["id"] == env.uid:
                    count_no_commit_child = request.env["xlcrm.review.commit"].sudo().search_count(
                        [('review_result_id', '=', 0),
                         ('review_id', '=', commit["review_id"]["id"]),
                         ('user_id', 'in', records_ref.child_ids_all.ids),
                         ('user_id', '!=', env.uid)])
                    if count_no_commit_child == 0:
                        commit["can_do_commit"] = 1
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'data': result, 'page': offset + 1, 'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/createProject',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_project(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            userIds = []
            data["create_user_id"] = env.uid
            if data.get('project_attend_user_ids'):
                userIds = data['project_attend_user_ids']
                data['project_attend_user_ids'] = [[6, 0, data['project_attend_user_ids']]]
            data["project_no"] = "PR" + str(env['xlcrm.project'].get_project_max_number()).zfill(6)
            create_id = env["xlcrm.project"].sudo().create(data).id
            if (data['documents']):
                doc_ids = []
                for doc in data['documents']:
                    doc_ids.append(doc['id'])
                # ids = map(int, doc_ids.split(' '))
                env["xlcrm.documents"].sudo().browse(doc_ids).write({"res_id": create_id})
            result_object = env["xlcrm.project"].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env["xlcrm.project"].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''

            stage_change = {
                'project_id': create_id,
                'stage_id': result_object["stage_id"]['id'],
                'from_stage_id': result_object["stage_id"]['id'],
                'to_stage_id': result_object["stage_id"]['id'],
                'operation_user_id': env.uid,
                'duration_effort': 0
            }
            env["sdo.project.stage.change"].sudo().create(stage_change)

            operation_log = {
                'name': '新增项目：' + result_object['name'],
                'operator_user_id': env.uid,
                'content': '新增项目：' + result_object['name'],
                'res_id': result_object['id'],
                'res_model': 'xlcrm.project',
                'res_id_related': result_object['customer_id']['id'],
                'res_model_related': 'xlcrm.customer',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)

            operation_log = {
                'name': '新增项目：' + result_object['name'],
                'operator_user_id': env.uid,
                'content': '新增项目：' + result_object['name'],
                'res_id': result_object['id'],
                'res_model': 'xlcrm.project',
                'res_id_related': result_object['id'],
                'res_model_related': 'xlcrm.project',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)
            # 发送邮件到参会人员
            from ..public import send_email
            # uid = env["xlcrm.users"].sudo().search_read([("id", "=", env.uid)])[0]
            # fromaddr = uid["email"]
            # qqCode = uid["email_password"]
            fromaddr = "crm@szsunray.com"
            qqCode = "Sunray201911"
            email_obj = send_email.Send_email(fromaddr, qqCode)
            sbuject = "项目创建成功通知"
            # userIds = [159, 161]
            emails = env["xlcrm.users"].sudo().search([("id", "in", userIds)])
            to = []
            cc = []
            failed_email = []
            for item in emails:
                # to.append(item["email"])
                # to = [item["email"]]

                to = [odoo.tools.config["test_username"]]
                uid = item["id"]
                # cc = ["yangyouhui@szsunray.com"]
                if odoo.tools.config["enviroment"] == 'PRODUCT':
                    to = [item["email"]]
                token = get_token(uid)
                href = request.httprequest.environ["HTTP_ORIGIN"] + '/#/public/crm-project-list/' + str(
                    create_id) + "/" + json.dumps(token)
                content = """
                            <html lang="en">            
                            <body>
                                <div>
                                    您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;""" + result_object[
                    'create_user_nick_name'] + """创建了""" + result_object['name'] + """项目，需要你参与，请点击
                                    <a href='""" + href + """' ><font color="red">链接</font></a>参与。
                                </div>
                                <div>
                                <br>
                                注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>,用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                                </div>
                            </body>
                            </html>
                            """

                msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                if msg["code"] == 500:  # 邮件发送失败
                    failed_email.append(to)

            env.cr.commit()
            success = True
            if len(failed_email) > 0:
                message = "success" + "邮件发送失败列表" + ";".join(failed_email)
            else:
                message = "新增成功！"
            # env.cr.commit()
            # success = True
            # message = "新增成功！"
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importProjectItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_project(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            userIds = []

            attend_users = []
            from ..public import account_public
            if data.get("date_from"):
                data['date_from'] = account_public.get_date(data['date_from'])
            if data.get("date_to"):
                data['date_to'] = account_public.get_date(data['date_to'])
            if data.get("date_do"):
                data['date_do'] = account_public.get_date(data['date_do'])
            if data.get("create_date_time"):
                data['create_date_time'] = account_public.get_date(data['create_date_time'])
            if data.get("logs_time"):
                data['logs_time'] = account_public.get_date(data['logs_time'])
            sales, pm, manage, fae = [], [], [], []
            if data.get('sales'):
                sal = data['sales'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                sales = [it['id'] for it in s_res] if s_res else []
            if data.get('pm'):
                sal = data['pm'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                pm = [it['id'] for it in s_res] if s_res else []
            if data.get('manage'):
                sal = data['manage'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                manage = [it['id'] for it in s_res] if s_res else []
            if data.get('fae'):
                sal = data['fae'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                fae = [it['id'] for it in s_res] if s_res else []
                if fae:
                    data["create_user_id"] = fae[0]
                else:
                    rp = {'status': 200, 'data': '', 'message': 'fae不存在', 'success': False}
                    return json_response(rp)
            attend_users = sales + pm + manage + fae
            data['reviewers'] = {'Sales': sales, 'PM': pm, 'Manage': manage, 'FAE': fae}
            data['project_attend_user_ids'] = [[6, 0, attend_users]]
            cus_res = env['xlcrm.customer'].sudo().search_read([('name', 'ilike', data['customer'].strip())])
            if cus_res:
                data['customer_id'] = cus_res[0]['id']
            else:
                rp = {'status': 200, 'data': '', 'message': '客户不存在', 'success': False}
                return json_response(rp)
            data['record_status'] = 1
            stage = env['xlcrm.project.stage'].sudo().search_read([('name', '=', data['stage'])])
            if not stage:
                rp = {'status': 200, 'data': '', 'message': '项目阶段%s不存在' % data['stage'], 'success': False}
                return json_response(rp)
            category = env['xlcrm.project.category'].sudo().search_read([('name', '=', data['category'])])
            data['category_id'] = category[0]['id']
            data['stage_id'] = stage[0]['id']
            data['status_id'] = 6 if data['stage_id'] == 5 else data['stage_id']
            # 芯片或模组类型
            model_typeres = env['xlcrm.project.model'].sudo().search_read([('name', '=', data['model_type'])])
            if model_typeres:
                data['model_type_id'] = model_typeres[0]['id']
            else:
                rp = {'status': 200, 'data': '', 'message': '芯片或模组类型不存在', 'success': False}
                return json_response(rp)

            pro_res = env['xlcrm.project'].sudo().search_read([('name', '=', data['name'])])
            if pro_res:
                pro_id = pro_res[0]['id']
                env["xlcrm.project"].sudo().browse(pro_id).write(data)
            else:
                data["project_no"] = "PR" + str(env['xlcrm.project'].get_project_max_number()).zfill(6)
                pro_id = env["xlcrm.project"].sudo().create(data).id
            log_inituser = env['xlcrm.users'].sudo().search_read([('nickname', '=', data['logs_create'])])
            if log_inituser:
                log_inituser = log_inituser[0]['id']
            else:
                rp = {'status': 200, 'data': '', 'message': '日志操作人不存在', 'success': False}
                return json_response(rp)
            stage_change = {
                'project_id': pro_id,
                'stage_id': data['stage_id'],
                'from_stage_id': data['stage_id'],
                'to_stage_id': data['stage_id'],
                'operation_user_id': env.uid,
                'duration_effort': 0
            }
            env["sdo.project.stage.change"].sudo().create(stage_change)
            logsdata = {
                "project_id": pro_id,
                "content": data.get('logs_content', ''),
                "init_user": log_inituser,
                "update_user": log_inituser,
                "update_time": data['logs_time']
            }
            logs_res = env["xlcrm.project.remark"].sudo().search_read([('project_id', '=', pro_id)])
            if logs_res:
                env["xlcrm.project.remark"].sudo().browse(logs_res[0]['id']).write(logsdata)
            else:
                env["xlcrm.project.remark"].sudo().create(logsdata)
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/createProjectReview/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_project_review(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            userIds = data['review_user_ids']
            data['review_user_ids'] = [[6, 0, userIds]]
            data['status_id'] = 1
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            if (data['documents']):
                doc_ids = []
                for doc in data['documents']:
                    doc_ids.append(doc['id'])
                # ids = map(int, doc_ids.split(' '))
                env["xlcrm.documents"].sudo().browse(doc_ids).write({"res_id": create_id})
            if (data['record_status'] == 1):
                for selected_user_id in userIds:
                    review_commit_item = {
                        'review_id': create_id,
                        'user_id': selected_user_id,
                        'create_user_id': env.uid
                    }
                    env["xlcrm.review.commit"].sudo().create(review_commit_item)
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            if result_object['review_commit_ids']:
                commits = request.env['xlcrm.review.commit'].sudo().search(
                    [('id', 'in', result_object['review_commit_ids'])])
                ret_commits = []
                for commit_item in commits:
                    ret_commits.append({
                        'id': commit_item.id,
                        'star_level': commit_item.star_level,
                        'review_result_id': commit_item.review_result_id,
                        'review_comment': commit_item.review_comment,
                        'date_commit': commit_item.date_commit,
                        'user_id': {
                            'id': commit_item.user_id.id,
                            'username': commit_item.user_id.username
                        }
                    })
                result_object['review_commits'] = ret_commits

            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''

            result_object_project = \
                env["xlcrm.project"].sudo().search_read([('id', '=', result_object["project_id"]["id"])])[0]
            model_fields_project = request.env["xlcrm.project"].fields_get()
            for f in result_object_project.keys():
                if model_fields_project[f]['type'] == 'many2one':
                    if result_object_project[f]:
                        result_object_project[f] = {'id': result_object_project[f][0],
                                                    'display_name': result_object_project[f][1]}
                    else:
                        result_object_project[f] = ''

            operation_log = {
                'name': '新增评审：' + result_object['review_title'],
                'operator_user_id': env.uid,
                'content': '新增评审：' + result_object['review_title'],
                'res_id': result_object['id'],
                'res_model': 'xlcrm.project.review',
                'res_id_related': result_object['project_id']['id'],
                'res_model_related': 'xlcrm.project',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)
            # env.cr.commit()
            # success = True
            # message = "success"
            # 发送邮件到参会人员
            from ..public import send_email,account_public
            uid = env["xlcrm.users"].sudo().search_read([("id", "=", env.uid)])[0]
            # fromaddr = uid["email"]
            # qqCode = uid["email_password"]
            fromaddr = "crm@szsunray.com"
            qqCode = "Sunray201911"
            email_obj = send_email.Send_email(fromaddr, qqCode)
            sbuject = "项目评审创建成功通知"
            # userIds = [159, 161]
            emails = env["xlcrm.users"].sudo().search_read([("id", "in", userIds)])
            to = []
            cc = []
            failed_email = []
            send_wechart = True
            for item in emails:
                # to.append(item["email"])
                # to = [item["email"]]
                to = [odoo.tools.config["test_username"]]
                to_wechart = odoo.tools.config["test_wechat"]
                uid = item["id"]
                # cc = ["yangyouhui@szsunray.com"]
                if odoo.tools.config["enviroment"] == 'PRODUCT':
                    to = [item["email"]]
                    to_wechart = item['nickname'] + '，' + item["username"]
                token = get_token(uid)
                href = request.httprequest.environ["HTTP_ORIGIN"] + '/#/public/crm-review-reviewcommit-list/' + str(
                    create_id) + "/" + json.dumps(token)
                import hashlib
                userinfo = base64.urlsafe_b64encode(to_wechart.encode()).decode()
                appkey = odoo.tools.config["appkey"]
                sign = hashlib.new('md5', (userinfo + appkey).encode()).hexdigest()
                url = 'http://crm.szsunray.com:9030/public/crm-review-reviewcommit-list/%d/%s/%s' % (
                    create_id, userinfo, sign)
                # user = base64.urlsafe_b64encode(to_wechart.encode())
                # url = 'http://crm.szsunray.com:9030/public/crm-review-reviewcommit-list/%s/%s' % (str(create_id), user)
                content = """
                <html lang="en">            
                <body>
                    <div>
                        您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;现有项目发起评审了，需要你参与评审结果的填写，请在规定时间内点击
                        <a href='""" + href + """' ><font color="red">PC端链接</font></a>或<a href='""" + url + """' ><font color="red">移动端链接</font></a>进行结果的提交
                    </div>
                    <div>
                    <br>
                    注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>，用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                    </div>
                </body>
                </html>
                """

                msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                if msg["code"] == 500:  # 邮件发送失败
                    failed_email.append(to)
                # 发微信通知
                account_result = env[model].sudo().search_read([('id', '=', create_id)])
                send_wechart = account_public.sendWechat('账期额度申请单待审核通知', to_wechart, url,
                                                         '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
                                                         account_result[0]["create_user_nick_name"],
                                                         datetime.datetime.strftime(
                                                             account_result[0]["create_date_time"],
                                                             '%Y-%m-%d %H:%M:%S'))
            env.cr.commit()
            success = True
            if len(failed_email) > 0:
                message = "success" + "邮件发送失败列表" + ";".join(failed_email)
            elif send_wechart:
                if not isinstance(send_wechart, bool):
                    send_wechart.commit()
                    send_wechart.close()
                message = "success"
        except Exception as e:
            result_object_project, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'dataProject': result_object_project, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/importProjectReview',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_project_review(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            userIds = []
            attend_users = []
            sales, pm, manage, fae = [], [], [], []
            if data.get('sales'):
                sal = data['sales'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                sales = [it['id'] for it in s_res] if s_res else []
            if data.get('pm'):
                sal = data['pm'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                pm = [it['id'] for it in s_res] if s_res else []
            if data.get('manage'):
                sal = data['manage'].split('，')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                manage = [it['id'] for it in s_res] if s_res else []
            if data.get('fae'):
                sal = data['fae'].split(',')
                s_res = env['xlcrm.users'].sudo().search_read([('nickname', 'in', sal)])
                fae = [it['id'] for it in s_res] if s_res else []
                data["create_user_id"] = fae[0]
            attend_users = sales + pm + manage + fae
            data['status_id'] = 3
            # data["create_user_id"] = env.uid
            data['record_status'] = 1
            data['review_user_ids'] = [[6, 0, attend_users]]
            data['review_result_id'] = 1
            project_res = env['xlcrm.project'].sudo().search_read([('name', '=', data['name'])])
            if project_res:
                data['project_id'] = project_res[0]['id']
                data['status_id'] = project_res[0]['status_id'][0]
                data['from_stage_id'] = project_res[0]['stage_id'][0]
                data['to_stage_id'] = data['from_stage_id'] + 1
            else:
                rp = {'status': 200, 'data': '', 'message': '项目不存在', 'success': False}
                return json_response(rp)
            create_id = env["xlcrm.project.review"].sudo().create(data).id
            att_user = set(attend_users)
            for us in att_user:
                review_commit_item = {
                    'review_id': create_id,
                    'user_id': us,
                    'create_user_id': env.uid,
                    'review_comment': '通过',
                    'status_id': 1,
                    'review_result_id': 1
                }
                env["xlcrm.review.commit"].sudo().create(review_commit_item)
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object_project, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': '', 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/createProjectRemark',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_project_remark(self, model=None, success=True, result=[], message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            project_id = data.get('project_id')
            content = data.get('content')
            id = data.get('id')
            data['update_user'] = env.uid
            data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
            if not id:
                data["init_user"] = env.uid
                id = env['xlcrm.project.remark'].sudo().create(data).id
            else:
                env['xlcrm.project.remark'].sudo().browse(id).write(
                    {'content': content, 'update_time': data['update_time']})
            result = env['xlcrm.project.remark'].sudo().search_read([('id', '=', id)])
            if result:
                result = result[0]
            env.cr.commit()
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/createAccount/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_account(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            from ..public import account_public
            data['station_no'] = 1
            data["init_user"] = env.uid
            data["update_user"] = env.uid
            data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            sta = account_public.Stations('帐期额度申请单')
            if data.has_key('account_attend_user_ids'):
                data['account_attend_user_ids'] = [[6, 0, data['account_attend_user_ids']]]
            result_object = {}
            # recode_status=0表示保存，1表示提交，草稿无下一站签核人
            record_status = data.get('record_status')
            type = 'add'
            if not data['id']:
                if record_status == 0:
                    data['signer'] = env.uid
                    review_id = env[model].sudo().create(data).id
                else:
                    data['account_attend_user_ids'] = [[6, 0, []]]
                    signers = data.get('reviewers', {})
                    data['station_no'] = 5
                    data['status_id'] = 2
                    data['signer'] = signers.get('Sales')
                    data['station_desc'] = sta.getStionsDesc(5)
                    review_id = env[model].sudo().create(data).id
                    env['xlcrm.account.base'].sudo().create(
                        {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
                    # 写入签核人信息
                    for key, values in signers.items():
                        station_no = sta.getStaions(key)
                        station_desc = sta.getStionsDesc(station_no)
                        signer = values
                        # # 如果下一站是销售BU负责人签核，需要找到salse签核者的主管
                        # if station_no == 15 and signers["Sales"]:
                        #     signer = request.env['xlcrm.users'].sudo().search_read(
                        #         [('id', '=', signers["Sales"])], ['parent_ids'])
                        #     if signer:
                        #         signer = signer[0]['parent_ids'][0]
                        # # 如果下一站是MKT签核，需要找到PM签核者的主管
                        # if station_no == 30 and signers["PM"]:
                        #     signer = request.env['xlcrm.users'].sudo().search_read(
                        #         [('id', '=', signers["PM"])], ['parent_ids'])
                        #     if signer:
                        #         signer = signer[0]['parent_ids']
                        #         signer = signer[0] if not (signer.remove(4) if 4 in signer else signer[0]) else signer[
                        #             0]
                        #         # 朱总不签核
                        # if signer == 4:
                        #     continue
                        # if signer:
                        #     if ',' in str(signer):
                        #         for s in signer.split(','):
                        #             data['account_attend_user_ids'][0][2].append(int(s))
                        #     else:
                        #         data['account_attend_user_ids'][0][2].append(signer)
                        #     env['xlcrm.account.signers'].sudo().create(
                        #         {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                        #          'signers': signer})
                        signer = [signer] if isinstance(signer, int) else signer
                        if signer and 4 in signer:
                            signer.remove(4)
                        if signer:
                            for s in signer:
                                data['account_attend_user_ids'][0][2].append(s)
                            env['xlcrm.account.signers'].sudo().create(
                                {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                                 'signers': ','.join(map(lambda x: str(x), signer))})
            else:
                type = 'set'
                if record_status == 0:
                    data['signer'] = env.uid
                    review_id = data['id']
                    env[model].sudo().browse(review_id).write(data)
                    result_object = env[model].sudo().search_read([('id', '=', review_id)])
                else:
                    data['account_attend_user_ids'] = [[6, 0, []]]
                    signers = data.get('reviewers', {})
                    data['station_no'] = 5
                    data['status_id'] = 2
                    data['signer'] = signers.get('Sales')
                    data['station_desc'] = sta.getStionsDesc(5)
                    review_id = data['id']
                    env[model].sudo().browse(review_id).write(data)
                    env['xlcrm.account.base'].sudo().search([('review_id', '=', review_id)]).unlink()
                    env['xlcrm.account.base'].sudo().create(
                        {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
                    sta_list = []
                    # 写入签核人信息
                    for key, values in signers.items():
                        station_no = sta.getStaions(key)
                        station_desc = sta.getStionsDesc(station_no)
                        signer = values
                        # # 如果下一站是销售BU负责人签核，需要找到salse签核者的主管
                        # if station_no == 15 and signers["Sales"]:
                        #     signer = request.env['xlcrm.users'].sudo().search_read(
                        #         [('id', '=', signers["Sales"])], ['parent_ids'])
                        #     if signer:
                        #         signer = signer[0]['parent_ids'][0]
                        # # 如果下一站是MKT签核，需要找到PM签核者的主管
                        # if station_no == 30 and signers["PM"]:
                        #     signer = request.env['xlcrm.users'].sudo().search_read(
                        #         [('id', '=', signers["PM"])], ['parent_ids'])
                        #     if signer:
                        #         signer = signer[0]['parent_ids']
                        #         signer = signer[0] if not (signer.remove(4) if 4 in signer else signer[0]) else signer[
                        #             0]
                        #
                        #         # if signer:
                        #
                        # # 朱总不签核
                        # if signer == 4:
                        #     continue
                        # if signer:
                        #     if ',' in str(signer):
                        #         for s in signer.split(','):
                        #             data['account_attend_user_ids'][0][2].append(int(s))
                        #     else:
                        #         data['account_attend_user_ids'][0][2].append(signer)
                        #     env['xlcrm.account.signers'].sudo().create(
                        #         {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                        #          'signers': signer})
                        signer = [signer] if isinstance(signer, int) else signer
                        if signer and 4 in signer:
                            signer.remove(4)
                        if signer:
                            for s in signer:
                                data['account_attend_user_ids'][0][2].append(s)
                            sign_result = env['xlcrm.account.signers'].sudo().search_read(
                                [('review_id', '=', review_id), ('station_no', '=', station_no)])
                            if sign_result:
                                write_data = {}
                                signers = ','.join(map(lambda x: str(x), signer))
                                if sign_result[0]['signers'] == signers:
                                    write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                                else:
                                    write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                                    write_data['signers'] = signers
                                env['xlcrm.account.signers'].sudo().browse(sign_result[0]['id']).write(write_data)
                            else:
                                env['xlcrm.account.signers'].sudo().create(
                                    {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                                     'signers': ','.join(map(lambda x: str(x), signer))})
                            station_model = sta.getModel(station_no)
                            signed_result = env[station_model].sudo().search_read(
                                [('review_id', '=', review_id), ('station_no', '=', station_no)])
                            if signed_result and signed_result[0]['init_user'][0] not in signer:
                                env[station_model].sudo().browse(signed_result[0]['id']).unlink()

                            sta_list.append(station_no)
                    # 删除不在这次签核人
                    no_station = env['xlcrm.account.signers'].sudo().search_read(
                        [('review_id', '=', review_id), ('station_no', 'not in', sta_list)])
                    env['xlcrm.account.signers'].sudo().search(
                        [('review_id', '=', review_id), ('station_no', 'not in', sta_list)]).unlink()

                    # 删除不在这次签核签核记录
                    if no_station:
                        for no_st in no_station:
                            no_model = sta.getModel(no_st['station_no'])
                            env[no_model].sudo().search([('review_id', '=', review_id)]).unlink()

            env[model].sudo().browse(review_id).write({"account_attend_user_ids": data['account_attend_user_ids']})
            result_object = env[model].sudo().search_read([('id', '=', review_id)])
            # 更新documents
            documents = data['filedata']
            doucument_ids = []
            for item in documents:
                doucument_ids.append(item['document_id'])
            if doucument_ids:
                env['xlcrm.documents'].sudo().browse(doucument_ids).write({'res_id': review_id})
            for r in result_object:
                for f in r.keys():
                    if f == "station_no":
                        r["station_desc"] = account_public.Stations('帐期额度申请单').getStionsDesc(r[f])
                r["review_type"] = account_public.FormType(r["review_type"]).getType()
                r["login_user"] = env.uid
                if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
                    r["status_id"] = 0
            success_email = True
            if result_object:
                result_object = result_object[0]
                result_object['type'] = type
                if result_object['signer'] and record_status > 0:
                    from ..public import send_email
                    email_obj = send_email.Send_email()
                    uid = result_object['signer'][0]
                    # fromaddr = "crm@szsunray.com"
                    # qqCode = "Sunray201911"
                    sbuject = "帐期额度申请单待审核通知"
                    # to = ["yangyouhui@szsunray.com"]
                    to = [odoo.tools.config["test_username"]]
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        to = [request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)["email"]]
                    token = get_token(uid)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/account-list_new/' + str(
                        review_id) + "/" + json.dumps(token)
                    content = """
                        <html lang="en">            
                        <body>
                            <div>
                                您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
                                <a href='""" + href + """' ><font color="red">链接</font></a>进入系统审核
                            </div>
                            <div>
                            <br>
                            注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>，用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                            </div>
                        </body>
                        </html>
                        """
                    msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                    if msg["code"] == 500:  # 邮件发送失败
                        success_email = False
            if success_email:
                env.cr.commit()
                success = True
                message = "success"
            else:
                success = False
                message = "通知邮件发送失败"
        except Exception as e:
            result_object, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'dataProject': result_object, 'message': message,
              'success': success}
        return json_response(rp)

    # @http.route([
    #     '/api/v12/createAccount/<string:model>',
    # ], auth='none', type='http', csrf=False, methods=['POST'])
    # def create_account2(self, model=None, success=True, message='', **kw):
    #     token = kw.pop('token')
    #     # token = token if token else get_token(1).pop('token').pop('token')
    #     data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     if not check_sign(token, kw):
    #         return no_sign()
    #     try:
    #         from . import account_public
    #         data['station_no'] = 1
    #         data["init_user"] = env.uid
    #         data["update_user"] = env.uid
    #         data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
    #         sta = account_public.Stations('帐期额度申请单')
    #         result_object = {}
    #         # recode_status=0表示保存，1表示提交，草稿无下一站签核人
    #         record_status = data.get('record_status')
    #         data['account_attend_user_ids'] = [[6, 0, []]]
    #
    #         products = data['products']
    #         data['reviewers']['PM'] = map(lambda x: x.get('PM'), products)
    #         data['reviewers']['PMins'] = []
    #         PMinspector_brandnames = ''
    #         for pmin in data['products']:
    #             pmin['PMins'] = ''
    #             if pmin.get('PM'):
    #                 res_ = env['xlcrm.user.ccfpminspector'].sudo().search_read([('pm', 'ilike', pmin.get('PM'))])
    #                 if res_:
    #                     PMinspector_brandnames = PMinspector_brandnames + ',' + pmin.get(
    #                         'brandname') if PMinspector_brandnames else pmin.get('brandname')
    #                     data['reviewers']['PMins'].append(res_[0]['inspector'])
    #                     pmin['PMins'] = res_[0]['inspector']
    #         data['reviewers']['PMM'] = map(lambda x: x.get('PMM'), products)
    #         data['reviewers']['PUR'] = map(lambda x: x.get('PUR'), products)
    #         specialsigner = env['xlcrm.user.ccfgroup'].sudo().search_read(
    #             [('status', '=', 1)],
    #             fields=['users', 'name'])
    #         type = 'add'
    #         if not data.get('id'):
    #             if record_status == 0:
    #                 data['signer'] = env.uid
    #                 review_id = env[model].sudo().create(data).id
    #             else:
    #                 signers = sta.getuserId(env, data['reviewers'])
    #                 data['reviewers']['Base'] = env.uid
    #                 data['station_no'] = 5
    #                 data['status_id'] = 2
    #                 data['signer'] = signers.get('Sales')
    #                 data['station_desc'] = sta.getStionsDesc(5)
    #                 review_id = env[model].sudo().create(data).id
    #                 env['xlcrm.account.base'].sudo().create(
    #                     {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
    #                 # signers['ChairMan'] = 3
    #                 if data['a_company'] not in ('深蕾半导体（香港）有限公司', '深圳前海深蕾半导体有限公司'):
    #                     # 添加总经理跟董事长签核人
    #                     signers['Manage'] = 4
    #                     # 添加风控签核人
    #                     riskSigner = filter(lambda x: x['name'] == "RISK", specialsigner)
    #                     if riskSigner:
    #                         riskSigner = [eval(riskSigner[0]['users'])]
    #                     else:
    #                         rp = {'status': 200, 'data': [], 'dataProject': [],
    #                               'message': '无风控审核人，请联系管理员维护风控组成员',
    #                               'success': False}
    #                         return json_response(rp)
    #
    #                     # 添加法务,财务签核人/非款到发货
    #                     if data['release_time_apply'] != '款到发货':
    #                         lgSigner = filter(lambda x: x['name'] == "LG", specialsigner)
    #                         riskSignerM = filter(lambda x: x['name'] == "RISKM", specialsigner)
    #                         fdSigner = filter(lambda x: x['name'] == "FD", specialsigner)
    #                         fdSignerM = filter(lambda x: x['name'] == "FDM", specialsigner)
    #                         if lgSigner and riskSignerM and fdSigner and fdSignerM:
    #                             lgSigner = eval(lgSigner[0]['users'])
    #                             riskSignerM = eval(riskSignerM[0]['users'])
    #                             fdSigner = eval(fdSigner[0]['users'])
    #                             fdSignerM = eval(fdSignerM[0]['users'])
    #                             riskSigner.append(riskSignerM[0])
    #                         else:
    #                             rp = {'status': 200, 'data': [], 'dataProject': [],
    #                                   'message': '非款到发货需要法务,财务及风控主管签核，请联系管理员维护法务组成员及风控主管',
    #                                   'success': False}
    #                             return json_response(rp)
    #
    #                         signers['LG'] = lgSigner
    #                         signers['FD'] = fdSigner
    #                         signers['FDM'] = fdSignerM
    #                     signers['RISK'] = riskSigner
    #
    #                 # 写入签核人信息(pm,pmm,pur除外)
    #                 for key, values in signers.items():
    #                     station_no = sta.getStaions(key)
    #                     station_desc = sta.getStionsDesc(station_no)
    #                     signer = values
    #                     signer = [signer] if isinstance(signer, int) else signer
    #                     # if signer and 4 in signer:
    #                     #     signer.remove(4)
    #                     if signer:
    #                         for s in signer:
    #                             if s:
    #                                 if isinstance(s, list):
    #                                     data['account_attend_user_ids'][0][2] += s
    #                                 else:
    #                                     data['account_attend_user_ids'][0][2].append(s)
    #
    #                         brandname = ''
    #                         if station_no in (20, 25, 30):
    #                             brandname = ','.join(map(lambda x: x['brandname'], products))
    #                         if station_no == 21:
    #                             brandname = PMinspector_brandnames
    #                         env['xlcrm.account.signers'].sudo().create(
    #                             {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
    #                              'signers': ','.join(map(lambda x: str(x), signer)), 'brandname': brandname})
    #         else:
    #             type = 'set'
    #             if record_status == 0:
    #                 data['signer'] = env.uid
    #                 review_id = data['id']
    #                 env[model].sudo().browse(review_id).write(data)
    #                 result_object = env[model].sudo().search_read([('id', '=', review_id)])
    #             else:
    #                 data['account_attend_user_ids'] = [[6, 0, []]]
    #                 signers = sta.getuserId(env, data['reviewers'])
    #                 data['reviewers']['Base'] = env.uid
    #                 data['station_no'] = 5
    #                 data['status_id'] = 2
    #                 data['signer'] = signers.get('Sales')
    #                 data['station_desc'] = sta.getStionsDesc(5)
    #                 review_id = data['id']
    #                 env[model].sudo().browse(review_id).write(data)
    #                 env['xlcrm.account.base'].sudo().search([('review_id', '=', review_id)]).unlink()
    #                 env['xlcrm.account.base'].sudo().create(
    #                     {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
    #                 sta_list = []
    #                 # signers['ChairMan'] = 3
    #                 if data['a_company'] not in ('深蕾半导体（香港）有限公司', '深圳前海深蕾半导体有限公司'):
    #                     # 添加总经理跟董事长签核人
    #                     signers['Manage'] = 4
    #                     # 添加风控签核人
    #                     riskSigner = filter(lambda x: x['name'] == "RISK", specialsigner)
    #                     if riskSigner:
    #                         riskSigner = [eval(riskSigner[0]['users'])]
    #                     else:
    #                         rp = {'status': 200, 'data': [], 'dataProject': [],
    #                               'message': '无风控审核人，请联系管理员维护风控组成员',
    #                               'success': False}
    #                         return json_response(rp)
    #                     # 添加法务,财务签核人/非款到发货
    #                     if data['release_time_apply'] != '款到发货':
    #                         lgSigner = filter(lambda x: x['name'] == "LG", specialsigner)
    #                         riskSignerM = filter(lambda x: x['name'] == "RISKM", specialsigner)
    #                         fdSigner = filter(lambda x: x['name'] == "FD", specialsigner)
    #                         fdSignerM = filter(lambda x: x['name'] == "FDM", specialsigner)
    #                         if lgSigner and riskSignerM and fdSigner and fdSignerM:
    #                             lgSigner = eval(lgSigner[0]['users'])
    #                             riskSignerM = eval(riskSignerM[0]['users'])
    #                             fdSigner = eval(fdSigner[0]['users'])
    #                             fdSignerM = eval(fdSignerM[0]['users'])
    #                             riskSigner.append(riskSignerM[0])
    #                         else:
    #                             rp = {'status': 200, 'data': [], 'dataProject': [],
    #                                   'message': '非款到发货需要法务,财务及风控主管签核，请联系管理员维护法务组成员及风控主管',
    #                                   'success': False}
    #                             return json_response(rp)
    #
    #                         signers['LG'] = lgSigner
    #                         signers['FD'] = fdSigner
    #                         signers['FDM'] = fdSignerM
    #                     signers['RISK'] = riskSigner
    #                 # 写入签核人信息
    #                 for key, values in signers.items():
    #                     station_no = sta.getStaions(key)
    #                     station_desc = sta.getStionsDesc(station_no)
    #                     signer = values
    #                     signer = [signer] if isinstance(signer, int) else signer
    #                     # if signer and 4 in signer:
    #                     #     signer.remove(4)
    #                     if signer:
    #                         for s in signer:
    #                             if s:
    #                                 if isinstance(s, list):
    #                                     data['account_attend_user_ids'][0][2] += s
    #                                 else:
    #                                     data['account_attend_user_ids'][0][2].append(s)
    #                         sign_result = env['xlcrm.account.signers'].sudo().search_read(
    #                             [('review_id', '=', review_id), ('station_no', '=', station_no)])
    #                         if sign_result:
    #                             write_data = {}
    #                             signers = ','.join(map(lambda x: str(x), signer))
    #                             write_data['signed'] = ''
    #                             write_data['brandnamed'] = ''
    #                             if station_no in (20, 25, 30):
    #                                 write_data['brandname'] = ','.join(map(lambda x: x['brandname'], products))
    #                             if station_no == 21:
    #                                 write_data['brandname'] = PMinspector_brandnames
    #                             if sign_result[0]['signers'] == signers:
    #                                 write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
    #                             else:
    #                                 write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
    #                                 write_data['signers'] = signers
    #                             env['xlcrm.account.signers'].sudo().browse(sign_result[0]['id']).write(write_data)
    #                         else:
    #                             brandname = ''
    #                             if station_no in (20, 25, 30):
    #                                 brandname = ','.join(map(lambda x: x['brandname'], products))
    #                             if station_no == 21:
    #                                 brandname = PMinspector_brandnames
    #                             env['xlcrm.account.signers'].sudo().create(
    #                                 {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
    #                                  'signers': ','.join(map(lambda x: str(x), signer)), 'brandname': brandname})
    #                         station_model = sta.getModel(station_no)
    #                         signed_result = env[station_model].sudo().search_read(
    #                             [('review_id', '=', review_id), ('station_no', '=', station_no)])
    #                         if signed_result and signed_result[0]['init_user'][0] not in signer:
    #                             env[station_model].sudo().browse(signed_result[0]['id']).unlink()
    #
    #                         sta_list.append(station_no)
    #                 # 删除不在这次签核人
    #                 no_station = env['xlcrm.account.signers'].sudo().search_read(
    #                     [('review_id', '=', review_id), ('station_no', 'not in', sta_list)])
    #                 env['xlcrm.account.signers'].sudo().search(
    #                     [('review_id', '=', review_id), ('station_no', 'not in', sta_list)]).unlink()
    #
    #                 # 删除不在这次签核签核记录
    #                 if no_station:
    #                     for no_st in no_station:
    #                         no_model = sta.getModel(no_st['station_no'])
    #                         env[no_model].sudo().search([('review_id', '=', review_id)]).unlink()
    #                 # 如果品牌变更，则品牌相关sales，pm，采购，mktvp原有的签核记录删除
    #                 new_brandnames = map(lambda x: x['brandname'], data['products'])
    #                 sales_res = env['xlcrm.account.sales'].sudo().search_read([('review_id', '=', review_id)])
    #                 if sales_res:
    #                     s_product = eval(sales_res[0]['products'])
    #                     s_brandname = map(lambda x: x['brandname'], s_product)
    #                     if not set(s_brandname) == set(new_brandnames):
    #                         new_product = [
    #                             filter(lambda x: x['brandname'] == bra, s_product)[0] if bra in s_brandname else {
    #                                 'brandname': bra, 'currency': '万人民币', 'turnover': ''} for bra in new_brandnames]
    #                         env['xlcrm.account.sales'].sudo().browse(sales_res[0]['id']).write(
    #                             {'products': new_product})
    #                     # s_brandname = map(lambda x: x['brandname'], eval(sales_res[0]['products']))
    #                     # if not set(s_brandname) < set(new_brandnames):
    #                     #     env['xlcrm.account.sales'].sudo().browse(sales_res[0]['id']).unlink()
    #                 for mo in ('pm', 'pmins', 'pur', 'pmm'):
    #                     mo = 'xlcrm.account.%s' % mo
    #                     pm_res = env[mo].sudo().search_read([('review_id', '=', review_id)])
    #                     if pm_res:
    #                         for p_res in pm_res:
    #                             if not p_res['brandname'] in new_brandnames:
    #                                 env[mo].sudo().browse(p_res['id']).unlink()
    #
    #         env[model].sudo().browse(review_id).write({"account_attend_user_ids": data['account_attend_user_ids']})
    #         result_object = env[model].sudo().search_read([('id', '=', review_id)])
    #         # 更新documents
    #         documents = data.get('filedata', [])
    #         doucument_ids = []
    #         for item in documents:
    #             doucument_ids.append(item['document_id'])
    #         if doucument_ids:
    #             env['xlcrm.documents'].sudo().browse(doucument_ids).write({'res_id': review_id})
    #         for r in result_object:
    #             for f in r.keys():
    #                 if f == "station_no":
    #                     r["station_desc"] = account_public.Stations('帐期额度申请单').getStionsDesc(r[f])
    #             r["review_type"] = account_public.FormType(r["review_type"]).getType()
    #             r["login_user"] = env.uid
    #             if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
    #                 r["status_id"] = 0
    #         success_email = True
    #         if result_object:
    #             result_object = result_object[0]
    #             result_object['type'] = type
    #             if result_object['signer'] and record_status > 0:
    #                 from . import send_email
    #                 email_obj = send_email.Send_email()
    #                 uid = result_object['signer'][0]
    #                 # fromaddr = "crm@szsunray.com"
    #                 # qqCode = "Sunray201911"
    #                 sbuject = "帐期额度申请单待审核通知"
    #                 # to = ["yangyouhui@szsunray.com"]
    #                 to = [odoo.tools.config["test_username"]]
    #                 to_wechart = odoo.tools.config["test_wechat"]
    #                 cc = []
    #                 if odoo.tools.config["enviroment"] == 'PRODUCT':
    #                     user = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
    #                     to = [user["email"]]
    #                     to_wechart = user['nickname'] + '，' + user["username"]
    #                 token = get_token(uid)
    #                 href = request.httprequest.environ[
    #                            "HTTP_ORIGIN"] + '/#/public/account-list_new/' + str(
    #                     review_id) + "/" + json.dumps(token)
    #                 import hashlib
    #                 userinfo = base64.urlsafe_b64encode(to_wechart.encode())
    #                 appkey = odoo.tools.config["appkey"]
    #                 sign = hashlib.new('md5', userinfo + appkey).hexdigest()
    #                 url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
    #                     review_id, userinfo, sign)
    #
    #                 content = """
    #                         <html lang="en">
    #                         <body>
    #                             <div>
    #                                 您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
    #                                 <a href='""" + href + """' ><font color="red">PC端链接</font></a>或<a href='""" + url + """' ><font color="red">移动端链接</font></a>进入系统审核
    #                             </div>
    #                             <div>
    #                             <br>
    #                             注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>，用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
    #                             </div>
    #                         </body>
    #                         </html>
    #                         """
    #                 msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
    #                 if msg["code"] == 500:  # 邮件发送失败
    #                     success_email = False
    #                 # 发微信通知
    #                 account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    #                 from .account_public import sendWechat
    #                 send_wechart = sendWechat('账期额度申请单待审核通知', to_wechart, url,
    #                                           '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
    #                                           account_result[0]["init_usernickname"],
    #                                           account_result[0]["init_time"])
    #         if success_email:
    #             env.cr.commit()
    #             success = True
    #             message = "success"
    #         else:
    #             success = False
    #             message = "通知邮件发送失败"
    #     except Exception as e:
    #         result_object, result_object, success, message = '', '', False, str(e)
    #     finally:
    #         env.cr.close()
    #     rp = {'status': 200, 'data': result_object, 'dataProject': result_object, 'message': message,
    #           'success': success}
    #     return json_response(rp)

    # @http.route([
    #     '/api/v11/reCallByAccountId',
    # ], auth='none', type='http', csrf=False, methods=['POST'])
    # def recall_account(self, model=None, success=True, message='', **kw):
    #     token = kw.pop('token')
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     try:
    #         from . import account_public
    #         review_id = ast.literal_eval(kw.get("review_id"))
    #         data = {}
    #         model = 'xlcrm.account'
    #         data['station_no'] = 1
    #         data['signer'] = ',%d,'% env.uid
    #         data["update_user"] = env.uid
    #         data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
    #         data['signer'] = env.uid
    #         data['status_id'] = 1
    #         data['isback'] = 2
    #         data['station_desc'] = '申请者填单'
    #         env[model].sudo().browse(review_id).write(data)
    #         # 判断是否回签
    #         sign_back = env['xlcrm.account.partial'].sudo().search_read(
    #             [('review_id', '=', review_id)], order='init_time desc', limit=1)
    #         if sign_back and sign_back[0]['sign_over'] == 'N':
    #             env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
    #                 {'sign_station': sign_back[0]['to_station']})
    #         result_object = env[model].sudo().search_read([('id', '=', review_id)])
    #         success_email = True
    #         if result_object:
    #             result_object = result_object[0]
    #             result_object['login_user'] = env.uid
    #             result_object['type'] = 'set'
    #             if result_object['signer']:
    #                 from . import send_email
    #                 email_obj = send_email.Send_email()
    #                 uid = result_object['signer'][0]
    #                 # fromaddr = "crm@szsunray.com"
    #                 # qqCode = "Sunray201911"
    #                 sbuject = "帐期额度申请单待审核通知"
    #                 to = [odoo.tools.config["test_username"]]
    #                 to_wechart = odoo.tools.config["test_wechat"]
    #                 cc = []
    #                 if odoo.tools.config["enviroment"] == 'PRODUCT':
    #                     user = request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
    #                     to = [user["email"]]
    #                     to_wechart = user['nickname'] + '，' + user["username"]
    #                 token = get_token(uid)
    #                 href = request.httprequest.environ[
    #                            "HTTP_ORIGIN"] + '/#/public/account-list_new/' + str(
    #                     review_id) + "/" + json.dumps(token)
    #                 # url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s' % (
    #                 #     review_id, base64.urlsafe_b64encode(to_wechart.encode()))
    #                 import hashlib
    #                 userinfo = base64.urlsafe_b64encode(to_wechart.encode())
    #                 appkey = odoo.tools.config["appkey"]
    #                 sign = hashlib.new('md5', userinfo + appkey).hexdigest()
    #                 url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
    #                     review_id, userinfo, sign)
    #                 content = """
    #                         <html lang="en">
    #                         <body>
    #                             <div>
    #                                 您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
    #                                 <a href='""" + href + """' ><font color="red">PC端链接</font></a>或<a href='""" + url + """' ><font color="red">移动端链接</font></a>进入系统审核
    #                             </div>
    #                             <div>
    #                             <br>
    #                             注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>，用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
    #                             </div>
    #                         </body>
    #                         </html>
    #                         """
    #                 msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
    #                 if msg["code"] == 500:  # 邮件发送失败
    #                     success_email = False
    #                 # 发微信通知
    #                 from .account_public import sendWechat
    #                 account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    #                 send_wechart = sendWechat('账期额度申请单待审核通知', to_wechart, url,
    #                                           '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
    #                                           account_result[0]["init_usernickname"],
    #                                           account_result[0]["init_time"])
    #         if success_email:
    #             env.cr.commit()
    #             success = True
    #             message = "success"
    #         else:
    #             success = False
    #             message = "通知邮件发送失败"
    #     except Exception as e:
    #         result_object, result_object, success, message = '', '', False, str(e)
    #     finally:
    #         env.cr.close()
    #     rp = {'status': 200, 'message': message, 'data': result_object, 'success': success}
    #     return json_response(rp)

    @http.route([
        '/api/v11/sendwxemail',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def send_wx_email(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        data = [value for value in data.values()]
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            for item in data:
                username = item['username']
                email = item['email']
                nickname = item['nickname']
                from ..public import send_email, connect_mssql
                email_obj = send_email.Send_email()
                sbuject = "微信绑定验证码"
                to = [odoo.tools.config["test_username"]]
                if odoo.tools.config["enviroment"] == 'PRODUCT':
                    to = [email]
                # 写入wechat
                mssql = connect_mssql.Mssql('wechart')
                qu_res = mssql.query("select *from Wx_email where email='%s'" % email)
                now_time = datetime.datetime.now() + datetime.timedelta(hours=8)
                code = send_email.getCode()
                if qu_res:
                    up_res = mssql.in_up_de("update Wx_email set init_time=%s,Code=%s where email=%s",
                                            (now_time, code, email))
                else:
                    up_res = mssql.in_up_de(
                        "insert into Wx_email(email,username,code,active,init_user,init_time)values(%s,%s,%s,%s,%s,%s)",
                        (email, nickname.encode(), code, 1, 'admin', now_time))

                content = """
                        <html lang="en">            
                        <body>
                            <div>
                                您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您的微信绑定验证码为%d，请从手机微信进入“新蕾科技集团公众号”，输入个人邮箱帐号加该验证码（格式形如aaa@szsunray.com,542136）
                            </div>
                            <div>
                            <br>
                                注：该验证码用于绑定个人邮箱和微信号，便于企业微信公众号中网站的免密登录
                            </div>
                        </body>
                        </html>""" % code
                msg = email_obj.send(subject=sbuject, to=to, content=content, env=env)
                if msg['code'] == 200 and up_res:
                    mssql.commit()
                else:
                    success = False
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
            mssql.close()
        rp = {'status': 200, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/getwxemail',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_wxemail(self, model=None, success=True, message='', **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = [('status', '=', 1)]
        fields = []
        order = kw.get('order', "update_time desc")
        condition = ''
        if kw.get("data"):
            json_data = kw.get("data").replace('null', 'None')
            queryFilter = ast.literal_eval(json_data)
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("user"):
                domain.append('|')
                domain.append(('username', 'ilike', queryFilter.get("user")))
                domain.append(('nickname', 'ilike', queryFilter.get("user")))

        try:
            from ..public import connect_mssql
            mssql = connect_mssql.Mssql('wechart')
            result = env['xlcrm.users'].sudo().search_read(domain, fields)
            res_wx = mssql.query('select email,openid,init_time,update_time from Wx_email where 1=1 %s' % condition)
            result_obj = []
            for re in result:
                re_tmp = {}
                wx_tmp = list(filter(lambda x: x[0] == re['email'], res_wx))
                re_tmp['nickname'] = re['nickname']
                re_tmp['username'] = re['username']
                re_tmp['email'] = re['email']
                re_tmp['init_time'] = wx_tmp[0][2] if wx_tmp else ''
                re_tmp['issend'] = '是' if wx_tmp else '否'
                re_tmp['isbind'] = '是' if wx_tmp and wx_tmp[0][1] else '否'
                re_tmp['update_time'] = wx_tmp[0][3] if wx_tmp and wx_tmp[0][3] else ''
                result_obj.append(re_tmp)
            if queryFilter and queryFilter.get("issend"):
                result_obj = filter(lambda x: x['issend'] == queryFilter.get("issend"), result_obj)
            if queryFilter and queryFilter.get("isbind"):
                result_obj = filter(lambda x: x['isbind'] == queryFilter.get("isbind"), result_obj)
            count = len(result_obj)
            result_obj.sort(key=lambda x: x['email'])
            start = offset * limit
            end = count if count <= offset * limit + limit else offset * limit + limit
            result_obj = result_obj[start:end]

            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result_obj, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/changeProjectStage',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def change_project_stage(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')

        sign = ast.literal_eval(list(kw.keys())[0]).get("sign")
        appkey = ast.literal_eval(list(kw.keys())[0]).get("appkey")
        timestamp = ast.literal_eval(list(kw.keys())[0]).get("timestamp")
        format = ast.literal_eval(list(kw.keys())[0]).get("format")
        data = ast.literal_eval(list(kw.keys())[0]).get("data")

        env = authenticate(token)
        if not env:
            return no_token()
        try:
            project_id = data["project_id"]
            to_stage_id = data["to_stage_id"]
            duration_effort = 0
            obj_stage_change_last = \
                env["sdo.project.stage.change"].sudo().search_read([('project_id', '=', project_id)], order='id desc')[
                    0]
            diff = datetime.datetime.now() - datetime.datetime.strptime(obj_stage_change_last['operation_date_time'],
                                                                        '%Y-%m-%d %H:%M:%S')
            duration_effort = round(diff.total_seconds() / 60.0, 2)
            env["sdo.project.stage.change"].sudo().browse(obj_stage_change_last['id']).write(
                {"duration_effort": duration_effort})

            data["operation_user_id"] = env.uid
            data["stage_id"] = to_stage_id
            obj_stage_change_id = env["sdo.project.stage.change"].sudo().create(data).id

            env["xlcrm.project"].sudo().browse(project_id).write({"stage_id": to_stage_id})
            obj_stage_change = env["sdo.project.stage.change"].sudo().search_read([('id', '=', obj_stage_change_id)])[0]
            operation_log = {
                'name': '项目状态变更：' + obj_stage_change["project_name"],
                'operator_user_id': env.uid,
                'content': '项目状态变更，从：' + obj_stage_change['from_stage_name'] + '到：' + obj_stage_change['to_stage_name'],
                'res_id': obj_stage_change['id'],
                'res_model': 'sdo.project.stage.change',
                'res_id_related': obj_stage_change['project_id'][0],
                'res_model_related': 'xlcrm.project',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)
            env.cr.commit()

            ret_object = env["xlcrm.project"].sudo().search_read([('id', '=', project_id)])[0]
            obj_stage_change_list = request.env["sdo.project.stage.change"].sudo().search_read(
                [('project_id', '=', project_id)],
                ['id', 'stage_id', 'stage_name', 'operation_date_time', 'operation_user_name',
                 'duration_effort'], 0, 0, order='id desc')
            model_fields = request.env["xlcrm.project"].fields_get()
            for f in ret_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if ret_object[f]:
                        ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                    else:
                        ret_object[f] = ''
            result = {
                "project": ret_object,
                "stage_change_list": obj_stage_change_list
            }

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/lostProject',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def lost_project(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        sign = ast.literal_eval(list(kw.keys())[0]).get("sign")
        appkey = ast.literal_eval(list(kw.keys())[0]).get("appkey")
        timestamp = ast.literal_eval(list(kw.keys())[0]).get("timestamp")
        format = ast.literal_eval(list(kw.keys())[0]).get("format")
        data = ast.literal_eval(list(kw.keys())[0]).get("data")

        env = authenticate(token)
        if not env:
            return no_token()
        try:
            project_id = data["project_id"]
            dl_reason = data["dl_reason"]
            from_stage_id = data["from_stage_id"]
            to_stage_id = 5
            project_status_id = 6
            duration_effort = 0
            if from_stage_id != to_stage_id:
                obj_stage_change_last = \
                    env["sdo.project.stage.change"].sudo().search_read([('project_id', '=', project_id)],
                                                                       order='id desc')[0]
                diff = datetime.datetime.now() - datetime.datetime.strptime(
                    obj_stage_change_last['operation_date_time'],
                    '%Y-%m-%d %H:%M:%S')
                duration_effort = round(diff.total_seconds() / 60.0, 2)
                env["sdo.project.stage.change"].sudo().browse(obj_stage_change_last['id']).write(
                    {"duration_effort": duration_effort})
                stageChange = {}
                stageChange["operation_user_id"] = env.uid
                stageChange["stage_id"] = to_stage_id
                stageChange["to_stage_id"] = to_stage_id
                stageChange["from_stage_id"] = from_stage_id
                stageChange["project_id"] = project_id
                obj_stage_change_id = env["sdo.project.stage.change"].sudo().create(stageChange).id

                obj_stage_change = \
                    env["sdo.project.stage.change"].sudo().search_read([('id', '=', obj_stage_change_id)])[0]
                operation_log = {
                    'name': '项目状态变更：' + obj_stage_change["project_name"],
                    'operator_user_id': env.uid,
                    'content': '项目状态变更，从：' + obj_stage_change['from_stage_name'] + '到：' + obj_stage_change[
                        'to_stage_name'],
                    'res_id': obj_stage_change['id'],
                    'res_model': 'sdo.project.stage.change',
                    'res_id_related': obj_stage_change['project_id'][0],
                    'res_model_related': 'xlcrm.project',
                    'operation_level': 0,
                    'operation_type': 0
                }
                env["xlcrm.operation.log"].sudo().create(operation_log)

            env["xlcrm.project"].sudo().browse(project_id).write(
                {"stage_id": to_stage_id, 'dl_reason': dl_reason, 'status_id': project_status_id})
            env.cr.commit()
            ret_object = env["xlcrm.project"].sudo().search_read([('id', '=', project_id)])[0]
            obj_stage_change_list = request.env["sdo.project.stage.change"].sudo().search_read(
                [('project_id', '=', project_id)],
                ['id', 'stage_id', 'stage_name', 'operation_date_time', 'operation_user_name',
                 'duration_effort'], 0, 0, order='id desc')
            model_fields = request.env["xlcrm.project"].fields_get()
            for f in ret_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if ret_object[f]:
                        ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                    else:
                        ret_object[f] = ''
            result = {
                "project": ret_object,
                "stage_change_list": obj_stage_change_list
            }

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/createUser/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_user(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            psd = data['password']
            if psd:
                psd = self._crypt_context().encrypt(psd)
                data['password'] = psd
            data["create_user_id"] = env.uid
            if data.get('parent_ids'):
                parent_ids = data['parent_ids']
                data['parent_ids'] = [[6, 0, parent_ids]]
            create_id = env[model].sudo().create(data).id
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/updateUser',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def update_objects_user(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            obj_id = data["id"]
            data["write_user_id"] = env.uid
            if data.get('parent_ids'):
                parent_ids = data['parent_ids']
                data['parent_ids'] = [[6, 0, parent_ids]]
            result = env["xlcrm.users"].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result:
                ret_object = env["xlcrm.users"].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = request.env["xlcrm.users"].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''

                message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': ret_object, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/createCustomerContact',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_contact(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            if (data["project_id"] == '0'):
                data.pop("project_id")
            create_id = env["xlcrm.customer.contact"].sudo().create(data).id
            contact = env["xlcrm.customer.contact"].sudo().search_read([('id', '=', create_id)])[0]
            province_id, city_id, district_id, province_name, city_name, district_name = '', '', '', '', '', ''
            if contact['province_id']:
                province_id = contact['province_id'][0]
            if contact['city_id']:
                city_id = contact['city_id'][0]
            if contact['district_id']:
                district_id = contact['district_id'][0]
            if contact['province_name']:
                province_name = contact['province_name']
            if contact['city_name']:
                city_name = contact['city_name']
            if contact['district_name']:
                district_name = contact['district_name']
            result_object = {
                'id': contact['id'],
                'name': contact['name'],
                'title': contact['title'],
                'mobile': contact['mobile'],
                'phone': contact['phone'],
                'province_id': province_id,
                'city_id': city_id,
                'district_id': district_id,
                'qq': contact['qq'],
                'wechat': contact['wechat'],
                'email': contact['email'],
                'dingding': contact['dingding'],
                'is_default': contact['is_default'],
                'address': contact['address'],
                'gender': contact['gender'],
                'birthday': contact['birthday'],
                'customer_id': contact['customer_id'],
                'province_name': contact['province_name'],
                'city_name': contact['city_name'],
                'district_name': contact['district_name'],
                'regions': province_name + " " + city_name + " " + district_name,
                'create_user_name': contact['create_user_name'],
                "avatar_url": contact["avatar_url"],
                "avatar_id": contact["avatar_id"]
            }

            operation_log = {
                'name': '新增联系人：' + result_object['name'],
                'operator_user_id': env.uid,
                'content': '新增联系人：' + result_object['name'],
                'res_id': result_object['id'],
                'res_model': 'xlcrm.customer.contact',
                'res_id_related': result_object['customer_id'][0],
                'res_model_related': 'xlcrm.customer',
                'operation_level': 0,
                'operation_type': 0
            }
            env["xlcrm.operation.log"].sudo().create(operation_log)

            env.cr.commit()
            success = True
            message = "新增成功！"
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/contact'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_contact(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data = ast.literal_eval(list(kw.keys())[0]).get("data")
            data["write_user_id"] = env.uid
            obj_id = data["id"]
            if (data['birthday'] == 'false'):
                data.pop('birthday')
            if (data['project_id'] == '0'):
                data.pop('project_id')
            result_obj = env["xlcrm.customer.contact"].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result_obj:
                contact = env["xlcrm.customer.contact"].sudo().search_read([('id', '=', obj_id)])[0]
                province_id, city_id, district_id, province_name, city_name, district_name = '', '', '', '', '', ''
                if contact['province_id']:
                    province_id = contact['province_id'][0]
                if contact['city_id']:
                    city_id = contact['city_id'][0]
                if contact['district_id']:
                    district_id = contact['district_id'][0]
                if contact['province_name']:
                    province_name = contact['province_name']
                if contact['city_name']:
                    city_name = contact['city_name']
                if contact['district_name']:
                    district_name = contact['district_name']
                result = {
                    'id': contact['id'],
                    'name': contact['name'],
                    'title': contact['title'],
                    'mobile': contact['mobile'],
                    'phone': contact['phone'],
                    'province_id': province_id,
                    'city_id': city_id,
                    'district_id': district_id,
                    'qq': contact['qq'],
                    'wechat': contact['wechat'],
                    'email': contact['email'],
                    'dingding': contact['dingding'],
                    'is_default': contact['is_default'],
                    'address': contact['address'],
                    'gender': contact['gender'],
                    'birthday': contact['birthday'],
                    'customer_id': contact['customer_id'],
                    'province_name': contact['province_name'],
                    'city_name': contact['city_name'],
                    'district_name': contact['district_name'],
                    'regions': province_name + " " + city_name + " " + district_name,
                    'create_user_name': contact['create_user_name'],
                    "avatar_url": contact["avatar_url"],
                    "avatar_id": contact["avatar_id"]
                }
                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/LoginUser',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def login_user(self, sid=None, success=True, message='', **kw):
        """ service, app(user/login),secret(password) """
        #  pdb.set_trace()
        try:
            serve = odoo.tools.config['serve_url']
            orgin = request.httprequest.environ["HTTP_ORIGIN"]
            db = odoo.tools.config['db_name']
            username = kw.pop('username')
            password = kw.pop('password')
            user_obj = request.env['xlcrm.users'].sudo().search([('username', '=', username), ('status', '=', 1)],
                                                                limit=1)
            valid_pass = False
            if user_obj:
                encrypted = user_obj['password']
                valid_pass, replacement = self._crypt_context().verify_and_update(password, encrypted)

            if orgin == 'http://localhost:8080':
                valid_pass = True

            if not user_obj or not valid_pass:
                success = False
                rp = {'token': '', 'success': success, 'message': '账号或密码不对，请联系系统管理员！'}
                return json_response(rp)

            uid = user_obj['id']
            token = base64.urlsafe_b64encode(
                ','.join([serve, db, username, str(uid), str(int(time.time()))]).encode()).replace(
                b'=', b'').decode()
            token = {
                'token': token,
                'group_id': user_obj['group_id'].id,
                'token_expires': int(time.time()),
                'refresh': base64.urlsafe_b64encode(
                    (token + ',' + str(int(time.time()) + 24 * 60 * 60 * 1)).encode()).decode(),
                'refresh_expires': int(time.time()) + 24 * 60 * 60 * 7
            }
            user = {
                'user_id': uid,
                'username': user_obj['username'],
                'group_id': user_obj['group_id'].id,
                'department_id': user_obj['department_id'].id,
                'nickname': user_obj['nickname'],
                'groupname': user_obj['user_group_name'],
                'departmentname': user_obj['department_name'],
                'head_pic': '',
                'status': user_obj['status']

            }
            result_data = {
                'token': token,
                'user': user
            }
            success = True
            rp = {'data': result_data, 'status': 200, 'success': success, 'message': message}

        except Exception as e:
            success = False
            rp = {'token': '', 'status': 200, 'success': success, 'message': str(e)}
        # finally:
        # request.env.cr.close()

        return json_response(rp)

    @http.route([
        '/api/v12/LoginUser',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def login_user12(self, sid=None, success=True, message='', **kw):
        """ service, app(user/login),secret(password) """
        #  pdb.set_trace()
        try:
            serve = odoo.tools.config['serve_url']
            orgin = request.httprequest.environ["HTTP_ORIGIN"]
            db = odoo.tools.config['db_name']
            username = kw.pop('username')

            password = kw.pop('password')
            user_obj = request.env['xlcrm.users'].sudo().search([('username', '=', username), ('status', '=', 1)],
                                                                limit=1)
            valid_pass = True
            # if user_obj:
            #     encrypted = user_obj['password']
            #     valid_pass, replacement = self._crypt_context().verify_and_update(password, encrypted)

            if orgin == 'http://192.168.1.145:8080':
                valid_pass = True

            if not user_obj or not valid_pass:
                success = False
                msgcode = 'username'
                rp = {'token': '', 'success': success, 'msgcode': msgcode, 'message': '账号或密码不对，请联系系统管理员！'}
                return json_response(rp)

            uid = user_obj['id']
            token = base64.urlsafe_b64encode(
                (','.join([serve, db, username, str(uid), str(int(time.time()))])).encode()).replace(
                b'=', b'').decode()
            token = {
                'token': token,
                'group_id': user_obj['group_id'].id,
                'token_expires': int(time.time()),
                'refresh': base64.urlsafe_b64encode(
                    (token + ',' + str(int(time.time()) + 24 * 60 * 60 * 1)).encode()).decode(),
                'refresh_expires': int(time.time()) + 24 * 60 * 60 * 7
            }
            user = {
                'user_id': uid,
                'username': user_obj['username'],
                'group_id': user_obj['group_id'].id,
                'department_id': user_obj['department_id'].id,
                'nickname': user_obj['nickname'],
                'groupname': user_obj['user_group_name'],
                'departmentname': user_obj['department_name'],
                'head_pic': '',
                'status': user_obj['status']
            }
            result_data = {
                'token': token,
                'user': user
            }
            success = True
            rp = {'data': result_data, 'status': 200, 'success': success, 'message': message}

        except Exception as e:
            success = False
            rp = {'token': '', 'status': 200, 'success': success, 'message': str(e)}
        # finally:
        # request.env.cr.close()

        return json_response(rp)

    @http.route([
        '/api/v12/LoginUser/Wechat',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def login_user_wechat12(self, sid=None, success=True, message='', **kw):
        """ service, app(user/login),secret(password) """
        #  pdb.set_trace()
        try:
            success = True
            result_data = {}
            username = kw.pop('username')
            result_data = {}
            password = kw.pop('password')
            openid = kw.pop('openid')
            user_obj = request.env['xlcrm.users'].sudo().search([('username', '=', username), ('status', '=', 1)],
                                                                limit=1)
            valid_pass = True
            if user_obj:
                encrypted = user_obj['password']
                valid_pass, replacement = self._crypt_context().verify_and_update(password, encrypted)
            if not user_obj or not valid_pass:
                success = False
                msgcode = 'username'
                rp = {'data': result_data, 'status': 200, 'success': success, 'msgcode': msgcode,
                      'message': '账号或密码不对，请联系系统管理员！'}
                return json_response(rp)
            if openid:
                from ..public import connect_mssql
                mssql = connect_mssql.Mssql('wechart')
                qu_res = mssql.query("select email from Wx_email where openid='%s'" % openid)
                user = request.env['xlcrm.users'].sudo().browse(user_obj[0]['id']).write({'wechat_id': openid})
                # user_ex = request.env['xlcrm.users'].sudo().search_read([('id', '=', openid)])
                if qu_res:
                    up = mssql.in_up_de('update Wx_email set openid=%s where email=%s', (openid, user_obj[0]['email']))

                else:
                    now_time = datetime.datetime.now() + datetime.timedelta(hours=8)
                    inser = mssql.in_up_de(
                        'insert into Wx_email(openid,email,username,active,init_user,init_time)values(%s,%s,%s,%s,%s,%s)',
                        (openid, user_obj[0]['email'], user_obj[0]['nickname'], 1, 'admin', now_time))
                mssql.commit()
                mssql.close()
                result_data['username'] = user_obj[0]['username']
            else:
                success = False
                message = '微信帐号错误，请联系系统管理员'

            rp = {'data': result_data, 'status': 200, 'success': success, 'message': message}

        except Exception as e:
            success = False
            rp = {'data': result_data, 'status': 200, 'success': success, 'message': str(e)}
        # finally:
        # request.env.cr.close()

        return json_response(rp)

    @http.route([
        '/api/v12/CheckUser/Wechat',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def check_user_wechat12(self, sid=None, success=True, message='', **kw):
        """ service, app(user/login),secret(password) """
        #  pdb.set_trace()
        try:
            code = kw.get('code')
            success = True
            result_data = {}
            openid = ''
            message = '首次登录需验证帐号密码'
            if code:
                from ..public import connect_mssql,account_public
                openid = account_public.loginwechat(code)
                if openid:
                    db = odoo.tools.config['db_name']
                    # registry = RegistryManager.get(db)
                    cr = registry(db).cursor()
                    env = api.Environment(cr, 1, {})
                    env['xlcrm.wechatlogs'].sudo().create({'openid': openid})
                    mssql = connect_mssql.Mssql('wechart')
                    qu_res = mssql.query("select email from Wx_email where openid='%s'" % openid)
                    user_obj = env['xlcrm.users'].sudo().search(
                        [('wechat_id', '=', openid), ('status', '=', 1)],
                        limit=1)
                    if qu_res and not user_obj:
                        env['xlcrm.users'].sudo().search([('email', '=', qu_res[0][0])]).write(
                            {'wechat_id': openid})
                    env.cr.commit()
                    user_obj = env['xlcrm.users'].sudo().search(
                        [('wechat_id', '=', openid), ('status', '=', 1)],
                        limit=1)
                    if user_obj:
                        result_data['username'] = user_obj[0]['username']
                else:
                    success = False
                    message = '微信帐号错误，请联系系统管理员'
            else:
                success = False
                message = '无效的微信code'

            rp = {'data': result_data, 'status': 200, 'success': success, 'openid': openid, 'message': message}

        except Exception as e:
            success = False
            rp = {'data': result_data, 'status': 200, 'success': success, 'openid': openid, 'message': str(e)}
        # finally:
        # request.env.cr.close()

        return json_response(rp)

    @http.route([
        '/api/v11/refreshUserToken',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def refresh_user_token(self, sid=None, success=True, message='', **kw):
        try:
            env = authenticate(kw.pop('token'))
            serve = odoo.tools.config['serve_url']
            db = odoo.tools.config['db_name']
            user_obj = request.env['xlcrm.users'].sudo().browse(env.uid)

            if not user_obj:
                success = False
                rp = {'token': '', 'success': success, 'message': '请重新登录！'}
                return json_response(rp)

            uid = user_obj['id']
            username = user_obj['username']
            token_value = base64.urlsafe_b64encode((
                                                       ','.join([serve, db, username, str(uid),
                                                                 str(int(time.time()))])).encode()).replace(
                b'=', b'').decode()
            token = {
                'token': token_value,
                'group_id': user_obj['group_id'].id,
                'token_expires': int(time.time()) + 24 * 60 * 60 * 1,
                'refresh': base64.urlsafe_b64encode(
                    (token_value + ',' + str(int(time.time()) + 24 * 60 * 60 * 1)).encode()).decode(),
                'refresh_expires': int(time.time()) + 24 * 60 * 60 * 3
            }
            user = {
                'user_id': uid,
                'username': user_obj['username'],
                'group_id': user_obj['group_id'].id,
                'nickname': user_obj['nickname'],
                'head_pic': '',
                'status': user_obj['status']
            }
            result_data = {
                'token': token,
                'user': user
            }
            success = True
            rp = {'data': result_data, 'status': 200, 'success': success, 'message': message}

        except Exception as e:
            success = False
            rp = {'token': '', 'status': 200, 'success': success, 'message': str(e)}
        # finally:
        #     request.env.cr.close()
        return json_response(rp)

    @http.route([
        '/api/v11/logoutUser',
    ], type='http', auth="none", csrf=False, methods=['POST', 'GET'])
    def logout_user(self, username=None, password='admin', sid=None, success=True, message='', **kw):
        rp = {'status': 200, 'data': True, 'message': 'success'}
        return json_response(rp)

    def _crypt_context(self):
        """ Passlib CryptContext instance used to encrypt and verify
        passwords. Can be overridden if technical, legal or political matters
        require different kdfs than the provided default.

        Requires a CryptContext as deprecation and upgrade notices are used
        internally
        """
        return default_crypt_context

    @http.route([
        '/api/v11/getMenuAuthList'
    ], auth='none', type='http', csrf=False, methods=['GET', 'POST'])
    def get_menu_auth_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = ast.literal_eval(list(kw.keys())[0]).get("token")
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            offset = 0
            limit = 0
            group_id = request.env['xlcrm.users'].sudo().browse(env.uid).group_id.id
            menu_ids = request.env['xlcrm.auth.rule'].sudo().search_read([('group_id', '=', group_id)], ['menu_auth'])
            if menu_ids:
                menu_ids_temp = menu_ids[0]['menu_auth'].replace("[", "").replace("]", "")
                menu_ids = []
                for menu_id in menu_ids_temp.split(','):
                    if menu_id in menu_ids:
                        continue
                    else:
                        menu_ids.append(int(menu_id))
            domain = []
            domain.append(('id', 'in', menu_ids))

            count = request.env['xlcrm.menu'].sudo().search_count(domain)
            result = request.env['xlcrm.menu'].sudo().search_read(domain, order='sort asc')
            model_fields = request.env['xlcrm.menu'].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getMenuList/<string:model>',
        '/api/v11/getMenuList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_menu_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'sort asc')
        if kw.get("data"):
            query_filter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 0
            domain = []
            if query_filter and query_filter.get("module"):
                domain.append(('module', '=', query_filter.get("module")))
            if query_filter and query_filter.get("status"):
                domain.append(('status', '=', query_filter.get("status")))
            if query_filter and query_filter.get("is_navi"):
                domain.append(('is_navi', '=', query_filter.get("is_navi")))
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProductCategoryList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_product_category_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 250
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'sort asc')
        domain = []
        if kw.get("data"):
            query_filter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 0

            if query_filter and query_filter.get("module"):
                domain.append(('module', '=', query_filter.get("module")))
            if query_filter and query_filter.get("status"):
                domain.append(('status', '=', query_filter.get("status")))
            if query_filter and query_filter.get("is_navi"):
                domain.append(('is_navi', '=', query_filter.get("is_navi")))
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = r[f][0]
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getDepartmentList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_department_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 250
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'sort asc')
        domain = []
        if kw.get("data"):
            query_filter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 0

            if query_filter and query_filter.get("module"):
                domain.append(('module', '=', query_filter.get("module")))
            if query_filter and query_filter.get("status"):
                domain.append(('status', '=', query_filter.get("status")))
            if query_filter and query_filter.get("is_navi"):
                domain.append(('is_navi', '=', query_filter.get("is_navi")))
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getBrandList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_brand_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        domain = []
        if kw.get("data"):
            query_filter = ast.literal_eval(kw.get("data"))
            offset = query_filter.pop("page_no") - 1
            limit = query_filter.pop("page_size")

            if query_filter and query_filter.get("name"):
                domain.append(('name', 'like', query_filter.get("name")))
            if query_filter and query_filter.get("module"):
                domain.append(('module', '=', query_filter.get("module")))
            if query_filter and query_filter.get("status"):
                domain.append(('status', '=', query_filter.get("status")))
            if query_filter and query_filter.get("is_navi"):
                domain.append(('is_navi', '=', query_filter.get("is_navi")))
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getAccountPeriod'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_period(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        try:
            if kw.get("data"):
                sql_add = ''
                query_filter = ast.literal_eval(kw.get("data"))
                if query_filter and query_filter.get("cCusName"):
                    sql_add += " and cCusName = '%s'" % query_filter.get("cCusName")
                from ..public import connect_mssql
                mysql = connect_mssql.Mssql('ErpCrmDB')
                result_ = mysql.query(
                    'select cCusType,iCusCreLineThousands,cName,PayType,cexch_name,HasDue from v_Customer_CCF where 1 = 1 %s' % sql_add)
                result = []
                for res in result_:
                    res_temp = {}
                    res_temp['kc_company'] = self.translation(res[0])
                    res_temp['credit_limit_now'] = res[1]
                    res_temp['release_time'] = res[2]
                    res_temp['payment_method'] = res[3]
                    res_temp['credit_limit_now_currency'] = res[4]
                    res_temp['transaction_status'] = '已建档有交易' if res[5] == "1" else '已建档无交易'
                    result.append(res_temp)
                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getAuthRuleList/<string:model>',
        '/api/v11/getAuthRuleList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_authrule_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        if kw.get("data"):
            query_filter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 0
            domain = []
            if query_filter and query_filter.get("module"):
                domain.append(('module', '=', query_filter.get("module")))
            if query_filter and query_filter.get("status"):
                domain.append(('status', '=', query_filter.get("status")))
            if query_filter and query_filter.get("group_id"):
                domain.append(('group_id', '=', query_filter.get("group_id")))
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/createAuthRule/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_rule(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
        except Exception as e:
            result_object, message = '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/partialRejection',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_partial(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            from ..public import account_public
            ap = account_public.Stations('帐期额度申请单')
            review_id = data.pop('review_id')
            from_station = data.pop('from_station')
            record_status = data.pop('record_status')
            par = env['xlcrm.account.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)

            to_station = ''
            remark = ''
            if data:
                for key, value in data.items():
                    to_station += str(ap.getStaionsReject(key)) + ','
                    remark += value['back_remark'] + "\p"
            data['review_id'] = review_id
            data['from_station'] = from_station
            data['to_station'] = to_station
            data['remark'] = remark
            data["init_user"] = env.uid
            if par:
                data['from_id'] = par[0]['id']
                if par[0]['from_station'] == from_station and par[0]['sign_over'] == 'N':
                    env['xlcrm.account.partial'].sudo().browse(par[0]['id']).write(data)
                else:
                    create_id = env['xlcrm.account.partial'].sudo().create(data).id

            else:
                create_id = env['xlcrm.account.partial'].sudo().create(data).id

            if record_status == 1:
                data_up = {'station_no': 28, 'update_time': datetime.datetime.now() + datetime.timedelta(hours=8),
                           'update_user': env.uid, 'signer': ''}
                env['xlcrm.account'].sudo().browse(review_id).write(data_up)
                env.cr.commit()
            result = request.env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            # model_fields = request.env[model].fields_get()
            for r in result:
                r["station_desc"] = ap.getStionsDesc(r['station_no'])
                r["review_type"] = account_public.FormType(r["review_type"]).getType()
                r["login_user"] = env.uid
                if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
                    r["status_id"] = 0
                if r['station_no'] and r['station_no'] == 28:
                    _station = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', r['id'])], order='init_time desc', limit=1)
                    if _station[0]['sign_over'] == 'N':
                        to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                        sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                            'sign_station'] else []
                        signer_nickname = ''
                        signer = ''
                        ne_station = list(set(to_station) - set(sign_station))
                        for sta in ne_station:
                            sig = env['xlcrm.account.signers'].sudo().search_read(
                                [('review_id', '=', r['id']), ('station_no', '=', sta)])
                            if sig:
                                if signer:
                                    signer = signer + ',' + sig[0]['signers']
                                else:
                                    signer = sig[0]['signers']
                                sta_desc = ap.getStionsDesc(int(sta))
                                if signer_nickname:
                                    signer_nickname = signer_nickname + ';' + sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env['xlcrm.users'].sudo().search_read(
                                                [('id', 'in', sig[0]['signers'].split(','))]))) + ')'
                                else:
                                    signer_nickname = sta_desc + '(' + ','.join(
                                        map(lambda x: x['nickname'],
                                            env[
                                                'xlcrm.users'].sudo().search_read(
                                                [('id', 'in',
                                                  sig[0]['signers'].split(','))]))) + ')'
                        if str(env.uid) in signer.split(','):
                            r['status_id'] = 0
                        r['signer'] = [signer]
                        r['signer_nickname'] = signer_nickname
                r['type'] = 'set'
            if result:
                result = result[0]
            env.cr.commit()

            message = "success"
            success = True
        except Exception as e:
            result_object, message, success = '', str(e), False
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success, 'dataProject': result}
        return json_response(rp)

    # @http.route([
    #     '/api/v12/partialRejection',
    # ], auth='none', type='http', csrf=False, methods=['POST'])
    # def create_partial12(self, model=None, success=True, message='', **kw):
    #     token = kw.pop('token')
    #     data = ast.literal_eval(list(kw.keys())[0]).get("data")
    #     env = authenticate(token)
    #     if not env:
    #         return no_token()
    #     if not check_sign(token, kw):
    #         return no_sign()
    #     try:
    #         from . import account_public
    #         ap = account_public.Stations('帐期额度申请单')
    #         review_id = data.pop('review_id')
    #         from_station = data.pop('from_station')
    #         record_status = data.pop('record_status')
    #         par = env['xlcrm.account.partial'].sudo().search_read(
    #             [('review_id', '=', review_id)], order='init_time desc', limit=1)
    #         p_id = par[0]['id'] if par else ''
    #         if par:
    #             data['from_id'] = par[0]['id']
    #             if par[0]['from_station'] == from_station and par[0]['sign_over'] == 'N':
    #                 env['xlcrm.account.partial'].sudo().browse(par[0]['id']).write(data)
    #             else:
    #                 p_id = env['xlcrm.account.partial'].sudo().create(data).id
    #         else:
    #             p_id = env['xlcrm.account.partial'].sudo().create(data).id
    #         to_station = ''
    #         remark = ''
    #         if data:
    #             from_id = data.pop('from_id') if data.get('from_id') else ''
    #             for key, value in data.items():
    #                 station = ap.getStaionsReject(key)
    #                 if key in ('pm', 'pmins', 'pur', 'pmm'):
    #                     to_brand = ''
    #                     b_remark = ''
    #                     b_data = {'init_user': env.uid}
    #                     for kp, vp in value.items():
    #                         to_brand += kp + ','
    #                         b_remark += vp['back_remark'] + '\p'
    #                     b_data['review_id'] = review_id
    #                     b_data['station_no'] = station
    #                     b_data['to_brand'] = to_brand
    #                     b_data['remark'] = b_remark
    #                     b_data['p_id'] = p_id
    #                     env['xlcrm.account.partial.sec'].sudo().create(b_data)
    #                 else:
    #                     remark += value['back_remark'] + '\p'
    #                 to_station += str(station) + ','
    #         data['review_id'] = review_id
    #         data['from_station'] = from_station
    #         data['to_station'] = to_station
    #         data['remark'] = remark
    #         data["init_user"] = env.uid
    #         env['xlcrm.account.partial'].sudo().browse(p_id).write(data)
    #
    #         if record_status == 1:
    #             data_up = {'station_no': 28, 'update_time': datetime.datetime.now() + datetime.timedelta(hours=8),
    #                        'update_user': env.uid, 'signer': ''}
    #             env['xlcrm.account'].sudo().browse(review_id).write(data_up)
    #             env.cr.commit()
    #         result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    #         account_public.getSigner(env, result, 'set', 'partial')
    #         from . import send_email
    #         email_obj = send_email.Send_email()
    #         success_email, send_wechart = True, True
    #         if result:
    #             result = result[0]
    #         if result['signer']:
    #             uid = result['signer']
    #             for ui in uid:
    #                 sbuject = "帐期额度申请单待审核通知"
    #                 to = [odoo.tools.config["test_username"]]
    #                 to_wechart = odoo.tools.config["test_wechat"]
    #                 cc = []
    #                 if odoo.tools.config["enviroment"] == 'PRODUCT':
    #                     user = env['xlcrm.users'].sudo().search([('id', '=', ui)], limit=1)
    #                     to = [user["email"]]
    #                     to_wechart = user['nickname'] + '，' + user["username"]
    #                 token = get_token(ui)
    #                 href = request.httprequest.environ[
    #                            "HTTP_ORIGIN"] + '/#/public/account-list/' + str(
    #                     review_id) + "/" + json.dumps(token)
    #                 # url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s' % (
    #                 #     review_id, base64.urlsafe_b64encode(to_wechart.encode()))
    #                 import hashlib
    #                 userinfo = base64.urlsafe_b64encode(to_wechart.encode())
    #                 appkey = odoo.tools.config["appkey"]
    #                 sign = hashlib.new('md5', userinfo + appkey).hexdigest()
    #                 url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
    #                     review_id, userinfo, sign)
    #                 content = """
    #                                         <html lang="en">
    #                                         <body>
    #                                             <div>
    #                                                 您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
    #                                                 <a href='""" + href + """' ><font color="red">PC端链接</font></a>或<a href='""" + url + """' ><font color="red">移动端链接</font></a>进入系统审核
    #                                             </div>
    #                                             <div>
    #                                             <br>
    #                                             注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>,用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
    #                                             </div>
    #                                         </body>
    #                                         </html>
    #                                         """
    #                 msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
    #                 if msg["code"] == 500:  # 邮件发送失败
    #                     success_email = False
    #                 # 发微信通知
    #                 account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    #                 # user = base64.urlsafe_b64encode(to_wechart.encode())
    #                 # url = 'http://crm.szsunray.com:9030/public/ccf-list/%s/%s' % (str(review_id), user)
    #                 import hashlib
    #                 userinfo = base64.urlsafe_b64encode(to_wechart.encode())
    #                 appkey = odoo.tools.config["appkey"]
    #                 sign = hashlib.new('md5', userinfo + appkey).hexdigest()
    #                 url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
    #                     review_id, userinfo, sign)
    #                 send_wechart = account_public.sendWechat('账期额度申请单待审核通知', to_wechart, url,
    #                                                          '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
    #                                                          account_result[0]["init_usernickname"],
    #                                                          account_result[0]["init_time"])
    #         message = "success"
    #         success = True
    #         if success_email and send_wechart:
    #             env.cr.commit()
    #             if not isinstance(send_wechart, bool):
    #                 send_wechart.commit()
    #                 send_wechart.close()
    #     except Exception as e:
    #         result, message, success = '', str(e), False
    #     finally:
    #         env.cr.close()
    #     rp = {'status': 200, 'message': message, 'success': success, 'dataProject': result}
    #     return json_response(rp)

    @http.route([
        '/api/v11/createMenu/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_menu(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
        except Exception as e:
            result_object, message = '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/createProductCategory/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_product_category(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/createDepartment/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_department(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/addBrandItem/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_product_brand(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/addProductItem/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_product(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            env.cr.commit()
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = request.env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/menustatusupdate'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def menu_status_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        id = ast.literal_eval(list(kw.keys())[0]).get("id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if id:
                records_ref = env['xlcrm.menu'].sudo().search([("id", '=', id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/setProductCategoryStatus'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def product_category_status_update(self, model=None, status=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        id = ast.literal_eval(list(kw.keys())[0]).get("id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if id:
                records_ref = env['sdo.product.category'].sudo().search([("id", '=', id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/setDepartmentStatus'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def department_status_update(self, model=None, status=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        id = ast.literal_eval(list(kw.keys())[0]).get("id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if id:
                records_ref = env['sdo.department'].sudo().search([("id", '=', id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/authrulestatusupdate'
    ], auth='none', type='http', csrf=False, methods=['post'])
    def auth_rule_status_update(self, model=None, group_id=None, status=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        rule_id = ast.literal_eval(list(kw.keys())[0]).get("rule_id")
        status = ast.literal_eval(list(kw.keys())[0]).get("status")
        try:
            if rule_id:
                records_ref = env['xlcrm.auth.rule'].sudo().search([("id", 'in', rule_id)])
                values = {
                    "status": status,
                }
                result = records_ref.sudo().write(values)
                env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getVisitList/<string:model>',
        '/api/v11/getVisitList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_visit_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("title"):
                domain.append(('title', 'like', queryFilter.get("title")))
            if queryFilter and queryFilter.get("customer_id"):
                domain.append(('customer_id', '=', queryFilter.get("customer_id")))
            if queryFilter and queryFilter.get("type_id"):
                domain.append(('type_id', '=', queryFilter.get("type_id")))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("id"):
                domain.append(('id', '=', queryFilter.get("id")))
            if queryFilter and queryFilter.get("create_user_nick_name"):
                domain.append(('create_user_nick_name', '=', queryFilter.get("create_user_nick_name")))
            if queryFilter and queryFilter.get("order_field"):
                order_condition = queryFilter.get("order_field")
                if order_condition == 'create_user_nick_name':
                    order_condition = 'create_user_id'
                order = order_condition + " " + queryFilter.get("order_type")

        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += [('create_user_id', 'in', records_ref.child_ids_all.ids)]

            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = request.env[model].fields_get()
            for r in result:
                for f in r.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if r[f]:
                            r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                        else:
                            r[f] = ''
                result_object = request.env['xlcrm.documents'].sudo().search_read(
                    [('res_id', '=', r['id']), ('res_model', '=', 'xlcrm.visit')])
                res_data = []
                for res in result_object:
                    res_tmp = {'id': res['id'],
                               'name': res['datas_fname'],
                               'url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                   res['id'])
                               }
                    res_data.append(res_tmp)
                r['filelist'] = res_data
            if ids and result and len(ids) == 1:
                result = result[0]
            success = True
            message = '操作成功！'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCalendarDataByCustomerId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_calendar_data_by_customer_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("title"):
                domain.append(('title', 'like', queryFilter.get("title")))
            if queryFilter and queryFilter.get("customer_id"):
                domain.append(('customer_id', '=', queryFilter.get("customer_id")))
            if queryFilter and queryFilter.get("type_id"):
                domain.append(('type_id', '=', queryFilter.get("type_id")))
            if queryFilter and queryFilter.get("status_id"):
                domain.append(('status_id', '=', queryFilter.get("status_id")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if not domain:
            domain = [('write_uid', '=', 1)]

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = request.env['xlcrm.visit'].sudo().search_count(domain)
            resultCalendar = request.env['xlcrm.visit'].sudo().search_read(domain, fields, offset * limit, limit, order)
            result = []
            for cal in resultCalendar:
                result.append({
                    'years': [(cal['visit_date'].split('-')[0])],
                    'months': [(cal['visit_date'].split('-')[1])],
                    'days': [(cal['visit_date'].split('-')[2])],
                    'things': cal['title'],
                    'id': cal['id'],
                    'content': cal['content'][0:10] + ' ...'
                })
            success = True
            message = 'success'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCalendarDataByUserId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_calendar_data_by_user_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env or env.uid == '':
            return no_token()
        domain = [('create_user_id', '=', env.uid)]
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        offset = 0
        limit = 0
        domain = searchargs(domain)
        try:
            count = request.env['xlcrm.visit'].sudo().search_count(domain)
            result_calendar = request.env['xlcrm.visit'].sudo().search_read(domain, fields, offset * limit, limit,
                                                                            order)
            result = []
            for cal in result_calendar:
                if cal['visit_date']:
                    result.append({
                        'years': [(f"{cal['visit_date']}".split('-')[0])],
                        'months': [(f"{cal['visit_date']}".split('-')[1])],
                        'days': [(f"{cal['visit_date']}".split('-')[2])],
                        'things': cal['title'],
                        'id': cal['id'],
                        'content': cal['content'][0:10] + ' ...'
                    })
            success = True
            message = 'success'
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/addfile'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile(self, success=False, message='', ret_data='', file='', **kw):
        if file:
            token = kw.pop('token')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {
                    'name': name,
                    'datas_fname': file.filename,
                    'res_model': 'xlcrm.users',
                    # 'db_datas': base64.b64encode(file_content),
                    'mimetype': file.mimetype,
                    'create_user_id': env.uid,
                    'file_size': size,
                    'type': 'url',
                    'url': url
                }
                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                result_object = env['xlcrm.documents'].sudo().search_read([('id', '=', create_id)])[0]
                ret_data = {'document_id': result_object['id'],
                            'document_url': odoo.tools.config['serve_url'] + '/crm/image/' + str(result_object['id'])
                            }
                env.cr.commit()
                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': ret_data, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/addfilecontact'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_contact(self, success=False, message='', ret_data='', file='', **kw):
        if file:
            token = kw.pop('token')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                # file_content = file.stream.read()
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {
                    'name': name,
                    'datas_fname': file.filename,
                    'res_model': 'xlcrm.customer.contact',
                    # 'db_datas': base64.b64encode(file_content),
                    'mimetype': file.mimetype,
                    'create_user_id': env.uid,
                    'file_size': size,
                    'type': 'url',
                    'url': url
                }

                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                result_object = env['xlcrm.documents'].sudo().search_read([('id', '=', create_id)])[0]
                ret_data = {'document_id': result_object['id'],
                            'document_url': odoo.tools.config['serve_url'] + '/crm/image/' + str(result_object['id'])
                            }
                env.cr.commit()
                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': ret_data, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/addfilereview'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_review(self, success=False, message='', ret_data='', file='', **kw):
        if file:
            token = kw.pop('token')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                res_id = kw.get('res_id')
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {
                    'name': name,
                    'datas_fname': file.filename,
                    'res_model': 'xlcrm.project.review',
                    # 'db_datas': base64.b64encode(file_content),
                    'mimetype': file.mimetype,
                    'create_user_id': env.uid,
                    'file_size': size,
                    'res_id': res_id,
                    'type': 'url',
                    'url': url
                }
                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                env.cr.commit()
                result_object = env['xlcrm.documents'].sudo().search_read([('id', '=', create_id)])[0]
                ret_data = {'document_id': result_object['id'],
                            'document_name': result_object['datas_fname'],
                            'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                result_object['id'])
                            }

                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': ret_data, 'success': success, 'message': message}
        return json_response(rp)

        # img = ImageReader(output)

    @http.route(['/crm/file/<int:id>'], csrf=False, type='http', auth="public", cors='*')
    def crm_content_file(self, xmlid=None, model='xlcrm.documents', id=None, field='db_datas',
                         filename_field='datas_fname', unique=None, filename=None, mimetype=None, download=True,
                         width=0, height=0):

        status, headers, content = binary_content(xmlid=xmlid, model=model, id=id, field=field, unique=unique,
                                                  filename=filename, filename_field=filename_field, download=download,
                                                  mimetype=mimetype, default_mimetype='image/png')
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        height = int(height or 0)
        width = int(width or 0)
        if content and (width or height):
            # resize maximum 500*500
            if width > 500:
                width = 500
            if height > 500:
                height = 500
            content = odoo.tools.image_resize_image(base64_source=content, size=(width or None, height or None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        aa = response.data
        return response

    @http.route(['/crm/image/<int:id>'], csrf=False, type='http', auth="public")
    def crm_content_image(self, xmlid=None, model='xlcrm.documents', id=None, field='db_datas',
                          filename_field='datas_fname',
                          unique=None, filename=None, mimetype=None, download=None, width=0, height=0):
        status, headers, content = binary_content(xmlid=xmlid, model=model, id=id, field=field, unique=unique,
                                                  filename=filename, filename_field=filename_field, download=download,
                                                  mimetype=mimetype, default_mimetype='image/png')
        if status == 304:
            return werkzeug.wrappers.Response(status=304, headers=headers)
        elif status == 301:
            return werkzeug.utils.redirect(content, code=301)
        elif status != 200 and download:
            return request.not_found()

        height = int(height or 0)
        width = int(width or 0)
        if content and (width or height):
            # resize maximum 500*500
            if width > 500:
                width = 500
            if height > 500:
                height = 500
            content = odoo.tools.image_resize_image(base64_source=content, size=(width or None, height or None),
                                                    encoding='base64', filetype='PNG')
            # resize force png as filetype
            headers = self.force_contenttype(headers, contenttype='image/png')

        if content:
            image_base64 = base64.b64decode(content)
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    @http.route([
        '/api/v11/getProjectReviewDocuments',
        '/api/v11/getProjectReviewDocuments/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_review_documents(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 25
            domain = []
            if queryFilter and queryFilter.get("document_id"):
                domain.append(('id', 'in', queryFilter.get("document_id")))
                if queryFilter and queryFilter.get("res_model"):
                    domain.append(('res_model', '=', queryFilter.get("res_model")))
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

                domain = searchargs(domain)
                try:
                    count = request.env["xlcrm.documents"].sudo().search_count(domain)
                    result = request.env["xlcrm.documents"].sudo().search_read(domain, fields, offset * limit, limit,
                                                                               order)
                    model_fields = request.env["xlcrm.documents"].fields_get()
                    for r in result:
                        for f in r.keys():
                            if model_fields[f]['type'] == 'many2one':
                                if r[f]:
                                    r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                                else:
                                    r[f] = ''
                    if ids and result and len(ids) == 1:
                        result = result[0]
                    success = True
                except Exception as e:
                    result, success, message = '', False, str(e)
                finally:
                    env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectReviewDocumentsByResId',
        '/api/v11/getProjectReviewDocumentsByResId/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_review_documents_by_res_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 25
            domain = []
            if queryFilter and queryFilter.get("res_id"):
                domain.append(('res_id', '=', queryFilter.get("res_id")))
                if queryFilter and queryFilter.get("res_model"):
                    domain.append(('res_model', '=', queryFilter.get("res_model")))
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

                domain = searchargs(domain)
                try:
                    count = request.env["xlcrm.documents"].sudo().search_count(domain)
                    result = request.env["xlcrm.documents"].sudo().search_read(domain, fields, offset * limit, limit,
                                                                               order)
                    model_fields = request.env["xlcrm.documents"].fields_get()
                    for r in result:
                        for f in r.keys():
                            if model_fields[f]['type'] == 'many2one':
                                if r[f]:
                                    r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                                else:
                                    r[f] = ''
                    if ids and result and len(ids) == 1:
                        result = result[0]
                    success = True
                except Exception as e:
                    result, success, message = '', False, str(e)
                finally:
                    env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getDocumentsByCustomerId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_documents_by_customer_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 25
            domain = []
            if queryFilter and queryFilter.get("customer_id"):
                customer_id = queryFilter.get("customer_id")
                customer_object = env['xlcrm.customer'].sudo().search_read([('id', '=', customer_id)])[0]

                domain.append(('res_id', 'in', customer_object['review_ids']))
                domain.append(('res_model', '=', 'xlcrm.project.review'))
                try:
                    count = request.env["xlcrm.documents"].sudo().search_count(domain)
                    result_object = request.env["xlcrm.documents"].sudo().search_read(domain, fields, offset * limit,
                                                                                      limit,
                                                                                      order)
                    result = []
                    for doc in result_object:
                        result.append({'document_id': doc['id'],
                                       'document_name': doc['datas_fname'],
                                       'create_date': doc['create_date'],
                                       'create_user_id': doc['create_user_id'],
                                       'file_size': round(doc['file_size'] / 1024.0, 2),
                                       'create_user_name': doc['create_user_name'],
                                       'create_user_nick_name': doc['create_user_nick_name'],
                                       'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                           doc['id'])
                                       })
                    success = True
                except Exception as e:
                    result, success, message = '', False, str(e)
                finally:
                    env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getDocumentsByProjectId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_documents_by_project_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 25
            domain = []
            if queryFilter and queryFilter.get("project_id"):
                project_id = queryFilter.get("project_id")
                project_object = env['xlcrm.project'].sudo().search_read([('id', '=', project_id)])[0]
                res_ids = project_object['review_ids']
                res_ids.append(project_id)
                domain.append(('res_id', 'in', res_ids))
                domain.append(('res_model', 'in', ('xlcrm.project.review', 'xlcrm.project')))
                try:
                    count = request.env["xlcrm.documents"].sudo().search_count(domain)
                    result_object = request.env["xlcrm.documents"].sudo().search_read(domain, fields, offset * limit,
                                                                                      limit,
                                                                                      order)
                    result = []
                    for doc in result_object:
                        result.append({'document_id': doc['id'],
                                       'document_name': doc['datas_fname'],
                                       'create_date': doc['create_date'],
                                       'create_user_id': doc['create_user_id'],
                                       'file_size': round(doc['file_size'] / 1024.0, 2),
                                       'create_user_name': doc['create_user_name'],
                                       'create_user_nick_name': doc['create_user_nick_name'],
                                       'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                           doc['id'])
                                       })
                    success = True
                except Exception as e:
                    result, success, message = '', False, str(e)
                finally:
                    env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectCountByStage'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_count_by_stage_id(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            do_count, di_count, dw_count, mp_count, commit_count, can_do_commit_count, project_count, customer_count = '', '', '', '', '', '', '', ''

            review_ids = request.env["xlcrm.review.commit"].sudo().search_read(
                [('review_result_id', '=', 0), ('user_id', '=', records_ref.id)], ["review_id"])
            can_do_commit_count = 0
            for review_id_temp in review_ids:
                count_no_commit_child = request.env["xlcrm.review.commit"].sudo().search_count(
                    [('review_result_id', '=', 0),
                     ('review_id', '=', review_id_temp["review_id"][0]),
                     ('user_id', 'in', records_ref.child_ids_all.ids),
                     ('user_id', '!=', records_ref.id)])
                if count_no_commit_child == 0:
                    can_do_commit_count = can_do_commit_count + 1

            if (records_ref.group_id.id != 1):
                do_count = request.env["xlcrm.project"].sudo().search_count(
                    ['&', ('stage_id', '=', 1), '|',
                     ('project_attend_user_ids', 'ilike', records_ref.id), '|', ('create_user_id', '=', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                # do_count = request.env["xlcrm.project"].sudo().search_count(
                #     ['&', '&', ('record_status', '=', 1), ('stage_id', '=', 1), '|',
                #      ('project_attend_user_ids', 'ilike', records_ref.id), '|', ('create_user_id', '=', records_ref.id),
                #      ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                di_count = request.env["xlcrm.project"].sudo().search_count(
                    ['&', ('stage_id', '=', 2), '|',
                     ('project_attend_user_ids', 'ilike', records_ref.id), '|', ('create_user_id', '=', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                dw_count = request.env["xlcrm.project"].sudo().search_count(
                    ['&', '&', ('record_status', '=', 1), ('stage_id', '=', 3), '|',
                     ('project_attend_user_ids', 'ilike', records_ref.id), '|', ('create_user_id', '=', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                mp_count = request.env["xlcrm.project"].sudo().search_count(
                    ['&', ('stage_id', '=', 4), '|',
                     ('project_attend_user_ids', 'ilike', records_ref.id), '|', ('create_user_id', '=', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                commit_count = request.env["xlcrm.review.commit"].sudo().search_count(
                    ['&', ('review_result_id', '=', 0), '|', ('user_id', '=', records_ref.id),
                     ('user_id', 'in', records_ref.child_ids_all.ids)])
                # project_count = request.env["xlcrm.project"].sudo().search_count(
                #     ['|', ('create_user_id', '=', records_ref.id), '|', '&', ('record_status', '=', 1),
                #      ('project_attend_user_ids', 'ilike', records_ref.id), '&', ('record_status', '=', 1),
                #      ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                # customer_count = request.env["xlcrm.customer"].sudo().search_count(
                #     ['|', ('create_user_id', '=', records_ref.id), '&', ('record_status', '=', 1),
                #      ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                project_count = request.env["xlcrm.project"].sudo().search_count(
                    ['|', ('create_user_id', '=', records_ref.id), '|',
                     ('project_attend_user_ids', 'ilike', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
                customer_count = request.env["xlcrm.customer"].sudo().search_count(
                    ['|', ('create_user_id', '=', records_ref.id),
                     ('create_user_id', 'in', records_ref.child_ids_all.ids)])
            else:
                do_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 1)])
                di_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 2)])
                dw_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 3)])
                # mp_count = request.env["xlcrm.project"].sudo().search_count(
                #     [('record_status', '=', 1), ('stage_id', '=', 4)])
                mp_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 4)])
                commit_count = request.env["xlcrm.review.commit"].sudo().search_count([('review_result_id', '=', 0)])
                project_count = request.env["xlcrm.project"].sudo().search_count([])
                customer_count = request.env["xlcrm.customer"].sudo().search_count([])
            result = {
                "do_count": do_count,
                "di_count": di_count,
                "dw_count": dw_count,
                "mp_count": mp_count,
                "commit_count": commit_count,
                "can_do_commit_count": can_do_commit_count,
                "project_count": project_count,
                "customer_count": customer_count
            }
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectCountByCustomerId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_count_by_customer_id(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if kw.get("customer_id"):
            customer_id = int(kw.get("customer_id"))
            try:
                do_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 1), ('customer_id', '=', customer_id)])
                di_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 2), ('customer_id', '=', customer_id)])
                dw_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 3), ('customer_id', '=', customer_id)])
                mp_count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 4), ('customer_id', '=', customer_id)])
                result = {
                    "do_count": do_count,
                    "di_count": di_count,
                    "dw_count": dw_count,
                    "mp_count": mp_count
                }
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getRegionList'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_region_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            fields = eval(kw.get('fields', "[]"))
            order = kw.get('order', 'region_name asc')
            domain = [('is_delete', '=', '0')]
            count = request.env["xlcrm.region"].sudo().search_count(domain)
            result = request.env["xlcrm.region"].sudo().search_read(domain, fields, 0, 0, order)

            message = '操作成功！'
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomerOverview'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customer_overview(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("customer_id"):
            customer_id = int(kw.get("customer_id"))
            try:
                customer_projects, projects_count = '', ''
                customer_projects = request.env["xlcrm.project"].sudo().search_read([('customer_id', '=', customer_id)],
                                                                                    ['id', 'stage_id', 'name'], 0, 1,
                                                                                    order='id desc')

                DO_Count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 1), ('customer_id', '=', customer_id)])
                DI_Count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 2), ('customer_id', '=', customer_id)])
                DW_Count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 3), ('customer_id', '=', customer_id)])
                MP_Count = request.env["xlcrm.project"].sudo().search_count(
                    [('stage_id', '=', 4), ('customer_id', '=', customer_id)])
                projects_count = {
                    "do_count": DO_Count,
                    "di_count": DI_Count,
                    "dw_count": DW_Count,
                    "mp_count": MP_Count
                }

                operation_log = request.env["xlcrm.operation.log"].sudo().search_read(
                    [('res_model_related', '=', 'xlcrm.customer'), ('res_id_related', '=', customer_id)],
                    ['name', 'operation_date_time', 'content', 'res_id', 'res_model',
                     'operator_user_id', 'operator_user_name', 'operator_user_nick_name'], 0, 4, order='id desc')

                result = {
                    'projects_count': projects_count,
                    'customer_projects': customer_projects,
                    'operation_log': operation_log
                }
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectOverview'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_overview(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if kw.get("project_id"):
            project_id = int(kw.get("project_id"))
            try:
                project_overview_effort, projects_overview_count = '', ''
                project_object = env['xlcrm.project'].sudo().search_read([('id', '=', project_id)])[0]
                project_overview_effort = request.env["sdo.project.stage.change"].sudo().search_read(
                    [('project_id', '=', project_id)], ['id', 'stage_id', 'stage_name',
                                                        'operation_date_time', 'operation_user_name',
                                                        'duration_effort'], 0, 0, order='id desc')
                count_project_document = request.env["xlcrm.documents"].sudo().search_count(
                    [('res_id', 'in', project_object['review_ids']), ('res_model', '=', 'xlcrm.project.review')])
                count_project_reviews = request.env["xlcrm.project.review"].sudo().search_count(
                    [('project_id', '=', project_id)])
                count_project_operation_log = request.env["xlcrm.operation.log"].sudo().search_count(
                    [('res_model_related', '=', 'xlcrm.project'), ('res_id_related', '=', project_id)])
                count_project_product_line = request.env["sdo.product.line"].sudo().search_count(
                    [('project_id', '=', project_id)])
                projects_overview_count = {
                    "count_project_document": count_project_document,
                    "count_project_reviews": count_project_reviews,
                    "count_project_operation_log": count_project_operation_log,
                    "count_project_product_line": count_project_product_line
                }

                result = {
                    'project_overview_effort': project_overview_effort,
                    'projects_overview_count': projects_overview_count
                }
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectOperationLog'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_operation_log(self, **kw):
        success, message, result, count = True, '', '', 0
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("project_id"):
            project_id = int(kw.get("project_id"))
            try:
                operation_log = request.env["xlcrm.operation.log"].sudo().search_read(
                    [('res_model_related', '=', 'xlcrm.project'), ('res_id_related', '=', project_id)],
                    ['name', 'operation_date_time', 'content', 'res_id', 'res_model',
                     'operator_user_id', 'operator_user_name', 'operator_user_nick_name', 'user_group_name'], 0, 0,
                    order='id desc')

                result = operation_log
                count = len(operation_log)
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count}
        return json_response(rp)

    @http.route([
        '/api/v11/getStageChangeListByProjectId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_stage_change_list_by_project_id(self, **kw):
        success, message, result, count = True, '', '', 0
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        if kw.get("project_id"):
            project_id = int(kw.get("project_id"))
            try:
                stage_change_list = request.env["sdo.project.stage.change"].sudo().search_read(
                    [('project_id', '=', project_id)], ['id', 'stage_id', 'stage_name',
                                                        'operation_date_time', 'operation_user_name',
                                                        'duration_effort'], 0, 0, order='id desc')

                project_attend_user_ids = ''
                project_attend_users = []
                project_attend_user_ids = request.env['xlcrm.project'].sudo().search_read([('id', '=', project_id)],
                                                                                          ['project_attend_user_ids'],
                                                                                          order='id desc', limit=1)
                if project_attend_user_ids:
                    project_attend_users = request.env['xlcrm.users'].sudo().search_read(
                        [('id', 'in', project_attend_user_ids[0]['project_attend_user_ids'])],
                        ['id', 'nickname', 'username', 'group_id', 'user_group_name'], 0,
                        0, order='id desc')
                reviewers = request.env['xlcrm.project'].sudo().search_read([('id', '=', project_id)], ['reviewers'],
                                                                            order='id desc', limit=1)
                reviewers = ast.literal_eval(reviewers[0]['reviewers']) if reviewers[0]['reviewers'] else ''
                if reviewers:
                    for key, value in reviewers.items():
                        reviewers[key] = request.env['xlcrm.users'].sudo().search_read(
                            [('id', 'in', value)], ['id', 'nickname', 'username', 'group_id', 'user_group_name'], 0,
                            0, order='id desc')
                result = {
                    'stage_change_list': stage_change_list,
                    'project_attend_users': project_attend_users,
                    'reviewers': reviewers
                }
                message = "success"
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count}
        return json_response(rp)

    @http.route([
        '/api/v11/getProjectStatisticByMonth'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_project_statistic_by_month(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            query_by_auth, str_ids, str_attend_project_ids = '', '', ''
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if len(records_ref.child_ids.ids) > 0:
                    user_child_ids = env['xlcrm.users'].sudo().search([("id", 'in', records_ref.child_ids_all.ids)]).ids
                    for child_id in user_child_ids:
                        str_ids = str_ids + "," + str(child_id)
                    str_ids = "  or create_user_id in (" + str_ids[1:] + ")"
                if len(records_ref.user_attend_project_ids.ids) > 0:
                    attend_project_ids = env['xlcrm.project'].sudo().search(
                        [('record_status', '=', 1), ("id", 'in', records_ref.user_attend_project_ids.ids)]).ids
                    for attend_project_id in attend_project_ids:
                        str_attend_project_ids = str_attend_project_ids + "," + str(attend_project_id)
                    str_attend_project_ids = "  or id in (" + str_attend_project_ids[
                                                              1:] + ")" if str_attend_project_ids else ''
                query_by_auth = "where create_user_id=" + str(records_ref.id) + str_ids + str_attend_project_ids
            statistic_query = "select count(*) as nbr,min(EXTRACT(YEAR FROM f.create_date)||'-'|| EXTRACT(MONTH FROM f.create_date)) as month from xlcrm_project f " + query_by_auth + " group by EXTRACT(MONTH FROM f.create_date)"
            env.cr.execute(statistic_query)
            res = env.cr.fetchall()
            statistic_by_month = []
            for statistic_row in res:
                statistic_by_month.append({
                    '日期': statistic_row[1],
                    '项目数量': statistic_row[0]
                })
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': statistic_by_month}
        return json_response(rp)

    @http.route([
        '/api/v11/getStageStatisticByMonth'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_stage_statistic_by_month(self, **kw):
        success, message, result = True, '', ''
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            query_by_auth, str_ids, str_attend_project_ids = '', '', ''
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if len(records_ref.child_ids.ids) > 0:
                    user_child_ids = env['xlcrm.users'].sudo().search([("id", 'in', records_ref.child_ids_all.ids)]).ids
                    for child_id in user_child_ids:
                        str_ids = str_ids + "," + str(child_id)
                    str_ids = "  or create_user_id in (" + str_ids[1:] + ")"
                if len(records_ref.user_attend_project_ids.ids) > 0:
                    attend_project_ids = env['xlcrm.project'].sudo().search(
                        [('record_status', '=', 1), ("id", 'in', records_ref.user_attend_project_ids.ids)]).ids
                    for attend_project_id in attend_project_ids:
                        str_attend_project_ids = str_attend_project_ids + "," + str(attend_project_id)
                    str_attend_project_ids = "  or id in (" + str_attend_project_ids[
                                                              1:] + ")" if str_attend_project_ids else ''

                query_by_auth = "and (create_user_id=" + str(records_ref.id) + str_ids + str_attend_project_ids + ")"
            statistic_query = "select x.month, sum(x.nbr_do) as nbr_do_x, sum(x.nbr_di) as nbr_di_x, sum(x.nbr_dw) as nbr_dw_x, sum(x.nbr_mp) as nbr_mp_x from (" \
                              "(select count(*) as nbr_do, 0 as nbr_di, 0 as nbr_dw, 0 as nbr_mp, min(EXTRACT(YEAR FROM f.create_date)||'-'||EXTRACT(MONTH FROM f.create_date)) as month from xlcrm_project f where stage_id=1 " + query_by_auth + " group by EXTRACT(MONTH FROM f.create_date)) " \
                                                                                                                                                                                                                                                   "union (select 0 as nbr_do, count(*) as nbr_di, 0 as nbr_dw, 0 as nbr_mp, min(EXTRACT(YEAR FROM f.create_date)||'-'||EXTRACT(MONTH FROM f.create_date)) as month from xlcrm_project f where stage_id=2 " + query_by_auth + " group by EXTRACT(MONTH FROM f.create_date))" \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                              "union (select 0 as nbr_do, 0 as nbr_di, count(*) as nbr_dw, 0 as nbr_mp, min(EXTRACT(YEAR FROM f.create_date)||'-'||EXTRACT(MONTH FROM f.create_date)) as month from xlcrm_project f where stage_id=3 " + query_by_auth + " group by EXTRACT(MONTH FROM f.create_date))" \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         "union (select 0 as nbr_do, 0 as nbr_di, 0 as nbr_dw, count(*) as nbr_mp, min(EXTRACT(YEAR FROM f.create_date)||'-'||EXTRACT(MONTH FROM f.create_date)) as month from xlcrm_project f where stage_id=4 " + query_by_auth + " group by EXTRACT(MONTH FROM f.create_date))" \
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ") x group by x.month"
            env.cr.execute(statistic_query)
            res = env.cr.fetchall()
            statistic_by_month = []
            for statistic_row in res:
                statistic_by_month.append({
                    "日期": statistic_row[0],
                    "DO数量": statistic_row[1],
                    "DI数量": statistic_row[2],
                    "DW数量": statistic_row[3],
                    "MP数量": statistic_row[4]
                })
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': statistic_by_month}
        return json_response(rp)

    @http.route([
        '/api/v11/getHelpDocByName'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_help_doc_by_name(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        if kw.get("data"):
            queryFilter = kw.get("data")
            try:
                help_content = '暂无帮助信息！'
                if queryFilter == 'userList':
                    help_content = '这里的用户是指使用系统登录后并进行各类操作的用户账号！<br>用户账号可以有上下级关系，上级用户可以查询下级用户的数据！'
                result = {
                    'help_content': help_content
                }
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)

        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/addfileproject'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_project(self, success=False, message='', ret_data='', file='', **kw):
        if file:
            token = kw.pop('token')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                res_id = kw.get('res_id')
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {
                    'name': name,
                    'datas_fname': file.filename,
                    'res_model': 'xlcrm.project',
                    # 'db_datas': base64.b64encode(file_content),
                    'mimetype': file.mimetype,
                    'create_user_id': env.uid,
                    'file_size': size,
                    'res_id': res_id,
                    'type': 'url',
                    'url': url
                }
                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                env.cr.commit()
                result_object = env['xlcrm.documents'].sudo().search_read([('id', '=', create_id)])[0]
                ret_data = {'document_id': result_object['id'],
                            'document_name': result_object['datas_fname'],
                            'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                result_object['id'])
                            }

                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': ret_data, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/addfilevisit'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_visit(self, success=False, message='', res_data=[], file='', **kw):
        if file:
            token = kw.pop('token')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                res_id = kw.get('res_id')
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {
                    'name': name,
                    'datas_fname': file.filename,
                    'res_model': 'xlcrm.visit',
                    # 'db_datas': base64.b64encode(file_content),
                    'mimetype': file.mimetype,
                    'create_user_id': env.uid,
                    'file_size': size,
                    'res_id': res_id,
                    'type': 'url',
                    'url': url
                }

                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                env.cr.commit()
                result_object = request.env['xlcrm.documents'].sudo().search_read(
                    [('res_id', '=', res_id), ('res_model', '=', 'xlcrm.visit')])
                res_data = []
                for res in result_object:
                    res_tmp = {'id': res['id'],
                               'name': res['datas_fname'],
                               'url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                   res['id']),
                               'res_id': res['res_id']
                               }
                    res_data.append(res_tmp)

                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': res_data, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/update/documents/'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS', 'GET'])
    def update_documents(self, success=False, message='', ids=[], **kw):
        try:
            token = get_token(1).pop('token').pop('token')
            env = authenticate(token)
            document_res = env['xlcrm.documents'].sudo().search_read()
            from ..public import account_public
            for doc in document_res:
                if doc['db_datas']:
                    file_content = base64.b64decode(doc['db_datas'])
                    filename = doc['datas_fname']
                    success, url, name, message = account_public.saveFileUpdate(doc['create_user_id'][0], file_content,
                                                                                filename)
                    if not success:
                        rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                        return json_response(rp)
                    file_data = {
                        'name': name,
                        'type': 'url',
                        'url': url,
                        'db_datas': ''
                    }
                    env['xlcrm.documents'].browse(doc['id']).write(file_data)
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        rp = {'status': 200, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/update/account_products/'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS', 'GET'])
    def update_account_products(self, success=False, message='', ids=[], **kw):
        try:
            token = get_token(1).pop('token').pop('token')
            env = authenticate(token)
            res = env['xlcrm.account'].sudo().search_read([('id', '=', 451)])

            from ..public import account_public
            account = account_public.Stations('zhang')
            for re in res:
                list_res = []
                si_res = env['xlcrm.account.signers'].sudo().search_read(
                    [('review_id', '=', re['id']), ('station_no', '>=', 20), ('station_no', '<=', 30)])
                brandnames = si_res[0]['brandname']
                for index, bd in enumerate(brandnames.split(',')):
                    tmp = {}
                    tmp['brandname'] = bd
                    pmm = filter(lambda x: x['station_no'] == 30, si_res)
                    tmp['PMM'] = account.getusername(env, pmm[0][
                        'signers'].split(',')[index]) if pmm else ''
                    pm = filter(lambda x: x['station_no'] == 20, si_res)
                    tmp['PM'] = account.getusername(env, pm[0]['signers'].split(
                        ',')[index]) if pm else ''
                    pur = filter(lambda x: x['station_no'] == 25, si_res)
                    tmp['PUR'] = account.getusername(env, pur[0][
                        'signers'].split(',')[index]) if pur else ''
                    list_res.append(tmp)
                env['xlcrm.account'].sudo().browse(re['id']).write({'products': list_res})
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        rp = {'status': 200, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/del/documents'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def del_documents(self, success=False, message='', file='', **kw):
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            doucment_id = kw.get('id')
            res_doc = env['xlcrm.documents'].sudo().search_read([('id', '=', doucment_id)])
            if res_doc and res_doc[0]['type'] == 'url' and res_doc[0]['url']:
                address = os.getcwd() + '/ms_addons' + res_doc[0]['url']
                if os.path.exists(address):
                    os.remove(address)
            create_id = env['xlcrm.documents'].sudo().search([('id', '=', doucment_id)]).unlink()
            env.cr.commit()
            success = True
        except Exception as e:
            ret_data, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message}
        return json_response(rp)

    @http.route([
        '/api/v11/getDocumentsByAccountId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_documents_by_account_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'create_date_time desc')

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = 0
            limit = 25
            domain = []
            if queryFilter and queryFilter.get("account_id"):
                res_ids = queryFilter.get("account_id")
                domain.append(('res_id', '=', res_ids))
                domain.append(('res_model', '=', 'xlcrm.account'))
            if queryFilter and queryFilter.get("init_usernickname"):
                user_ids = env['xlcrm.users'].sudo().search_read(
                    [('nickname', 'ilike', queryFilter.get("init_usernickname"))])
                user_ids = map(lambda x: x['id'], user_ids)
                domain.append(('create_user_id', 'in', user_ids))
            try:
                # count = request.env["xlcrm.documents"].sudo().search_count(domain)
                result_object = request.env["xlcrm.documents"].sudo().search_read(domain, order=order)
                result = []
                for doc in result_object:
                    result.append({'document_id': doc['id'],
                                   'document_name': doc['datas_fname'],
                                   'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                       doc['id']),
                                   'init_user': doc['create_user_id'][0],
                                   'init_usernickname':
                                       env['xlcrm.users'].sudo().search_read([('id', '=', doc['create_user_id'][0])])[
                                           0]['nickname'],
                                   'init_time': doc['create_date_time'],
                                   'description': f"料号：{doc['description']}的合规许可证附件" if doc['description'] else '',
                                   })
                success = True
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/updateByAccountId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def update_by_account_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        try:
            id = ast.literal_eval(kw.get("id"))
            token = get_token(1)
            token = token.pop('token')
            env = authenticate(token['token'])
            # res = request.env['xlcrm.account'].sudo().search_read([('id','=',id)])
            env['xlcrm.account'].sudo().browse(id).write({'release_time_applyM': '90', 'release_time_apply': '月结'})
            env.cr.commit()
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getUserReload'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_user_reload(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = False, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            # count = request.env["xlcrm.documents"].sudo().search_count(domain)
            result_reload = request.env["xlcrm.reload"].sudo().search([('users', '=', env.uid), ('reload', '=', False)])
            result = True if result_reload else False
            if result:
                data = {}
                data['users'] = env.uid
                data['reload'] = True
                result_reload.write(data)
                env.cr.commit()
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'success': success, 'message': message, 'reload': result}
        return json_response(rp)

    @http.route([
        '/api/v11/updateUserReload',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def updateReload(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data['user'] = env.uid
            data['reload'] = True
            env['xlcrm.reload'].sudo().search([('user', '=', env.uid), ('reload', '=', False)]).write(data)
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message,
              'success': success}
        return json_response(rp)



    # @http.route([
    #     '/api/v11/updateFlowerItem/<string:model>',
    # ], auth='none', type='http', csrf=False, methods=['POST'])
    # def update_flower(self, model=None, success=True, message='', **kw):
    #     token = kw.pop('token')
    #     data = ast.literal_eval(list(kw.keys())[0].replace('true', '""')).get("data")
    #     env = authenticate(token)
    #     reviewers, products, account_attend_user_ids = [], [], []
    #     if not env:
    #         return no_token()
    #     if not check_sign(token, kw):
    #         return no_sign()
    #     try:
    #         from . import account_public
    #         from collections import Iterator
    #         review_id = data.pop('review_id')
    #         signers = filter(lambda x: x['signer'], data.values())
    #         sta = account_public.Stations('帐期额度申请单')
    #         res = env[model].sudo().search_read([('id', '=', review_id)])[0]
    #         reviewers = eval(res['reviewers'])
    #         products = eval(res['products'])
    #         for signer in signers:
    #             station_no = signer['station_no']
    #             stionsCode = sta.getStionsCode(station_no)
    #             sign = filter(lambda x: x['signer'], signer['signer']) if isinstance(signer['signer'], Iterator) else \
    #                 signer['signer']
    #             sign_ids = sign
    #             if station_no in (20, 25, 30):
    #                 for brand in sign:
    #                     brandname = brand['brandname']
    #                     for product in products:
    #                         if product['brandname'] == brandname:
    #                             product[stionsCode] = brand['signer']
    #                             if station_no == 20:
    #                                 res_ = env['xlcrm.user.ccfpminspector'].sudo().search_read(
    #                                     [('pm', 'ilike', brand['signer'])])
    #                                 if res_:
    #                                     product['PMins'] = res_[0]['inspector']
    #                                 else:
    #                                     product['PMins'] = ''
    #
    #                 sign = map(lambda x: x[stionsCode], products)
    #                 sign_ids = ','.join(map(lambda x: str(x), sta.getuserId(env, {stionsCode: sign})[stionsCode]))
    #                 if station_no == 20:
    #                     sign_ = map(lambda x: x['PMins'], products)
    #                     brandname_ = ','.join(map(lambda x: x['brandname'], products))
    #                     sign_ids_ = ','.join(map(lambda x: str(x), sta.getuserId(env, {'PMins': sign_})['PMins']))
    #                     res_s_ = env['xlcrm.account.signers'].sudo().search(
    #                         [('review_id', '=', review_id), ('station_no', '=', 21)])
    #                     if res_s_:
    #                         if sign_ids_:
    #                             res_s_.write({'signers': sign_ids_})
    #                         else:
    #                             res_s_.unlink()
    #                     else:
    #                         env['xlcrm.account.signers'].sudo().create({'review_id': review_id,
    #                                                                     'station_no': 21, 'station_desc': 'PM总监签核',
    #                                                                     'signers': sign_ids_,
    #                                                                     'brandname': brandname_})
    #                     reviewers['PMins'] = sign_
    #             res_s = env['xlcrm.account.signers'].sudo().search(
    #                 [('review_id', '=', review_id), ('station_no', '=', station_no)])
    #             res_s.write({'signers': sign_ids})
    #             reviewers[stionsCode] = sign
    #
    #         attend_res = env['xlcrm.account.signers'].sudo().search_read([('review_id', '=', review_id)])
    #         attend_res = filter(lambda x: x['signers'], attend_res)
    #         attend_ids = ','.join(map(lambda x: x['signers'], attend_res)).replace('[', '').replace(']', '')
    #         attend_ids = map(lambda x: int(x), attend_ids.split(','))
    #         env[model].sudo().browse(review_id).write(
    #             {'reviewers': reviewers, 'products': products, 'account_attend_user_ids': [[6, 0, attend_ids]]})
    #         env.cr.commit()
    #         message = '变更成功'
    #     except Exception as e:
    #         success, message, reviewers, products, account_attend_user_ids = False, str(e), [], [], []
    #     finally:
    #         env.cr.close()
    #     rp = {'status': 200, 'message': message,
    #           'success': success, 'reviewers': reviewers, 'products': products, 'account_attend_user_ids': attend_ids}
    #     return json_response(rp)

    @http.route([
        '/api/v11/setLoginLog',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def setloginlog(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0].replace('true', '""')).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            import datetime, dateutil, pytz
            tz = pytz.timezone('Asia/Shanghai')
            # aa = request.httprequest.environ
            # print '--------------',aa
            data['init_user'] = env.uid
            env['xlcrm.loginlog'].sudo().create(data)
            env.cr.commit()
            message = '记录成功'
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getLoginLogList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_loginlog_list12(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', "init_time desc")
        try:
            if kw.get("data"):
                json_data = kw.get("data").replace('null', 'None')
                queryFilter = ast.literal_eval(json_data)
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get("path"):
                    domain.append(('path', 'ilike', queryFilter.get("path")))
                if queryFilter and queryFilter.get("sdate"):
                    domain.append(('create_date', '>=', queryFilter.get("sdate")))
                if queryFilter and queryFilter.get("edate"):
                    domain.append(('create_date', '<=', queryFilter.get("edate")))
                if queryFilter and queryFilter.get("name"):
                    domain.append(('name', 'ilike', queryFilter.get("name")))
                if queryFilter and queryFilter.get("init_usernickname"):
                    domain.append(('init_usernickname', '=', queryFilter.get("init_usernickname")))
                if queryFilter and queryFilter.get("order_field"):
                    condition = queryFilter.get("order_field")
                    if condition == "init_usernickname":
                        condition = 'init_user'
                        order = condition + " " + queryFilter.get("order_type")
                    else:
                        order = condition + " " + queryFilter.get("order_type")
            count = request.env[model].sudo().search_count(domain)
            result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            if ids and result and len(ids) == 1:
                result = result[0]
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/getCustomers'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_customers(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            from ..public import connect_mssql
            sql = "select cCusCode,cCusName,cCusType,cCusAbbName,companycode from v_Customer_CCF"
            mysql = connect_mssql.Mssql('ErpCrmDB')
            res_sql = mysql.query(sql)
            for res in res_sql:
                tmp = {}
                tmp['cCusCode'] = res[0]
                tmp['cCusName'] = res[1]
                tmp['cCusType'] = self.translation(res[2])
                tmp['cCusAbbName'] = res[3]
                tmp['companycode'] = res[4]
                result.append(tmp)
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getProtocolCodes'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_protocol_codes(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            from ..public import connect_mssql
            sql = "select cCode,cName from v_Aa_agreement"
            mysql = connect_mssql.Mssql('ErpCrmDB')
            res_sql = mysql.query(sql)
            for res in res_sql:
                tmp = {}
                tmp['cCode'] = res[0]
                tmp['cName'] = res[1]
                result.append(tmp)
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getDepartment'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getDepartment(self, model=None, ids=None, **kw):
        success, message, dept_name,super_dept,spec_operator = True, '', '','',''
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            username = kw.get('username')
            from ..public import connect_mssql
            sql = "select 七级部门名称,六级部门名称,五级部门名称,四级部门名称,三级部门名称,二级部门名称," \
                  "一级部门名称,部门编号,人员编号 from v_hr_hi_person where 人员姓名='%s'" % username
            mysql = connect_mssql.Mssql('ErpCrmDB')
            res_sql = mysql.query(sql)
            if res_sql:
                res = res_sql[0]
                super_dept = res[7]
                spec_operator = res[8]
                for de in res:
                    if de:
                        dept_name = de
                        break
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'deptname': dept_name,'super_dept':super_dept,'spec_operator':spec_operator}
        return json_response(rp)

    @http.route([
        '/api/v11/getHisamount'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getHisamount(self, model=None, ids=None, **kw):
        success, message, result = True, '', []
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            ccusname = kw.get('ccusname')
            from ..public import connect_mssql
            sql = "select distinct companycodename,收款金额,价税合计,cexch_name from v_Custoemr_GetSales where ccusname='%s'" % ccusname
            mysql = connect_mssql.Mssql('ErpCrmDB')
            res_sql = mysql.query(sql)
            for res in res_sql:
                tmp = {}
                tmp['a_company'] = self.translation(res[0])
                tmp['payment_account'] = res[1] if res[1] else '0'
                tmp['salesment_account'] = res[2] if res[2] else '0'
                tmp['payment_currency'] = res[3] if res[3] else ''
                tmp['salesment_currency'] = res[3] if res[3] else ''
                result.append(tmp)
            message = "success"
        except Exception as e:
            result, success, message = [{}], False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'historys': result}
        return json_response(rp)


def binary_content(xmlid=None, model='xlcrm.documents', id=None, field='db_datas', unique=False, filename=None,
                   filename_field='datas_fname', download=False, mimetype=None,
                   default_mimetype='application/octet-stream', env=None):
    return request.registry['ir.http'].binary_content_crm(
        xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
        filename_field=filename_field,
        download=download, mimetype=mimetype, default_mimetype=default_mimetype, env=env)


def get_token(uid):
    serve = odoo.tools.config['serve_url']
    db = odoo.tools.config['db_name']
    # username = kw.pop('username')
    # password = kw.pop('password')
    user_obj = request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
    username = user_obj["username"]
    token = base64.urlsafe_b64encode(','.join([serve, db, username, str(uid), str(int(time.time()))]).encode()).replace(
        b'=', b'').decode()
    token = {
        'token': token,
        'group_id': user_obj['group_id'].id,
        'token_expires': int(time.time()),
        'refresh': base64.urlsafe_b64encode((token + ',' + str(int(time.time()) + 24 * 60 * 60 * 1)).encode()).decode(),
        'refresh_expires': int(time.time()) + 24 * 60 * 60 * 7
    }
    user = {
        'user_id': uid,
        'username': user_obj['username'],
        'group_id': user_obj['group_id'].id,
        'department_id': user_obj['department_id'].id,
        'nickname': user_obj['nickname'],
        'groupname': user_obj['user_group_name'],
        'departmentname': user_obj['department_name'],
        'head_pic': '',
        'status': user_obj['status']
    }
    result_data = {
        'token': token,
        'user': user
    }
    return result_data
