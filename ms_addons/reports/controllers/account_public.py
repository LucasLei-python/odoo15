# -*- coding: utf-8 -*-
import datetime, odoo, base64, time, json
from odoo.http import request


class Stations:
    def __init__(self, type):
        self.type = type

    def getStionsDesc(self, station):
        """
        签核站别描述数据
        :return: 签核站别描述
        """
        if self.type == '帐期额度申请单':
            tar_dict = {
                1: '申请者填单',
                5: 'Sales签核',
                10: '客服经理签核',
                15: '销售BU负责人签核',
                20: 'PM签核',
                25: '采购部签核',
                30: 'MKT VP签核',
                35: '财务部签核',
                40: '法务部签核',
                45: '风控部签核',
                50: '总经理签核',
                55: '董事长签核',
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
        if self.type == '帐期额度申请单':
            tar_dict = {
                1: 'Base',
                5: 'Sales',
                10: 'CS',
                15: 'SalesM',
                20: 'PM',
                25: 'PUR',
                30: 'PMM',
                35: 'FD',
                40: 'LG',
                45: 'RISK',
                50: 'Manage',
                55: 'ChairMan',

            }
            return tar_dict[station]

    def getStaions(self, desc):
        """

        :return:签核站别
        """
        if self.type == '帐期额度申请单':
            tar_dict = {
                'Base': 1,
                'Sales': 5,
                'CS': 10,
                'SalesM': 15,  # 销售BU负责人
                'PM': 20,
                'PUR': 25,
                'PMM': 30,  # PM 主管
                'FD': 35,
                'LG': 40,
                'RISK': 45,
                'Manage': 50,
                'ChairMan': 55
            }
            return tar_dict[desc]

    def getStaionsReject(self, desc):
        """

        :return:签核站别
        """
        if self.type == '帐期额度申请单':
            tar_dict = {
                'base': 1,
                'sales': 5,
                'customer': 10,
                'salesm': 15,  # 销售BU负责人
                'pm': 20,
                'pur': 25,
                'pmm': 30,  # PM 主管
                'fd': 35,
                'lg': 40,
                'risk': 45,
                'manage': 50,
                'chairman': 55
            }
            return tar_dict[desc]

    def getStatus(self, number):
        """

        :return:签核状态
        """
        if self.type == '帐期额度申请单':
            tar_dict = {
                0: "我的待签核",
                1: "草稿",
                2: "审核中",
                3: "已完成"
            }
            return tar_dict[number]

    def getModel(self, station_no, type=None):
        if self.type == '帐期额度申请单':
            tar_dict = {
                1: "base",
                5: "sales",
                10: "customer",
                15: "salesm",
                20: "pm",
                25: "pur",
                30: "pmm",
                35: "fd",
                40: "lg",
                45: "risk",
                50: "manage",
                55: "chairman",
            }
            if type == 'in':
                return tar_dict
            return "xlcrm.account." + tar_dict[station_no]

    def getModelByStaion(self, station_no):
        dict_tar = self.getModel(station_no, type='in')
        return dict(filter(lambda x: x[0] <= station_no, dict_tar.items()))

    def getnextstation(self, current_no):
        dict_next = {1: 5, 5: 10, 10: 15, 15: 20, 20: 25, 25: 30, 30: 35, 35: 40, 40: 45, 45: 50, 50: 55, 55: 99}
        return dict_next[current_no]

    def getuserId(self, env, users):
        userIds = {}
        for key, value in users.items():
            if isinstance(value, list):
                userIds[key] = []
                for va in value:
                    if va:
                        if not isinstance(va, int):
                            username = va.split('(')[1].split(')')[0] if '(' in va else va
                            va = env['xlcrm.users'].sudo().search_read(
                                ['|', ('username', 'ilike', username + '@'), ('username', '=', username)])[0][
                                'id'] if username else ''
                        userIds[key].append(va)
            else:
                if value:
                    if not isinstance(value, int):
                        username = value.split('(')[1].split(')')[0] if '(' in value else value
                        value = env['xlcrm.users'].sudo().search_read(
                            ['|', ('username', 'ilike', username + '@'), ('username', '=', username)])[0][
                            'id'] if username else ''
                    userIds[key] = value
            if (key == 'RISK1' or key == 'RISK2') and userIds.get(key):
                if userIds.get('RISK'):
                    if key == 'RISK1':
                        userIds['RISK'].insert(0, userIds.get(key))
                    else:
                        userIds['RISK'].append(userIds.get(key))
                else:
                    userIds['RISK'] = [userIds.get(key)]
                del userIds[key]
            if (key == 'FD1' or key == 'FD2') and userIds.get(key):
                if userIds.get('FD'):
                    if key == 'FD1':
                        userIds['FD'].insert(0, userIds[key])
                    else:
                        userIds['FD'].append(userIds[key])
                else:
                    userIds['FD'] = [userIds[key]]
                del userIds[key]

        userIds['Base'] = env.uid
        return userIds


class FormType:
    def __init__(self, id=1):
        self.id = id

    def getType(self):
        dict_type = {
            1: "帐期额度申请单",
            '1': "帐期额度申请单",
        }
        return dict_type[self.id]


def saveFile(uid, file):
    try:
        success, url, name, size, message = False, '', '', 0, ''
        import time, os
        dir = os.getcwd()
        timestrap = int(time.time() * 1000)
        name = str(uid) + '_' + str(timestrap) + '_' + file.filename
        saveurl = dir + '/ms_addons/xl_crm/static/files/' + name
        url = '/xl_crm/static/files/' + name
        # file_content = file.stream.read()
        file_content = file.read()
        with open(saveurl, 'wb') as f:
            f.write(file_content)
            return True, url, name, len(file_content), ''
    except Exception as e:
        return False, '', '', 0, str(e)


def saveFileUpdate(uid, file_content, filename):
    try:
        success, url, name, message = False, '', '', ''
        import time, os
        dir = os.getcwd()
        timestrap = int(time.time() * 1000)
        name = str(uid) + '_' + str(timestrap) + '_' + filename
        saveurl = dir + '/ms_addons/xl_crm/static/files/' + name
        url = '/xl_crm/static/files/' + name
        # file_content = file.stream.read()
        # file_content = file.read()
        with open(saveurl, 'wb') as f:
            f.write(file_content)
            return True, url, name, ''
    except Exception as e:
        return False, '', '', str(e)


def loginwechat(code):
    import requests
    import urllib
    import json

    # 向微信发请求验证
    params = {
        'code': code,
        'appid': 'wx513547ab52038ad1',
        'secret': '2dd9eb0540cf554d5682a4dcea36a267',
        'grant_type': 'authorization_code'
    }
    openid = ''
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.urlencode(params)
    res = requests.get(url=url)
    if res.status_code == 200:
        data = json.loads(res.content)
        openid = data.get('openid')
    return openid


def updateAccountReview(model, data, env):
    try:
        review_id = data.get('review_id')
        station_no = data.get("station_no")
        account = Stations('帐期额度申请单')
        record_status = data.get('record_status')
        if station_no == 1:
            review_id = data.get('id')
            data.pop('station_no')
            data.pop('signer')
            data['init_nickname'] = ''
            signers = data.get('reviewers', {})
            env[model].sudo().browse(review_id).write(data)
        reject_reason = data.get("backreason")
        station_model = account.getModel(station_no)
        domain = [('review_id', '=', review_id), ('init_user', '=', env.uid)]
        brandname = data.get('brandname')
        if station_no in (20, 25, 30):
            domain.append(('brandname', '=', brandname))
        result = env[station_model].sudo().search_read(domain=domain)
        if result:
            # data.pop('backreason')
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
        if record_status > 0:
            date_main = {}
            from . import send_email
            email_obj = send_email.Send_email()
            if record_status == 1:
                next_signer = ''
                next_station = 0
                signed_temp = 'N'
                signed_temp_ = 'N'
                if station_no in (20, 25, 30):
                    res = env['xlcrm.account.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)])
                    if res:
                        res = res[0]
                        # 判断pm,pur,pmm 是否有回签
                        backs = env['xlcrm.account.partial.sec'].sudo().search_read(
                            [('review_id', '=', review_id), ('station_no', '=', station_no)],
                            order='init_time desc', limit=1)
                        if backs:
                            if backs[0]['sign_over'] == 'Y':
                                signed_temp = 'Y'
                            else:
                                si_brand = backs[0]['sign_brand'] + brandname + ',' if backs[0][
                                    'sign_brand'] else '' + brandname + ','
                                env['xlcrm.account.partial.sec'].sudo().browse(backs[0]['id']).write(
                                    {'sign_brand': si_brand})
                                to_brand = backs[0]['to_brand']
                                sign_brand = backs[0]['sign_brand'] if backs[0]['sign_brand'] else ''
                                ne_signed = list(set(to_brand.split(',')) - set(sign_brand.split(',')))
                                if not ne_signed or ne_signed[0] == brandname:
                                    signed_temp = 'Y'
                        else:
                            signed = str(env.uid) if not res['signed'] else res['signed'] + ',' + str(env.uid)
                            brandnamed = brandname if not res['brandnamed'] else res['brandnamed'] + ',' + brandname
                            signed_temp_ = 'Y' if sorted(set(signed.split(','))) == sorted(
                                set(res['signers'].split(','))) and sorted(set(brandnamed.split(','))) == sorted(
                                set(res['brandname'].split(','))) else 'N'
                            env['xlcrm.account.signers'].sudo().browse(res['id']).write(
                                {'signed': signed, 'brandnamed': brandnamed})

                while not next_signer:
                    # 首先判断下一站是否有签核人
                    next_station = account.getnextstation(station_no)
                    next_signer = env['xlcrm.account.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], ['signers'])
                    if next_signer:
                        next_signer = next_signer[0]['signers']
                    else:
                        next_signer = ''

                    # 否是多人签核
                    signer_many = env['xlcrm.account.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)])
                    if signer_many:
                        signer_many = signer_many[0]
                        signers = signer_many['signers'].split(',')
                        signers_index = 0
                        if len(signers) > 1:
                            if station_no in (35, 45):  # 财务，风控多人签核有先后顺序
                                for index, value in enumerate(signers):
                                    if value == str(env.uid):
                                        signers_index = index
                                        break
                                if signers_index < len(signers) - 1:  # 多人签且当前签核人不是多人签中的最后一个时，下一站站别信息不变
                                    next_station = station_no
                                    next_signer = signers[signers_index + 1]
                            else:
                                if signer_many['sign_over'] == 'N' and signed_temp_ == 'N':
                                    next_station = station_no
                                    break
                                    # need_set =  set(signers) - set(signer_many['signed'].split(','))
                                    # next_signer =
                    # 判断是否回签
                    sign_back = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    if sign_back and sign_back[0]['sign_over'] == 'N':
                        if next_station == station_no:  # 说明是多人签核且还有人没有签完
                            next_station = 28
                            next_signer = ''
                            break
                        else:
                            if station_no in (20, 25, 30):
                                if signed_temp == 'Y':
                                    sign_station = sign_back[0]['sign_station'] + str(station_no) + ',' if \
                                        sign_back[0][
                                            'sign_station'] else '' + str(station_no) + ','
                                    env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
                                        {'sign_station': sign_station})
                                else:
                                    sign_station = sign_back[0]['sign_station'] if \
                                        sign_back[0]['sign_station'] else ''
                            else:
                                sign_station = sign_back[0]['sign_station'] + str(station_no) + ',' if sign_back[0][
                                    'sign_station'] else '' + str(station_no) + ','
                                env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
                                    {'sign_station': sign_station})

                            ne_station = list(
                                set(sign_back[0]['to_station'].split(',')) - set(sign_station.split(',')))
                            if not ne_station or ne_station == [str(station_no)]:
                                if ne_station in (20, 25, 30):
                                    if signed_temp == 'Y':
                                        next_station = sign_back[0]['from_station']
                                        next_signer = env['xlcrm.account.signers'].sudo().search_read(
                                            ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)],
                                            ['signers'])
                                        if next_signer:
                                            next_signer = next_signer[0]['signers']
                                        else:
                                            next_signer = ''
                                else:
                                    next_station = sign_back[0]['from_station']
                                    next_signer = env['xlcrm.account.signers'].sudo().search_read(
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
                # date_main['signer'] = next_signer
                date_main['station_desc'] = account.getStionsDesc(next_station)
            # if record_status == 2:  # 驳回
            #     # 写入驳回记录表
            #     if reject_reason:
            #         env['xlcrm.account.reject'].sudo().create({'review_id': review_id,
            #                                                    'station_no': station_no,
            #                                                    'reason': reject_reason,
            #                                                    'init_user': env.uid})
            #     create_uid = env["xlcrm.account"].sudo().search_read([("id", "=", review_id)])
            #     if create_uid:
            #         create_uid = create_uid[0]
            #     date_main['signer'] = create_uid["init_user"][0]
            #     station_no = 1
            #     station_desc = account.getStionsDesc(station_no)
            #     date_main['station_no'] = station_no
            #     date_main['station_desc'] = station_desc
            #     date_main['status_id'] = 1
            #     date_main['record_status'] = 0
            #     date_main['isback'] = 1

            if date_main['signer']:
                uid = date_main['signer']
                sbuject = "帐期额度申请单待审核通知"
                to = ["leihui@szsunray.com"]
                to_wechart = '雷辉，leihui@szsunray.com'
                cc = []
                if odoo.tools.config["enviroment"] == 'PRODUCT':
                    user = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
                    to = [user["email"]]
                    to_wechart = user['nickname'] + ',' + user["email"]
                token = get_token(env, uid)
                href = request.httprequest.environ[
                           "HTTP_ORIGIN"] + '/#/public/account-list/' + str(
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
                                            注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>,用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                                            </div>
                                        </body>
                                        </html>
                                        """
                msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content)
                if msg["code"] == 500:  # 邮件发送失败
                    success_email = False
                # 发微信通知
            account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            url = 'http://crm.szsunray.com/public/account-list/%s/%s' % (str(review_id), json.dumps(token))
            send_wechart = sendWechat('账期额度申请单待审核通知', to_wechart, url,
                                                     '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
                                                     account_result[0]["init_usernickname"],
                                                     account_result[0]["init_time"])
            date_main["update_user"] = env.uid
            date_main["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            result = env['xlcrm.account'].sudo().browse(review_id).write(date_main)
        if send_email and send_wechart:
            env.cr.commit()
            send_wechart.commit()
            return True
        else:
            return False
    except Exception as e:
        return False
    finally:
        send_wechart.close()


def get_token(env, uid):
    serve = odoo.tools.config['serve_url']
    db = odoo.tools.config['db_user']
    # username = kw.pop('username')
    # password = kw.pop('password')
    user_obj = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
    username = user_obj["username"]
    token = base64.urlsafe_b64encode(','.join([serve, db, username, str(uid), str(int(time.time()))])).replace(
        '=', '')
    token = {
        'token': token,
        'group_id': user_obj['group_id'].id,
        'token_expires': int(time.time()),
        'refresh': base64.urlsafe_b64encode(token + ',' + str(int(time.time()) + 24 * 60 * 60 * 1)),
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


def getaccountlistold(r, env, ap):
    for f in r.keys():
        if f == "station_no":
            r["station_desc"] = ap.getStionsDesc(r[f])
    r["review_type"] = FormType(r["review_type"]).getType()
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


def getaccountlistnew(r, env, ap):
    import ast
    for f in r.keys():
        if f == "station_no":
            r["station_desc"] = ap.getStionsDesc(r[f])
    r["review_type"] = FormType(r["review_type"]).getType()
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
                signer_temp = ''
                sig = env['xlcrm.account.signers'].sudo().search_read(
                    [('review_id', '=', r['id']), ('station_no', '=', sta)])
                if sig:
                    sta_desc = ap.getStionsDesc(int(sta))
                    if int(sta) in (20, 25, 30):
                        sec = env['xlcrm.account.partial.sec'].sudo().search_read(
                            [('review_id', '=', r['id']), ('station_no', '=', sta),
                             ('p_id', '=', _station[0]['id'])])
                        if sec:
                            to_brands = sec[0]['to_brand'].split(',')
                            sign_brands = sec[0]['sign_brand'].split(',') if sec[0]['sign_brand'] else []
                            brands = filter(lambda x: x, list(set(to_brands) - set(sign_brands)))
                            products = ast.literal_eval(r['products']) if r['products'] else {}
                            sta_code = ap.getStionsCode(int(sta))
                            for br in brands:
                                sign_br = filter(lambda x: x['brandname'] == br, products)[0] if br else {}
                                sign_username = sign_br.get(sta_code)
                                if sign_username:
                                    sign_username = sign_username.split('(')[1].split(')')[0]
                                    signer_user = env['xlcrm.users'].sudo().search_read(
                                        [('username', 'like', sign_username)])[0]
                                    if signer:
                                        signer = signer + ',' + str(signer_user['id'])
                                    else:
                                        signer = str(signer_user['id'])
                                    signer_temp = signer_temp + ',' + str(
                                        signer_user['id']) if signer_temp else str(signer_user['id'])
                    else:
                        if signer:
                            signer = signer + ',' + sig[0]['signers']
                        else:
                            signer = sig[0]['signers']
                        signer_temp = signer_temp + ',' + sig[0]['signers'] if signer_temp else sig[0][
                            'signers']

                    if signer_nickname:
                        signer_nickname = signer_nickname + ';' + sta_desc + '(' + ','.join(
                            map(lambda x: x['nickname'],
                                env['xlcrm.users'].sudo().search_read(
                                    [('id', 'in', signer_temp.split(','))]))) + ')'
                    else:
                        signer_nickname = sta_desc + '(' + ','.join(
                            map(lambda x: x['nickname'],
                                env[
                                    'xlcrm.users'].sudo().search_read(
                                    [('id', 'in',
                                      signer_temp.split(','))]))) + ')'
            if str(env.uid) in signer.split(','):
                r['status_id'] = 0
            r['signer'] = [signer]
            r['signer_nickname'] = signer_nickname
    # pm,采购,mktvp 按品牌签核
    if r['station_no'] in (20, 25, 30):
        signers = env['xlcrm.account.signers'].sudo().search_read([('review_id', '=', r['id']),
                                                                   ('station_no', '=', r['station_no'])])
        if signers:
            signed = map(lambda x: int(x), signers[0]['signed'].split(',')) if signers[0]['signed'] else []
            signer = map(lambda x: int(x), signers[0]['signers'].split(',')) if signers[0][
                'signers'] else []
            r['signer'] = list(set(signer) - set(signed))
            r['signer_nickname'] = ','.join(
                map(lambda x: x['nickname'],
                    env['xlcrm.users'].sudo().search_read(
                        [('id', 'in', r['signer'])])))
            if env.uid in r['signer']:
                r['status_id'] = 0
            r['signer'] = [','.join(map(lambda x: str(x), r['signer']))]

def sendWechat(subject,to_wechart,url,content,init_user,init_time):
    from . import connect_mssql
    wechart = connect_mssql.Mssql('wechart')
    send_wechart = wechart.in_up_de(
        "insert into dbo.BusinessTemplateMsg(templateType,userId,url,first,key1,key2)values('"+subject+"','" + to_wechart + "','" + url + "', '"+content+"', '" +init_user + "', '" + init_time + "')")

    return wechart if send_wechart else send_wechart