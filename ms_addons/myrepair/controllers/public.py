# -*- coding: utf-8 -*-
from odoo import registry
import ast, odoo, base64, json, werkzeug, time, re, csv, _ast
from hashlib import md5
from odoo import api
from odoo.http import request
from datetime import date, datetime
from decimal import Decimal

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


def check_sign(token, kws):
    sign = ast.literal_eval(kws).get("sign")
    appkey = ast.literal_eval(kws).get("appkey")
    timestamp = ast.literal_eval(kws).get("timestamp")
    format = ast.literal_eval(kws).get("format")
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


DOMAIN_OPERATORS = frozenset('!|&')
_term_re = re.compile(
    '([\w._]+)\s*'  '(=(?:like|ilike|\?)|[<>]=?|!?=(?!=)'
    '|(?<= )(?:like|ilike|in|not like|not ilike|not in|child_of))'  '\s*(.*)')


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def json_response(rp):
    headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}
    return werkzeug.wrappers.Response(json.dumps(rp, ensure_ascii=False, cls=MyEncoder).replace("false", '""'), mimetype='application/json',
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
        env = api.Environment(cr, int(uid), {})
        request.uid = uid
    except Exception as e:
        return str(e)
    return env


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


class Stations:
    def __init__(self, type):
        self.type = type

    def getStionsDesc(self, station):
        """
        签核站别描述数据
        :return: 签核站别描述
        """
        if self.type == '维修申请单':
            tar_dict = {
                1: '申请者填单',
                5: '检测工程师填单',
                10: '维修客服确认',
                98: '作废',
                99: '签核完成'
            }
            return tar_dict.get(station)

    def getStaions(self, desc):
        """

        :return:签核站别
        """
        if self.type == '维修申请单':
            tar_dict = {
                'Test': 5,
                'TCS': 10,
            }
            return tar_dict[desc]

    def getStatus(self, number):
        """

        :return:签核状态
        """
        if self.type == '维修申请单':
            tar_dict = {
                0: "我的待签核",
                1: "草稿",
                2: "审核中",
                3: "已完成"
            }
            return tar_dict[number]

    def getModel(self, station_no, type=None):
        if self.type == '维修申请单':
            tar_dict = {
                5: "testing",
                10: "cs",
            }
            if type == 'in':
                return tar_dict
            return "repair." + tar_dict[station_no]

    def getModelByStaion(self, station_no):
        dict_tar = self.getModel(station_no, type='in')
        return dict(filter(lambda x: x[0] <= station_no, dict_tar.items()))

    def getnextstation(self, current_no):
        dict_next = {1: 5, 5: 10, 10: 99}
        return dict_next[current_no]

    def write_repair_products(self, env, data, ts_id):
        env['repair.products'].sudo().search([('ts_id','=',ts_id)]).unlink()
        for item in data:
            env['repair.products'].sudo().create(dict(item, **{'ts_id': ts_id}))
