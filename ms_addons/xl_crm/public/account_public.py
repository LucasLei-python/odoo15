# -*- coding: utf-8 -*-
import datetime, odoo, base64, time, json
from odoo.http import request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header


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
                16: 'Sales VP签核',
                20: 'PM签核',
                21: 'PM总监签核',
                25: '采购部签核',
                30: 'MKT VP签核',
                35: '财务助理签核',
                36: '财务主管签核',
                40: '法务部签核',
                45: '风控部签核',
                46: 'CS VP签核',
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
                16: 'SalesVP',
                20: 'PM',
                21: 'PMins',
                25: 'PUR',
                30: 'PMM',
                35: 'FD',
                36: 'FDM',
                40: 'LG',
                45: 'RISK',
                46: 'CSVP',
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
                'SalesVP': 16,
                'PM': 20,
                'PMins': 21,
                'PUR': 25,
                'PMM': 30,  # PM 主管
                'FD': 35,
                'FDM': 36,
                'LG': 40,
                'RISK': 45,
                'CSVP': 46,
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
                'salesvp': 16,
                'pm': 20,
                'pmins': 21,
                'pur': 25,
                'pmm': 30,  # PM 主管
                'fd': 35,
                'fdm': 36,
                'lg': 40,
                'risk': 45,
                'csvp': 46,
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
                16: "salesvp",
                20: "pm",
                21: "pmins",
                25: "pur",
                30: "pmm",
                35: "fd",
                36: "fd",
                40: "lg",
                45: "risk",
                46: "csvp",
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
        dict_next = {1: 5, 5: 10, 10: 15,15:16, 16: 20, 20: 21, 21: 25, 25: 30, 30: 35, 35: 36, 36: 40, 40: 45, 45: 46,
                     46: 50,
                     50: 55,
                     55: 99}
        return dict_next[current_no]

    def getusername(self, env, userid):
        res_user = env['xlcrm.users'].sudo().search([('id', '=', int(userid))])[0]
        username = res_user['nickname'] + '(' + res_user['username'].split('@')[0] + ')'
        return username

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


def sendVisitEmail(result_object, env, res_id):
    import os
    user = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])[0]
    result_file = request.env['xlcrm.documents'].sudo().search_read(
        [('res_id', '=', res_id), ('res_model', '=', 'xlcrm.visit')])
    files = "<div>"
    msgImage = []
    for res in result_file:
        cid = str(res['id'])
        files += "<img src='cid:%s'>" % cid
        saveurl = os.getcwd() + '/ms_addons' + res['url']
        with open(saveurl, 'rb') as f:
            temp = MIMEImage(f.read())
            temp.add_header("Conteng-ID", cid)
            msgImage.append(temp)
    files += "</div>"
    from_addr = user["email"]
    qqCode = user["email_password"]
    # from_addr = "crm@szsunray.com"  # 邮件发送账号
    # qqCode = "Sunray201911"  # 授权码（这个要填自己获取到的）
    # qqCode="f546321."
    smtp_server = "smtp.szsunray.com"  # 固定写死
    smtp_port = 465  # 固定端口

    # 配置服务器
    smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
    try:
        smtp.login(from_addr, qqCode)
    except:
        raise Exception('请绑定你的邮箱账号密码')
    # 组装发送内容
    result_object["content"] = result_object["content"].replace('\n', '<br>')
    mail = MIMEMultipart()
    html = """
            <html>
            <style>
             table, td{ 
          border:1px solid black; 
          border-collapse:collapse; 
        }
        </style>
            <table style="white-space: pre-wrap;">
                    <tr><td colspan="2" style="text-align: center;">""" + str(
        result_object["title"]) + """</td></tr>
                    <tr><td style="width:'120px'">拜访日期：</td><td>""" + str(
        result_object["visit_date"]) + """</td></tr>

                        <tr><td style="width:'120px'">客户名称：</td>
                            <td>""" + str(result_object["customer_name"]) + """</td></tr>
                        <tr><td style="width:'120px'">客户规模：</td>
                            <td>""" + str(result_object["scope_id_name"]) + """</td></tr>
                        <tr><td style="width:'120px'">主营产品：</td>
                            <td>""" + str(result_object["customer_products"]) + """</td></tr>
                        <tr><td style="width:'120px'">年营业额：</td>
                            <td>""" + str(result_object["revenue_id_name"]) + """</td></tr>
                        <tr><td style="width:'120px'">生意机会：</td>
                            <td>""" + str(result_object["opportunity"]) + """</td></tr>
                        <tr><td style="width:'120px'">拜访目的：</td>
                            <td>""" + str(result_object["target"]) + """</td></tr>
                        <tr><td style="width:'120px'">协同人员：</td>
                            <td>""" + str(result_object["with_man"]) + """</td></tr>
                        <tr><td style="width:'120px'">会议内容：</td>
                            <td>""" + str(result_object["content"]) + """</td>
                </tr>

                </table>
            """ + files + """      
        </body>
        </html>
        """
    subject = '客户拜访记录：' + str(result_object['title'])
    to = str(result_object["to_email"])
    cc = str(result_object["cc_email"])
    mail = MIMEMultipart('related')
    content = MIMEText(html, _subtype='html', _charset='utf-8')
    mail.attach(content)
    for mI in msgImage:
        mail.attach(mI)
    mail["Subject"] = Header(subject, 'utf-8').encode()
    mail["From"] = from_addr
    mail["to"] = to
    # mail["To"] = "yangwenbo@szsunray.com"
    mail["Cc"] = cc
    recivers = list(filter(None, to.split(',') + cc.split(',')))
    result = smtp.sendmail(from_addr, recivers, mail.as_string())
    smtp.quit()


class Signer:
    def __init__(self, env, result=[], type='', action=''):
        self.env = env
        self.result = result
        self.type = type
        self.action = action
        self.ap = Stations('帐期额度申请单')

    def get_next_signer(self, station_no, review_id):
        next_signer, next_station = '', 0
        while not next_signer:
            # 首先判断下一站是否有签核人
            next_station = self.ap.getnextstation(station_no)
            next_signer = request.env['xlcrm.account.signers'].sudo().search_read(
                ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], ['signers'])
            next_signer = next_signer[0]['signers'] if next_signer else ''
            is_many_signer = self.many_signer(station_no, review_id)
            next_signer, next_station = is_many_signer if is_many_signer[0] else next_signer, next_station

    def many_signer(self, station_no, review_id):
        next_signer, next_station = '', ''
        signer = request.env['xlcrm.account.signers'].sudo().search_read(
            ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)], ['signers'])
        if signer:
            signers = signer[0]['signers'].split(',')
            signers_index = 0
            if len(signers) > 1:
                for index, value in enumerate(signers):
                    if value == str(self.env.uid):
                        signers_index = index
                        break
                if signers_index < len(signers) - 1:  # 多人签且当前签核人不是多人签中的最后一个时，下一站站别信息不变
                    next_station = station_no
                    next_signer = signers[signers_index + 1]
        return next_signer, next_station

    def back_signer(self, review_id, station_no, next_station):
        next_station, next_signer, stop = '', next_station, False
        sign_back = self.env['xlcrm.account.partial'].sudo().search_read(
            [('review_id', '=', review_id)], order='init_time desc', limit=1)
        if sign_back and sign_back[0]['sign_over'] == 'N':
            if next_station == station_no:  # 说明是多人签核且还有人没有签完
                next_station, next_signer, stop = 28, '', True
            else:
                sign_station = sign_back[0]['sign_station'] + str(station_no) + ',' if sign_back[0][
                    'sign_station'] else '' + str(station_no) + ','
                self.env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
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
                    next_station, next_signer, stop = 28, '', True
        return next_station, next_signer, stop

    def get_signer(self):
        for r in self.result:
            r["station_desc"] = self.ap.getStionsDesc(r['station_no'])
            r["review_type"] = FormType(r["review_type"]).getType()
            r["login_user"] = self.env.uid
            r["signer"] = [r["signer"][0]] if r["signer"] else []
            if r.get('station_no') == 28:
                r['signer_nickname'], r['signer'] = self.back_signer(r)

    def back_signer(self, r):
        signer_nickname, signer = '', ''
        _station = self.env['xlcrm.account.partial'].sudo().search_read(
            [('review_id', '=', r['id'])], order='init_time desc', limit=1)
        if _station[0]['sign_over'] == 'N':
            to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
            sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                'sign_station'] else []
        return signer, signer_nickname


def getSigner(env, result, type, action):
    import ast
    ap = Stations('帐期额度申请单')
    for r in result:
        r["station_desc"] = ap.getStionsDesc(r['station_no'])
        r["review_type"] = FormType(r["review_type"]).getType()
        r["login_user"] = env.uid
        r["signer"] = [r["signer"][0]] if r["signer"] else []

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
                        if int(sta) in (20, 21, 25, 30):
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
                        elif int(sta) == 45:
                            si = sig[0]['signers']
                            si_temp = ''
                            if '[' in si:
                                si_temp = ','.join(map(lambda x: str(x), eval(si.replace('[', '').replace(']', ''))))
                            signer = signer + ',' + si_temp if signer else si_temp
                            signer_temp = signer_temp + ',' + si_temp if signer_temp else si_temp
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
                signer = map(lambda x: int(x), filter(lambda x: x, signer.split(',')))
                r['signer'] = signer
                r['signer_nickname'] = signer_nickname
        r['type'] = type
        if action == 'update':
            signers = env['xlcrm.account.signers'].sudo().search_read([('review_id', '=', r['id']),
                                                                       ('station_no', '=',
                                                                        r['station_no'])])
            # pm,采购,mktvp 按品牌签核
            if r['station_no'] in (20, 21, 25, 30, 35, 40):
                if signers:
                    signed = map(lambda x: int(x), signers[0]['signed'].split(',')) if signers[0][
                        'signed'] else []
                    signer = map(lambda x: int(x), signers[0]['signers'].split(',')) if signers[0][
                        'signers'] else []
                    r['signer'] = list(set(signer) - set(signed))
                    r['signer_nickname'] = ','.join(
                        map(lambda x: x['nickname'],
                            env['xlcrm.users'].sudo().search_read(
                                [('id', 'in', r['signer'])])))
            if r['station_no'] == 45:
                si = signers[0]['signers']
                if '[' in si:
                    si = eval(si)
                    for s in si:
                        if isinstance(si, list):
                            r['signer'] = si
                            break
                        if r['signer'][0] == s or r['signer'][0] in s:
                            r['signer'] = s if isinstance(s, list) else [s]
                            break
                    r['signer_nickname'] = ','.join(
                        map(lambda x: x['nickname'],
                            env['xlcrm.users'].sudo().search_read(
                                [('id', 'in', r['signer'])])))
        if env.uid in r['signer']:
            r['status_id'] = 0

    return result


def loginwechat(code):
    try:
        import requests
        import urllib.parse
        import json

        # 向微信发请求验证
        params = {
            'code': code,
            'appid': 'wx513547ab52038ad1',
            'secret': '2dd9eb0540cf554d5682a4dcea36a267',
            'grant_type': 'authorization_code'
        }
        openid = ''
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.parse.urlencode(params)
        res = requests.get(url=url)
        if res.status_code == 200:
            data = json.loads(res.content)
            openid = data.get('openid')
        return openid
    except Exception as e:
        raise Exception(str(e))


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
        domain = [('review_id', '=', review_id)]
        if station_no not in (35, 40):
            domain.append(('init_user', '=', env.uid))
        brandname = data.get('brandname')
        if station_no in (20, 21, 25, 30):
            domain.append(('brandname', '=', brandname))
        result = env[station_model].sudo().search_read(domain=domain)
        if result:
            # data.pop('backreason')
            init_pop = data.pop('init_nickname') if data.get('init_nickname') else ''
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
        send_wechart = True
        if record_status > 0:
            date_main = {}
            from ..public import send_email
            email_obj = send_email.Send_email()
            next_signer = ''
            if record_status == 1:
                next_station = 0
                signed_temp = 'N'
                signed_temp_ = 'N'
                riskM_email = ''
                if station_no in (20, 21, 25, 30):
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
                    # 写入法务签核人
                    # if next_station == 40:
                    #     insertlgsigner(env, review_id, next_station)
                    next_signer = env['xlcrm.account.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], ['signers'])
                    if next_signer:
                        next_signer = eval(next_signer[0]['signers'])[0] if '[' in next_signer[0]['signers'] else \
                            next_signer[0]['signers']
                    else:
                        next_signer = ''

                    # 否是多人签核
                    signer_many = env['xlcrm.account.signers'].sudo().search_read(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)])
                    if signer_many:
                        signer_many = signer_many[0]
                        signers = signer_many['signers']
                        if '[' in signers:
                            signers = eval(signers)
                            signers = [signers] if isinstance(signers, list) else signers
                        else:
                            signers = signers.split(',')
                        signers_index = 0
                        if len(signers) > 1:
                            if station_no == 45:  # 风控多人签核有先后顺序
                                for index, value in enumerate(signers):
                                    value = str(value) if isinstance(value, int) else value
                                    if value == str(env.uid) or (isinstance(value, list) and env.uid in value):
                                        signers_index = index
                                        break
                                if signers_index < len(signers) - 1:  # 多人签且当前签核人不是多人签中的最后一个时，下一站站别信息不变
                                    next_station = station_no
                                    next_signer = signers[signers_index + 1]
                                    riskM_email = next_signer
                            elif station_no == 40:
                                from collections import Iterable
                                next_signer = ','.join(map(lambda x: str(x), next_signer)) if isinstance(
                                    next_signer, Iterable) else next_signer  # 风控助理
                            else:
                                if signer_many['sign_over'] == 'N' and signed_temp_ == 'N' and station_no != 35:
                                    next_station = station_no
                                    break
                                    # need_set =  set(signers) - set(signer_many['signed'].split(','))
                                    # next_signer =
                        # else:
                        #     next_signer = signers[0]
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
                                        sign_back[0]['sign_station'] else '' + str(station_no) + ','
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
                    elif data.get('loa'):
                        # 判断是否需要添加法务签核
                        write_lg_signer(env, review_id)
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
                sbuject = "帐期额度申请单待审核通知"
                to = [odoo.tools.config["test_username"]]
                to_wechart = odoo.tools.config["test_wechat"]
                cc = []
                if date_main['station_no'] in (35, 40, 45):  # 法务，财务，风控需要分别发送邮件
                    station_model = account.getModel(date_main['station_no'])
                    res_main = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
                    res = env['xlcrm.user.ccfnotice'].sudo().search_read([('a_company', '=', res_main[0]['a_company'])])
                    if res:
                        uid = res[0][station_model.split('.')[-1]]
                        uid = eval(uid) if uid else []
                        uid = [riskM_email] if riskM_email else uid  # 邮件通知风控主管
                    else:
                        pass
                for ui in uid:
                    user = env['xlcrm.users'].sudo().search([('id', '=', ui)], limit=1)
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        to = [user["email"]]
                        to_wechart = user['nickname'] + '，' + user["username"]
                    token = get_token(env, ui)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/account-list/' + str(
                        review_id) + "/" + json.dumps(token)
                    import hashlib
                    userinfo = base64.urlsafe_b64encode(to_wechart.encode())
                    appkey = odoo.tools.config["appkey"]
                    sign = hashlib.new('md5', userinfo + appkey).hexdigest()
                    url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
                        review_id, userinfo, sign)
                    # url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s' % (
                    #     review_id, base64.urlsafe_b64encode(to_wechart.encode()))
                    content = """
                                            <html lang="en">            
                                            <body>
                                                <div>
                                                    """ + user['nickname'] + """您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
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
                    account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
                    send_wechart = sendWechat('账期额度申请单待审核通知', to_wechart, url,
                                              '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
                                              account_result[0]["init_usernickname"],
                                              account_result[0]["init_time"])
            date_main["update_user"] = env.uid
            date_main["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            result = env['xlcrm.account'].sudo().browse(review_id).write(date_main)
        if success_email and send_wechart:
            env.cr.commit()
            if not isinstance(send_wechart, bool):
                send_wechart.commit()
                send_wechart.close()
            return True
        else:
            return False
    except Exception as e:
        return False


def write_lg_signer(env, review_id):
    res = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
    if res and res[0]['release_time_apply'] == '款到发货':
        lg_signer = env['xlcrm.account.signers'].sudo().search_read(
            [('review_id', '=', review_id), ('station_no', '=', 40)])
        if not lg_signer:
            specialsigner = env['xlcrm.user.ccfgroup'].sudo().search_read(
                [('status', '=', 1)],
                fields=['users', 'name'])
            lgSigner = eval(filter(lambda x: x['name'] == "LG", specialsigner)[0]['users'])
            env['xlcrm.account.signers'].sudo().create(
                {"review_id": review_id, "station_no": 40, 'station_desc': '法务签核',
                 'signers': ','.join(map(lambda x: str(x), lgSigner))})
            account_attend_user_ids = res[0]['account_attend_user_ids'] + lgSigner
            env['xlcrm.account'].sudo().browse(review_id).write(
                {'account_attend_user_ids': [[6, 0, account_attend_user_ids]]})


def get_token(env, uid):
    serve = odoo.tools.config['serve_url']
    db = odoo.tools.config['db_name']
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


def sendWechat(subject, to_wechart, url, content, init_user, init_time):
    from ..public import connect_mssql
    wechart = connect_mssql.Mssql('wechart')
    send_wechart = wechart.in_up_de(
        "insert into dbo.BusinessTemplateMsg(templateType,userId,url,first,key1,key2)values('" + subject + "','" + to_wechart + "','" + url + "', '" + content + "', '" + init_user + "', '" + init_time + "')")

    return wechart if send_wechart else send_wechart


def insertlgsigner(env, review_id, station_no):
    st = Stations('帐期额度申请单')
    station_code = st.getStionsCode(station_no)
    station_desc = st.getStionsDesc(station_no)
    signer = env['xlcrm.user.ccfgroup'].sudo().search_read([('name', '=', station_code), ('status', '=', 1)],
                                                           fields=['users'])
    if signer:
        signer = eval(signer[0]['users'])
        for si in signer:
            env['users.account_rel'].sudo().create({'account_id': review_id, 'users_id': si})
        env['xlcrm.account.signers'].sudo().create(
            {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
             'signers': ','.join(map(lambda x: str(x), signer))})
        env.cr.commit()


def get_date(date_int):
    import datetime
    date_int = date_int if not date_int or type(date_int) == str else datetime.date(1899, 12,
                                                                                    31) + datetime.timedelta(
        days=date_int - 1)
    return date_int
