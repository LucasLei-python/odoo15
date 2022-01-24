# -*- coding: utf-8 -*-
import ast, odoo, base64, json, werkzeug, time, re, csv, _ast
from odoo import api,registry
from hashlib import md5
from odoo.http import request
from datetime import date, datetime, timedelta
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


def check_sign(token, kw):    
    sign = ast.literal_eval(list(kw.keys())[0].replace('null', '""')).get("sign")
    appkey = ast.literal_eval(list(kw.keys())[0].replace('null', '""')).get("appkey")
    timestamp = ast.literal_eval(list(kw.keys())[0].replace('null', '""')).get("timestamp")
    format = ast.literal_eval(list(kw.keys())[0].replace('null', '""')).get("format")
    check_req_str = odoo.tools.config["api_key"] + format + token + str(timestamp) + appkey + odoo.tools.config[
        "api_key"]
    md5_obj = md5()
    md5_obj.update(check_req_str.encode(encoding='utf-8'))
    check_sign_str = md5_obj.hexdigest()
    return check_sign_str == sign

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


def get_token(env, uid):
    serve = odoo.tools.config['serve_url']
    db = odoo.tools.config['db_user']
    # username = kw.pop('username')
    # password = kw.pop('password')
    user_obj = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
    username = user_obj["username"]
    token = base64.urlsafe_b64encode((','.join([serve, db, username, str(uid), str(int(time.time()))])).encode()).replace(
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


class Stations:
    def __init__(self, type):
        self.type = type

    def getStionsDesc(self, station):
        """
        签核站别描述数据
        :return: 签核站别描述
        """
        if self.type == 'PO申请单':
            tar_dict = {
                1: '申请者填单',
                5: 'PM备货填写',
                10: 'MKT VP意见',
                15: 'COO审批意见',
                20: 'CEO审批意见',
                98: '作废',
                99: '签核完成',
                28: '回签'
            }
            return tar_dict[station]

    def getStionsCode(self, station):
        """
        签核站别描述数据
        :return: 站别代码
        """
        if self.type == 'PO申请单':
            tar_dict = {
                1: 'base',
                5: 'pm',
                10: 'pmm',
                15: 'coo',
                20: 'ceo',
            }
            return tar_dict[station]

    def getStaions(self, desc):
        """

        :return:签核站别
        """
        if self.type == 'PO申请单':
            tar_dict = {
                'base': 1,
                'pm': 5,
                'pmm': 10,
                'coo': 15,
                'ceo': 20,
            }
            return tar_dict[desc]

    def getStaionsReject(self, desc):
        """

        :return:签核站别
        """
        if self.type == 'PO申请单':
            tar_dict = {
                'base': 1,
                'pm': 5,
                'pmm': 10,
                'coo': 15,  # 销售BU负责人
                'ceo': 20,
            }
            return tar_dict[desc]

    def getStatus(self, number):
        """

        :return:签核状态
        """
        if self.type == 'PO申请单':
            tar_dict = {
                0: "我的待签核",
                1: "草稿",
                2: "审核中",
                3: "已完成"
            }
            return tar_dict[number]

    def getModel(self, station_no, type=None):
        if self.type == 'PO申请单':
            tar_dict = {
                1: "base",
                5: "pm",
                10: "pmm",
                15: "coo",
                20: "ceo",
            }
            if type == 'in':
                return tar_dict
            return "report.po" + tar_dict[station_no]

    def getModelByStaion(self, station_no):
        dict_tar = self.getModel(station_no, type='in')
        return dict(filter(lambda x: x[0] <= station_no, dict_tar.items()))

    def getnextstation(self, current_no):
        dict_next = {1: 5, 5: 10, 10: 15, 15: 20,
                     20: 99}
        return dict_next[current_no]

    def getusername(self, env, userid):
        res_user = env['xlcrm.users'].sudo().search_read([('id', '=', int(userid))])[0]
        username = res_user['nickname'] + '(' + res_user['username'].split('@')[0] + ')'
        return username


def updatePOReview(model, data, env):
    try:
        review_id = int(data.get('review_id'))
        station_no = data.get("si_station")
        account = Stations('PO申请单')
        record_status = data.get('record_status')
        if station_no == 1:
            review_id = data.get('id')
            data.pop('si_station')
            data.pop('signer')
            data['init_nickname'] = ''
            signers = data.get('reviewers', {})
            env[model].sudo().browse(review_id).write(data)
        reject_reason = data.get("backreason")
        station_model = account.getModel(station_no)
        domain = [('review_id', '=', review_id)]
        result = env[station_model].sudo().search_read(domain=domain)
        tmp = data[account.getModel(station_no, 'in')[station_no]]
        if result:
            tmp.pop('review_id')
            tmp.pop('init_user')
            tmp["update_user"] = env.uid
            tmp["update_time"] = datetime.now() + timedelta(hours=8)
            env[station_model].sudo().browse(result[0]['id']).write(tmp)
        else:
            tmp['review_id'] = review_id
            tmp["init_user"] = env.uid
            tmp["init_time"] = datetime.now() + timedelta(hours=8)
            tmp["update_user"] = env.uid
            tmp["update_time"] = datetime.now() + timedelta(hours=8)
            result = env[station_model].sudo().create(tmp)
        success_email = True
        send_wechart = True
        if record_status > 0:
            date_main = {}
            from . import send_email
            email_obj = send_email.Send_email()
            next_signer = ''
            if record_status == 1:
                next_station = 0
                signed_temp = 'N'
                signed_temp_ = 'N'
                riskM_email = ''
                while not next_signer:
                    # 首先判断下一站是否有签核人
                    next_station = account.getnextstation(station_no)
                    next_signer = env['report.po.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], ['signers'])
                    if next_signer:
                        next_signer = eval(next_signer[0]['signers'])[0] if '[' in next_signer[0]['signers'] else \
                            next_signer[0]['signers']
                    else:
                        next_signer = ''
                    # 判断是否回签
                    sign_back = env['reports.po.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    if sign_back and sign_back[0]['sign_over'] == 'N':
                        if next_station == station_no:  # 说明是多人签核且还有人没有签完
                            next_station = 28
                            next_signer = ''
                            break
                        else:
                            sign_station = sign_back[0]['sign_station'] + str(station_no) + ',' if sign_back[0][
                                'sign_station'] else '' + str(station_no) + ','
                            env['reports.po.partial'].sudo().browse(sign_back[0]['id']).write(
                                {'sign_station': sign_station})

                            ne_station = list(
                                set(sign_back[0]['to_station'].split(',')) - set(sign_station.split(',')))
                            if not ne_station or ne_station == [str(station_no)]:
                                next_station = sign_back[0]['from_station']
                                next_signer = env['report.po.signers'].sudo().search_read(
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
                next_signer = next_signer if isinstance(next_signer, str) else str(next_signer)
                next_signer = eval(next_signer)[0] if '[' in next_signer else next_signer.split(',')[0]
                next_signer = next_signer[0] if isinstance(next_signer, list) else next_signer
                next_signer = next_signer if isinstance(next_signer, str) else str(next_signer)
                date_main['signer'] = next_signer
                # date_main['signer'] = next_signer
                date_main['station_desc'] = account.getStionsDesc(next_station)
                if date_main['signer']:
                    uid = next_signer.split(',')
                    sbuject = "采购PO申请单待审核通知"
                    to = ["leihui@szsunray.com"]
                    to_wechart = '雷辉，lucas'
                    cc = []
                    for ui in uid:
                        user = env['xlcrm.users'].sudo().search([('id', '=', ui)], limit=1)
                        if odoo.tools.config["enviroment"] == 'PRODUCT':
                            to = [user["email"]]
                            to_wechart = user['nickname'] + ',' + user["username"]
                        token = get_token(env, ui)
                        href = request.httprequest.environ[
                                   "HTTP_ORIGIN"] + '/#/public/reports-U8-PO-list/' + str(
                            review_id) + "/" + json.dumps(token)
                        content = """
                                                <html lang="en">            
                                                <body>
                                                    <div>
                                                        """ + user['nickname'] + """您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核采购PO申请单，请点击
                                                        <a href='""" + href + """' ><font color="red">链接</font></a>进入系统审核
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
                        # # 发微信通知
                        # account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
                        # user = base64.b64encode(to_wechart)
                        # url = 'http://crm.szsunray.com:9030/public/ccf-list/%s/%s' % (str(review_id), user)
                        # send_wechart = sendWechat('账期额度申请单待审核通知', to_wechart, url,
                        #                           '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
                        #                           account_result[0]["init_usernickname"],
                        #                           account_result[0]["init_time"])
                date_main["update_user"] = env.uid
                date_main["update_time"] = datetime.now() + timedelta(hours=8)
                result = env['report.pobase'].sudo().browse(review_id).write(date_main)
            if success_email:
                env.cr.commit()
                return True
            else:
                return False
    except Exception as e:
        return False


def getSigner(env, result):
    ap = Stations('PO申请单')
    for r in result:
        r["station_desc"] = ap.getStionsDesc(r["station_no"])
        if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
            r["status_id"] = 0
        if r['station_no'] and r['station_no'] == 28:
            _station = env['reports.po.partial'].sudo().search_read(
                [('review_id', '=', r['id'])], order='init_time desc', limit=1)
            if _station[0]['sign_over'] == 'N':
                to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                    'sign_station'] else []
                signer_nickname = ''
                signer = ''
                ne_station = list(set(to_station) - set(sign_station))
                for sta in ne_station:
                    sig = env['report.po.signers'].sudo().search_read(
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
                r['signer'] = signer.split(',')
                r['signer_nickname'] = signer_nickname


def changeCount(env, result, type='reduce'):
    try:
        status = {'success': True, 'message': ''}
        others = eval(result['others'])
        from . import connect_mssql
        mysql = connect_mssql.Mssql('stock')
        query = []
        for oth in others:
            versions = oth['versions']
            cinvcode = oth['cinvcode']
            iquantity = oth['iquantity']
            # 先查询是否还有余量
            res = mysql.query(
                "select confirm from PurchaseDetail where versions='%s' and cinvCode='%s'" % (versions, cinvcode))
            if type == 'reduce':
                change = int(res[0][0]) - int(iquantity)
            else:
                change = int(res[0][0]) + int(iquantity)
            if change < 0:
                status['success'] = False
                status['message'] = '存货编码%s,版本号%s的余量%d不足以申请%d' % (cinvcode, versions, int(res[0][0]), int(iquantity))
                return status
            query.append((change, versions, cinvcode))
            chg_res = env['report.pochangelog'].sudo().create({'review_id': result['id'], 'init_user': env.uid,
                                                               'cinvcode': cinvcode, 'versions': versions,
                                                               'old': int(res[0][0]), 'new': change})
        res_sql = mysql.batch_in_up_de(
            [["update PurchaseDetail set confirm=%d where versions=%s and cinvCode=%s", query]])
        if res_sql:
            mysql.commit()
            env.cr.commit()
        else:
            status['success'] = False
            status['message'] = '数量更新失败'
    except Exception as e:
        status['success'] = False
        status['message'] = str(e)
    finally:
        return status
