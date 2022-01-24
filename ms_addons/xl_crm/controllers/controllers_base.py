# -*- coding: utf-8 -*-
import base64, time, ast, werkzeug, json, odoo
from hashlib import md5
from odoo.http import request
# from odoo.modules.registry import RegistryManager
from odoo import api, registry


def action_auth(fun):
    def wrapper(*args, **kwargs):
        token = kwargs.pop('token')
        base = Base()
        env = base.authenticate(token)
        if not env:
            return base.no_token()
        if not base.check_sign(token, kwargs):
            return base.no_sign()
        return fun(*args, **kwargs)

    return wrapper


class Base:

    def authenticate(self, token):
        try:
            a = 4 - len(token) % 4
            if a != 0:
                token += '==' if a == 2 else '='
            SERVER, db, login, uid, ts = base64.urlsafe_b64decode(str(token).encode()).decode().split(',')
            if int(ts) + 60 * 60 * 24 * 7 * 10 < time.time():
                return False
            # registry = RegistryManager.get(db)
            cr = registry(db).cursor()
            env = api.Environment(cr, int(uid), {})

            request.uid = uid
        except Exception as e:
            return str(e)
        return env

    def no_token(self):
        rp = {'status': '401', 'result': '', 'success': False, 'message': 'invalid token!'}
        return self.json_response(rp)

    def no_sign(self):
        rp = {'status': '401', 'result': '', 'success': False, 'message': 'invalid sign!'}
        return self.json_response(rp)

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

    def json_response(self, rp):
        # rp_ = json.dumps(rp).replace('False','')
        headers = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"}
        return werkzeug.wrappers.Response(json.dumps(rp, ensure_ascii=False, cls=self.MyEncoder).replace("false", '""'),
                                          mimetype='application/json',
                                          headers=headers)

    def check_sign(self, token, kw):
        data = list(kw.keys())[0].replace('null', '""').replace('true', '""')
        sign = ast.literal_eval(data).get("sign")
        appkey = ast.literal_eval(data).get("appkey")
        timestamp = ast.literal_eval(data).get("timestamp")
        format = ast.literal_eval(data).get("format")
        check_req_str = odoo.tools.config["api_key"] + format + token + str(timestamp) + appkey + \
                        odoo.tools.config[
                            "api_key"]
        md5_obj = md5()
        md5_obj.update(check_req_str.encode(encoding='utf-8'))
        check_sign_str = md5_obj.hexdigest()
        return check_sign_str == sign

    def literal_eval(self, val):
        return ast.literal_eval(val)

    @staticmethod
    def translation(resource):
        import platform
        sysstr = platform.system()
        if sysstr == 'Windows':
            return resource.encode('latin-1').decode('gbk')
        return resource
