# -*- coding: utf-8 -*-
import datetime
import odoo
from odoo.http import request

import json, base64


class BaseInfo:
    @staticmethod
    def get_stations_desc(station=None):
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
        return tar_dict[int(station)] if station else tar_dict

    @staticmethod
    def get_staions(desc=None):
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
        return tar_dict[desc] if desc else tar_dict

    @staticmethod
    def get_model(station_no, type=None):
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
        return "xlcrm.account." + tar_dict[int(station_no)]

    @staticmethod
    def get_next_station(current_no):
        dict_next = {1: 5, 5: 10, 10: 15, 15: 16, 16: 20, 20: 21, 21: 25, 25: 30, 30: 35, 35: 36, 36: 40, 40: 45,
                     45: 46,
                     46: 50,
                     50: 55,
                     55: 99}
        return dict_next[int(current_no)]

    @staticmethod
    def get_forward_station(current_no):
        dict_next = {5: 1, 10: 5, 15: 10, 16: 15, 20: 16, 21: 20, 25: 21, 30: 25, 35: 30, 36: 35, 40: 36, 45: 40,
                     46: 45,
                     50: 46,
                     55: 50,
                     99: 55}
        return dict_next[int(current_no)]

    @staticmethod
    def get_staions_reject(desc):
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

    @staticmethod
    def get_station_code(station):
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
        return tar_dict[int(station)]

    def get_model_by_station(self, station_no):
        dict_tar = self.get_model(station_no, type='in')
        return dict(filter(lambda x: x[0] <= station_no, dict_tar.items()))

    @staticmethod
    def get_stations_reject(desc):
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


class CCF(BaseInfo):
    def get_pmins(self, products, env):
        pmins, pm_inspector_brand_names = [], ''
        for pmin in products:
            brand_name = pmin.get('sign_brand_name')
            if pmin.get('PM'):
                res_ = env['xlcrm.user.ccfpminspector'].sudo().search_read([('pm', 'ilike', pmin.get('PM'))])
                if res_:
                    pm_inspector_brand_names = pm_inspector_brand_names + ',' + brand_name if pm_inspector_brand_names else brand_name
                    pmins.append(res_[0]['inspector'])
                    pmin['PMins'] = res_[0]['inspector']
        return pm_inspector_brand_names, pmins

    def create(self, model, data, env):
        return env[model].sudo().create(data).id

    def update(self, model, id, data, env):
        return env[model].sudo().browse(id).write(data)

    def create_or_update(self, model, data, env):
        review_id = data.pop('review_id')
        res = env[model].sudo().search_read([('review_id', '=', review_id)])
        if res:
            return self.update(model, res[0]['id'], data, env)
        else:
            return self.create(model, data, env)

    def get_user_id(self, reviewers, env):
        userIds = {}
        for key, value in reviewers.items():
            if isinstance(value, list):
                userIds[key] = []
                for va in value:
                    if va:
                        if not isinstance(va, int):
                            va = self.__get_user_id_by_names(va, env)
                        userIds[key].append(va)
            else:
                if value:
                    if not isinstance(value, int):
                        value = self.__get_user_id_by_names(value, env)
                    userIds[key] = value

        userIds['Base'] = env.uid
        return userIds

    def __get_user_id_by_names(self, names, env):
        username = names.split('(')[1].split(')')[0] if '(' in names else names
        names = env['xlcrm.users'].sudo().search(
            ['|', ('username', 'ilike', username + '@'), ('username', '=', username)])[0][
            'id'] if username else ''
        return names

    def get_special_signer(self, a_company, release_time_apply, protocol_code, env):
        manage, lg, fd, fdm, risk, error_msg = '', '', '', '', '', ''
        special_signer = env['xlcrm.user.ccfgroup'].sudo().search_read(
            [('status', '=', 1)],
            fields=['users', 'name'])
        need = env['xlcrm.account.special.signers'].sudo().search_read(
            [('code', '=', protocol_code)], limit=1
        )
        if a_company not in ('深蕾半导体（香港）有限公司', '深圳前海深蕾半导体有限公司'):
            # 添加总经理跟董事长签核人
            manage = 4
            # 添加风控签核人
            risk_signer = list(filter(lambda x: x['name'] == "RISK", special_signer))
            if risk_signer:
                risk_signer = [eval(risk_signer[0]['users'])]
            else:
                error_msg = '无风控审核人，请联系管理员维护风控组成员'
                return manage, lg, fd, fdm, risk, error_msg
            lg, fd, fdm, risk_m, error_msg = self.__compute_special_signer(special_signer)
            if error_msg:
                return manage, lg, fd, fdm, risk, error_msg
            # 添加法务,财务签核人/非款到发货
            if not need:
                error_msg = '付款协议%s没有维护款到发货签核人信息，请联系管理员到系统设置中维护' % protocol_code
                return manage, lg, fd, fdm, risk, error_msg
            lg = lg if need[0]['lg'] else ''
            fd, fdm = (fd, fdm) if need[0]['fd'] else ('', '')
            if need[0]['riskm']:
                risk_signer.append(risk_m)
            risk = risk_signer
        return manage, lg, fd, fdm, risk, error_msg

    @staticmethod
    def __compute_special_signer(special_signer):
        lg, fd, fdm, risk_m, error_msg = '', '', '', '', ''
        lg_signer = list(filter(lambda x: x['name'] == "LG", special_signer))
        risk_signer_m = list(filter(lambda x: x['name'] == "RISKM", special_signer))
        fd_signer = list(filter(lambda x: x['name'] == "FD", special_signer))
        fd_signer_m = list(filter(lambda x: x['name'] == "FDM", special_signer))
        if lg_signer and risk_signer_m and fd_signer and fd_signer_m:
            lg_signer = eval(lg_signer[0]['users'])
            risk_signer_m = eval(risk_signer_m[0]['users'])[0]
            fd_signer = eval(fd_signer[0]['users'])
            fd_signer_m = eval(fd_signer_m[0]['users'])
        else:
            error_msg = '请联系系统管理员设置法务，财务，风控用户组'
            return lg, fd, fdm, risk_m, error_msg
        lg, fd, fdm, risk_m = lg_signer, fd_signer, fd_signer_m, risk_signer_m
        return lg, fd, fdm, risk_m, error_msg

    def __create_signer(self, review_id, signers, products, pm_inspector_brand_names, env):
        account_attend_user_ids, sta_list = [], []
        for key, values in signers.items():
            station_no = self.get_staions(key)
            station_desc = self.get_stations_desc(station_no)
            signer = values
            signer = [signer] if isinstance(signer, int) else signer
            if signer:
                sta_list.append(station_no)
                for s in signer:
                    if s:
                        if isinstance(s, list):
                            account_attend_user_ids += s
                        else:
                            account_attend_user_ids.append(s)

                sign_result = env['xlcrm.account.signers'].sudo().search_read(
                    [('review_id', '=', review_id), ('station_no', '=', station_no)])
                brand_name = ''
                if station_no in (20, 25, 30):
                    brand_name = ','.join(
                        list(map(lambda x: x['sign_brand_name'], products)))
                if station_no == 21:
                    brand_name = pm_inspector_brand_names
                if sign_result:
                    write_data = {}
                    signers = ','.join(list(map(lambda x: str(x), signer)))
                    write_data['signed'] = ''
                    write_data['brandnamed'] = ''
                    write_data['brandname'] = brand_name
                    if sign_result[0]['signers'] == signers:
                        write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                    else:
                        write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                        write_data['signers'] = signers
                    self.update('xlcrm.account.signers', sign_result[0]['id'], write_data, env)
                else:
                    env['xlcrm.account.signers'].sudo().create(
                        {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                         'signers': ','.join(list(map(lambda x: str(x), signer))), 'brandname': brand_name})
                station_model = self.get_model(station_no)
                signed_result = env[station_model].sudo().search_read(
                    [('review_id', '=', review_id), ('station_no', '=', station_no)])
                if signed_result and signed_result[0]['init_user'][0] not in signer:
                    env[station_model].sudo().browse(signed_result[0]['id']).unlink()
        return account_attend_user_ids, sta_list

    def add(self, data, products, pm_inspector_brand_names, env):
        record_status = data.get('record_status')
        signers = data.get('signers')
        account_attend_user_ids = []
        data['signer'] = ',%d,' % env.uid if record_status == 0 else data['signer']
        review_id = self.create('xlcrm.account', data, env)
        if record_status == 1:
            env['xlcrm.account.base'].sudo().create(
                {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
            signers['Manage'], signers['LG'], signers['FD'], signers[
                'FDM'], signers['RISK'], error_msg = self.get_special_signer(data['a_company'],
                                                                             data['release_time_apply'],
                                                                             data['protocol_code'], env)
            if error_msg:
                raise Exception(error_msg)
            # 写入签核人信息(pm,pmm,pur除外)
            account_attend_user_ids, _ = self.__create_signer(review_id, signers, products, pm_inspector_brand_names,
                                                              env)
        return account_attend_user_ids, review_id

    def set(self, data, products, pm_inspector_brand_names, env):
        record_status = data.get('record_status')
        signers = data.get('signers')
        account_attend_user_ids, review_id = [], data['id']
        data['signer'] = ',%d,' % env.uid if record_status == 0 else data['signer']
        self.update('xlcrm.account', review_id, data, env)
        if record_status == 1:
            self.create_or_update('xlcrm.account.base',
                                  {'review_id': review_id, 'station_no': 1, 'init_user': env.uid,
                                   'update_user': env.uid}, env)
            signers['Manage'], signers['LG'], signers['FD'], signers[
                'FDM'], signers['RISK'], error_msg = self.get_special_signer(data['a_company'],
                                                                             data['release_time_apply'],
                                                                             data['protocol_code'], env)
            if error_msg:
                raise Exception(error_msg)
            account_attend_user_ids, sta_list = self.__create_signer(review_id, signers, products,
                                                                     pm_inspector_brand_names, env)
            self.__del_history_signer(review_id, sta_list, env)
            self.__del_change_brand(review_id, products, env)
        return account_attend_user_ids, review_id

    def __del_history_signer(self, review_id, sta_list, env):
        # 删除不在这次签核人
        no_station = env['xlcrm.account.signers'].sudo().search_read(
            [('review_id', '=', review_id), ('station_no', 'not in', sta_list)])
        env['xlcrm.account.signers'].sudo().search(
            [('review_id', '=', review_id), ('station_no', 'not in', sta_list)]).unlink()

        # 删除不在这次签核签核记录
        if no_station:
            for no_st in no_station:
                no_model = self.get_model(no_st['station_no'])
                env[no_model].sudo().search([('review_id', '=', review_id)]).unlink()

    def __del_change_brand(self, review_id, products, env):
        # 如果品牌变更，则品牌相关sales，pm，采购，mktvp原有的签核记录删除
        new_brandnames = list(map(lambda x: x['brandname'], products))
        sales_res = env['xlcrm.account.sales'].sudo().search_read([('review_id', '=', review_id)])
        if sales_res:
            s_product = eval(sales_res[0]['products'])
            s_brandname = list(map(lambda x: x['brandname'], s_product))
            if not set(s_brandname) == set(new_brandnames):
                new_product = [
                    list(filter(lambda x: x['brandname'] == bra, s_product))[0] if bra in s_brandname else {
                        'brandname': bra, 'currency': '万人民币', 'turnover': ''} for bra in new_brandnames]
                env['xlcrm.account.sales'].sudo().browse(sales_res[0]['id']).write(
                    {'products': new_product})
        for mo in ('pm', 'pmins', 'pur', 'pmm'):
            mo = 'xlcrm.account.%s' % mo
            pm_res = env[mo].sudo().search_read([('review_id', '=', review_id)])
            if pm_res:
                for p_res in pm_res:
                    if not p_res['brandname'] in new_brandnames:
                        env[mo].sudo().browse(p_res['id']).unlink()

    def change_documents(self, review_id, documents, env):
        doucument_ids = []
        for item in documents:
            doucument_ids.append(item['document_id'])
        if doucument_ids:
            env['xlcrm.documents'].sudo().browse(doucument_ids).write({'res_id': review_id})

    def send_email(self, uid, review_id, env):
        from . import send_email
        email_obj = send_email.Send_email()
        sbuject = "帐期额度申请单待审核通知"
        cc = []
        self._get_to_towechat(uid, env)
        self._get_href_url(uid, self.to_wechart, review_id, env)
        content = """
            <html lang="en">            
            <body>
                <div>
                    您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核帐期额度申请单，请点击
                    <a href='""" + self.href + """' ><font color="red">PC端链接</font></a>或<a href='""" + self.url + """' ><font color="red">移动端链接</font></a>进入系统审核
                </div>
                <div>
                <br>
                注：系统仅支持谷歌浏览器，如打开链接异常或默认浏览器不是谷歌，请复制如下网址链接：<font color="red">crm.szsunray.com:9020</font>，用谷歌浏览器打开链接，系统登录帐号为公司邮箱号，登录密码默认为Sunray2020（S大写，如有修改密码，请用修改后的密码登录）
                </div>
            </body>
            </html>
            """
        msg = email_obj.send(subject=sbuject, to=self.to, cc=cc, content=content, env=env)
        if msg["code"] == 500:
            raise ValueError('发送邮件错误')

    def send_wechat(self, uid, review_id, env):
        try:
            from . import send_wechat
            self._get_to_towechat(uid, env)
            self._get_href_url(uid, self.to_wechart, review_id, env)
            account_result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            send_wechart = send_wechat.send_wechat('账期额度申请单待审核通知', self.to_wechart, self.url,
                                                   '您好！ 您有账期额度申请单待审核，请登录新蕾电子 企业云平台进行审核',
                                                   account_result[0]["init_usernickname"],
                                                   datetime.datetime.strftime(account_result[0]["init_time"],
                                                                              '%Y-%m-%d %H:%M:%S'))
        except Exception as e:
            raise Exception(repr(e))

    def _get_href_url(self, uid, to_wechart, review_id, env):
        import hashlib
        userinfo = base64.urlsafe_b64encode(to_wechart.encode()).decode()
        appkey = odoo.tools.config["appkey"]
        sign = hashlib.new('md5', (userinfo + appkey).encode()).hexdigest()
        url = 'http://crm.szsunray.com:9030/public/ccf-list/%d/%s/%s' % (
            review_id, userinfo, sign)
        token = self.get_token(uid, env)
        href = 'http://crm.szsunray.com:9020/#/public/account-list_new/' + str(
            review_id) + "/" + json.dumps(token)
        self.url, self.href = url, href

    def _get_to_towechat(self, uid, env):
        to_wechart = odoo.tools.config["test_wechat"]
        to = [odoo.tools.config["test_username"]]
        if odoo.tools.config["enviroment"] == 'PRODUCT':
            user = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
            to_wechart = user['nickname'] + '，' + user["username"]
            to = [user["email"]]
        self.to, self.to_wechart = to, to_wechart

    def get_token(self, uid, env):
        import time
        serve = odoo.tools.config['serve_url']
        db = odoo.tools.config['db_user']
        # username = kw.pop('username')
        # password = kw.pop('password')
        user_obj = env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)
        username = user_obj["username"]
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
        return result_data

    def get_flow_list(self, current_sta, env):
        result = []
        if current_sta:
            current_sta = current_sta[0]
            current_station, review_id = current_sta["station_no"], current_sta["id"]
            records_ref = env['xlcrm.account.signers'].sudo().search_read([("review_id", '=', review_id)])
            if records_ref:
                for item in records_ref:
                    station_no = item["station_no"]
                    signer_model = self.get_model(station_no)
                    uid = item["signers"]
                    station_desc = self.get_stations_desc(station_no)
                    timestamp, signed = '', False
                    if current_station == 28:
                        back = env['xlcrm.account.partial'].sudo().search_read([('review_id', '=', review_id)],
                                                                               order='init_time desc',
                                                                               limit=1)
                        if back and back[0]['from_station'] > station_no:
                            signed = True
                    elif current_station > station_no:
                        signed = True

                    domain = [("review_id", '=', review_id), ('station_no', '=', station_no)]
                    signer_info = env[signer_model].sudo().search_read(domain, order='update_time desc')
                    if signer_info:
                        timestamp = signer_info[0]['update_time']
                        if station_no == 45 and len(uid.split('],')) < 2 or len(signer_info) > 1:
                            # signed = True
                            uid = list(map(lambda x: x['update_user'][0], signer_info))

                    uid = uid if isinstance(uid, list) else uid.replace('[', '').replace(']', '').split(',')
                    nickname = ','.join(
                        list(map(lambda x: x['nickname'], env['xlcrm.users'].sudo().search(
                            [('id', 'in', list(filter(lambda x: x, uid)))], order='id desc'))))
                    if nickname:
                        description = nickname + ' (' + station_desc + ')'
                        result.append(
                            {"station_no": station_no, "description": description,
                             "timestamp": timestamp,
                             "signed": signed})
        return result

    def get_flow_reject(self, rejects, env):
        rejects_result = []
        if rejects:
            for reject in rejects:
                station_desc = self.get_stations_desc(reject['station_no']).replace('签核', '')
                reason = [reject['reason']]
                init_user = env["xlcrm.users"].sudo().search_read([("id", "=", reject["init_user"][0])])[0][
                    "nickname"]
                init_time = reject["init_time"]
                rejects_result.append(
                    {"description": station_desc + ' ' + init_user + " (驳回)", "timestamp": init_time,
                     'reason': reason})
        return rejects_result

    def get_flow_partial(self, partials, env):
        rejects_result = []
        if partials:
            for partial in partials:
                station_desc = self.get_stations_desc(partial['from_station']).replace('签核', '')
                init_user = env["xlcrm.users"].sudo().search([("id", "=", partial["init_user"][0])])[0][
                    "nickname"]
                init_time = partial["init_time"]
                reason = []
                to_station = partial["to_station"].split(',')[:-1]
                a = -1
                for i in range(len(to_station)):
                    desc = self.get_stations_desc(int(to_station[i])).replace('签核', '')
                    if int(to_station[i]) in (20, 21, 25, 30):
                        sec = env['xlcrm.account.partial.sec'].sudo().search_read(
                            [('review_id', '=', partial['review_id'][0]), ('station_no', '=', int(to_station[i])),
                             ('p_id', '=', partial['id'])])
                        if sec:
                            sec = sec[0]
                            brandname = sec['to_brand'].split(',')[:-1]
                            brand_remark = sec["remark"].split("\p")[:-1]
                            for j in range(len(brandname)):
                                desc_ = '%s(品牌：%s)' % (desc, brandname[j].split('_index')[0])
                                reason.append(desc_ + '::--->' + brand_remark[j])
                    else:
                        a += 1
                        remark = partial["remark"].split("\p")[:-1]
                        reason.append(desc + '::--->' + remark[a])
                rejects_result.append(
                    {"description": station_desc + ' ' + init_user + " (部分驳回)", "timestamp": init_time,
                     'reason': reason})
        return rejects_result

    def next_form(self, model, data, env):
        try:
            review_id, station_no, si_station, record_status = data.get('review_id'), data.get("station_no"), data.get(
                "si_station"), data.get(
                'record_status')
            station_no, si_station = int(station_no), int(si_station) if si_station else int(station_no)
            data['station_no'] = si_station
            if si_station == 1:
                data.pop('station_no')
                data.pop('signer')
                data['init_nickname'] = ''
                review_id = data.get('id')
                env['xlcrm.account.affiliates'].sudo().search([('account', '=', review_id)]).unlink()
                for item in data['affiliates']:
                    item['account'] = review_id
                    self.create('xlcrm.account.affiliates', item, env)
                env[model].sudo().browse(review_id).write(data)
            station_model = self.get_model(si_station)
            domain = [('review_id', '=', review_id)]
            if si_station not in (35, 40):
                domain.append(('init_user', '=', env.uid))
            brandname = data.get('brandname')
            if si_station in (20, 21, 25, 30):
                domain.append(('brandname', '=', brandname))
            result = env[station_model].sudo().search_read(domain=domain)
            if result:
                model_id = result[0]['id']
                data.pop('init_nickname', None)
                data.pop('record_status', None)
                data["update_user"] = env.uid
                data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                self.update(station_model, result[0]['id'], data, env)
            else:
                data['review_id'] = review_id
                data["init_user"], data["update_user"] = env.uid, env.uid
                data["init_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                model_id = self.create(station_model, data, env)
            if si_station == 20:
                env['xlcrm.material.profit'].sudo().search([('pm_id', '=', model_id)]).unlink()
                for item_ in data['material_profit']:
                    item_['pm_id'] = model_id
                    self.create('xlcrm.material.profit', item_, env)
            if record_status == 1:
                data_main = {}
                signed_temp, signed_temp_ = self.update_signed(review_id, si_station, brandname, env)
                data_main['station_no'], next_signer, data_main[
                    'station_desc'], risk_leader_email = self.get_next_singer(
                    review_id, station_no, signed_temp, signed_temp_, env)
                data_main['signer'] = ',%s,' % ','.join(next_signer).replace(' ', '') if next_signer else ''
                data_main['status_id'] = 3 if data_main['station_no'] == 99 else 2
                if si_station == 5:
                    self.update_lg_signer(review_id, env, data.get('loa'))
                if next_signer:
                    uid = next_signer
                    if data_main['station_no'] in (35, 40, 45):  # 法务，财务，风控需要分别发送邮件
                        station_model = self.get_model(data_main['station_no'])
                        res_main = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
                        res = env['xlcrm.user.ccfnotice'].sudo().search_read(
                            [('a_company', '=', res_main[0]['a_company'])])
                        if res:
                            uid = res[0][station_model.split('.')[-1]]
                            uid = eval(uid) if uid else []
                            uid = [risk_leader_email] if risk_leader_email else uid  # 邮件通知风控主管
                    for ui in uid:
                        if ui:
                            self.send_email(ui, review_id, env)
                data_main["update_user"] = env.uid
                data_main["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
                self.update('xlcrm.account', review_id, data_main, env)
            env.cr.commit()
        except Exception as e:
            raise Exception(repr(e))

    def update_signed(self, review_id, sign_station, brandname, env):
        signed_temp, signed_temp_ = 'N', 'N'
        # station_no = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])[0]['station_no']
        # if station_no == 28:
        sign_back = env['xlcrm.account.partial'].sudo().search_read(
            [('review_id', '=', review_id)], order='init_time desc', limit=1)
        if sign_back and sign_back[0]['sign_over'] == 'N':
            if sign_station in (20, 21, 25, 30):
                signed_temp = self.__get_special_back(review_id, sign_station, brandname, env)
            if signed_temp == 'Y' or sign_station not in (20, 21, 25, 30):
                sign_station = str(sign_station) if not sign_back[0]['sign_station'] else sign_back[0][
                                                                                              'sign_station'] + str(
                    sign_station)
                sign_station += ','
                self.update('xlcrm.account.partial', sign_back[0]['id'], {'sign_station': sign_station}, env)
                # env.cr.commit()
        else:
            signed_temp_ = self.__get_special_signer(review_id, sign_station, brandname, env)
        return signed_temp, signed_temp_

    def __get_special_back(self, review_id, station_no, brandname, env):
        signed_temp = 'N'
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

                to_brand = backs[0]['to_brand']
                if brandname in to_brand.split(','):
                    self.update('xlcrm.account.partial.sec', backs[0]['id'], {'sign_brand': si_brand}, env)
                sign_brand = backs[0]['sign_brand'] if backs[0]['sign_brand'] else ''
                ne_signed = list(set(to_brand.split(',')) - set(sign_brand.split(',')))
                if not ne_signed or (len(ne_signed) == 1 and ne_signed[0] == brandname):
                    signed_temp = 'Y'

        return signed_temp

    def __get_special_signer(self, review_id, station_no, brandname, env):
        temp_data, signed_temp_ = {}, ''
        res = env['xlcrm.account.signers'].sudo().search_read(
            ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)])
        if res:
            res = res[0]
            signed = str(env.uid) if not res['signed'] else res['signed'] + ',' + str(env.uid)
            if brandname:
                brandnamed = brandname if not res['brandnamed'] else res['brandnamed'] + ',' + brandname
                signed_temp_ = 'Y' if sorted(set(signed.split(','))) == sorted(
                    set(res['signers'].split(','))) and sorted(set(brandnamed.split(','))) == sorted(
                    set(res['brandname'].split(','))) else 'N'
                temp_data['brandnamed'] = brandnamed
            else:
                signed_temp_ = 'Y' if sorted(set(signed.split(','))) == sorted(
                    set(res['signers'].replace('[', '').replace(']', '').split(','))) else 'N'
            temp_data['signed'] = signed
            self.update('xlcrm.account.signers', res['id'], temp_data, env)
        return signed_temp_

    def get_next_singer(self, review_id, station_no, signed_temp, signed_temp_, env):
        next_station, next_signer, station_desc, risk_leader_email = 0, '', '', ''
        back_sign = False
        # station_no = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])[0]['station_no']
        while not next_signer:
            if station_no == 28:
                sign_back = env['xlcrm.account.partial'].sudo().search_read(
                    [('review_id', '=', review_id)], order='init_time desc', limit=1)
                if sign_back and sign_back[0]['sign_over'] == 'N':
                    next_station = 28
                    signed_station = set(sign_back[0]['sign_station'].split(',')) if sign_back[0][
                        'sign_station'] else set()
                    to_station = set(sign_back[0]['to_station'].split(','))
                    ne_station = tuple(to_station - signed_station)
                    if signed_temp == 'Y' and 1 == 2:  # 说明(pm.pmin,pur,mkt回签已经完成)
                        next_signer, station_desc = self._get_common_signer(review_id, ne_station, env)
                    else:
                        tar_set = {'20', '21', '25', '30'}
                        common_station = tuple(set(ne_station) - tar_set)
                        next_signer, station_desc = self._get_common_signer(review_id, common_station, env)
                        for ne in set(ne_station) & tar_set:
                            next_signer_tmp = self._get_partial_signer(env, review_id, ne)
                            next_signer += next_signer_tmp
                            station_desc += '%s(%s)-回签' % (self.get_stations_desc(ne),
                                                           self._get_user_nickname([('id', 'in', next_signer_tmp)],
                                                                                   'nickname', env, True))
                    next_signer = ','.join(next_signer)
                    break
                else:
                    station_no, back_sign = sign_back[0]['from_station'], True
            if station_no in range(20, 46):
                signer_ = self._search_signers(['&', ('review_id', '=', review_id), ('station_no', '=', station_no)],
                                               env)
                if station_no == 45:
                    signer_tmp = signer_[0]['signers'].split('],') if signer_ else []
                    if not back_sign and len(signer_tmp) > 1 and str(env.uid) != signer_tmp[-1]:
                        next_station, next_signer = station_no, signer_tmp[-1]
                        risk_leader_email = next_signer
                        station_desc = '%s(%s)' % (self.get_stations_desc(station_no), self._get_user_nickname(
                            [('id', 'in', tuple(next_signer.split(',')))], 'nickname', env, True))
                        break
                elif station_no < 35:
                    if signer_:
                        if signer_[0]['sign_over'] == 'N' and signed_temp_ == 'N':
                            next_station = station_no
                            signed = set(signer_[0]['signed'].split(',')) if signer_[0]['signed'] else set()
                            signers = set(signer_[0]['signers'].split(','))
                            next_signer = ','.join(signers - signed)
                            if next_signer:
                                station_desc = '%s(%s)' % (self.get_stations_desc(station_no), self._get_user_nickname(
                                    [('id', 'in', tuple(next_signer.split(',')))], 'nickname', env, True))
                            break

            if back_sign:
                station_no = self.get_forward_station(station_no)
            next_station = self.get_next_station(station_no)
            next_signer = self._search_signers(
                ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)], env)
            next_signer = next_signer[0]['signers'] if next_signer else ''
            if next_station == 45 and station_no != next_station and next_signer:
                next_signer = next_signer.split('],')[0]
            next_signer = next_signer.replace('[', '').replace(']', '')
            station_desc = '%s(%s)' % (self.get_stations_desc(next_station), self._get_user_nickname(
                [('id', 'in', tuple(next_signer.split(',')))], 'nickname', env, True)) if next_signer else ''
            station_no = next_station
            if station_no == 99:
                station_desc = '签核完成'
                break
        next_signer = next_signer.replace('[', '').replace(']', '').split(',')
        return next_station, next_signer, station_desc, risk_leader_email

    def _search_signers(self, domain, env):
        res = env['xlcrm.account.signers'].sudo().search_read(domain)
        return res

    def _get_user_nickname(self, domain, fields, env, many=False):
        res = env['xlcrm.users'].sudo().search_read(domain, [fields])
        return ','.join(list(map(lambda x: x[fields], res))) if many else res[0][fields]

    def _get_common_signer(self, review_id, ne_station, env):
        next_signer, station_desc = [], ''
        res_signer = self._search_signers(
            [('review_id', '=', review_id), ('station_no', 'in', ne_station)], env)
        for res_ in res_signer:
            next_temp = res_['signers'].replace('[', '').replace(']', '').split(',')
            next_signer += next_temp
            nickname = self._get_user_nickname([('id', 'in', next_temp)], 'nickname', env, True)
            station_desc += '%s(%s)' % (self.get_stations_desc(res_['station_no']), nickname)

        return next_signer, station_desc

    def _get_partial_signer(self, env, review_id, ne):
        next_signer_tmp = []
        backs = env['xlcrm.account.partial.sec'].sudo().search_read(
            [('review_id', '=', review_id), ('station_no', '=', ne)],
            order='init_time desc', limit=1)
        if backs[0]['sign_over'] == 'N':
            to_brand = backs[0]['to_brand'].split(',') if backs[0]['to_brand'] else {}
            sign_brand = backs[0]['sign_brand'].split(',') if backs[0]['sign_brand'] else {}
            ne_brands = set(to_brand) - set(sign_brand)
            if '' in ne_brands:
                ne_brands.remove('')
            sig = self._search_signers([('review_id', '=', review_id), ('station_no', '=', ne)],
                                       env)
            for tar_brand in ne_brands:
                uid_index = self._compute_partial_singer(tar_brand, sig[0]['brandname'].split(','))
                next_signer_tmp.append(sig[0]['signers'].split(',')[uid_index])
        return next_signer_tmp

    def _compute_partial_singer(self, tar_brands, brandnames):
        for index, brand in enumerate(brandnames):
            if brand == tar_brands:
                return index

    def update_lg_signer(self, review_id, env, loa):
        res = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
        if res:
            lg_signer = env['xlcrm.account.signers'].sudo().search_read(
                [('review_id', '=', review_id), ('station_no', '=', 40)])
            if not lg_signer and loa:
                special_signer = env['xlcrm.user.ccfgroup'].sudo().search_read(
                    [('status', '=', 1)], fields=['users', 'name'])
                lg_signer = eval(list(filter(lambda x: x['name'] == "LG", special_signer))[0]['users'])
                env['xlcrm.account.signers'].sudo().create(
                    {"review_id": review_id, "station_no": 40, 'station_desc': '法务签核',
                     'signers': ','.join(list(map(lambda x: str(x), lg_signer)))})
                account_attend_user_ids = res[0]['account_attend_user_ids'] + lg_signer
                self.update('xlcrm.account', review_id, {'account_attend_user_ids': [[6, 0, account_attend_user_ids]]},
                            env)
            elif lg_signer and not loa:
                is_need = env["xlcrm.account.special.signers"].sudo().search_read(
                    [('code', '=', res[0]['protocol_code'])])
                if is_need and is_need[0]['lg'] == '否':
                    env['xlcrm.account.signers'].sudo().browse(lg_signer[0]['id']).unlink()

    def get_query_list_domain(self, query_filter, env):
        domain = []
        if query_filter:
            if query_filter.get("status_id") == 0:
                signer = ',%s,' % str(env.uid)
                domain.append(('signer', 'ilike', signer))
            elif query_filter.get("status_id"):
                domain.append(('status_id', '=', query_filter.get("status_id")))
            if query_filter.get("status_id"):
                domain.append(('status_id', '=', query_filter.get("status_id")))
            if query_filter.get("sdate"):
                domain.append(('create_date', '>=', query_filter.get("sdate")))
            if query_filter.get("edate"):
                domain.append(('create_date', '<=', query_filter.get("edate")))
            if query_filter.get("usdate"):
                domain.append(('station_no', '=', 99))
                domain.append(('update_time', '>=', query_filter.get("usdate")))
            if query_filter.get("uedate"):
                domain.append(('station_no', '=', 99))
                domain.append(('update_time', '<=', query_filter.get("uedate")))
            if query_filter.get("a_company"):
                domain.append(('a_company', 'ilike', query_filter.get("a_company")))
            if query_filter.get("department"):
                domain.append(('department', 'ilike', query_filter.get("department")))
            if query_filter.get("kc_company"):
                domain.append(('kc_company', 'ilike', query_filter.get("kc_company")))
            if query_filter.get("init_usernickname"):
                domain.append(('init_usernickname', '=', query_filter.get("init_usernickname")))
        records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
        if records_ref.group_id.id != 1 and env.uid not in (165, 166):
            if len(domain) > 0:
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
                    domain += [('account_attend_user_ids', 'ilike', child)]
                    if index < len(childs) - 1:
                        domain += ['|']
            if records_ref['username'] == 'jinhuihui@szsunray.com':
                childs = records_ref.child_ids_all.ids
                station_sign = 25
                domain += ['|']
                for index, child in enumerate(childs):

                    domain += [('account_attend_user_ids', 'ilike', child)]
                    if index < len(childs) - 1:
                        domain += ['|']
            domain += [('init_user', 'in', records_ref.child_ids_all.ids)]
            if station_sign:
                domain += [('station_no', '>=', station_sign)]
        # if env.uid == 4:
        #     domain = [('signer', 'ilike', '4,')]
        return domain

    def get_query_list_order(self, query_filter):
        order = 'update_time desc'
        if query_filter:
            order_field = query_filter.get('order_field')
            order_type = query_filter.get('order_type')
            condition = order_field
            if condition:
                if condition == "init_usernickname":
                    condition = 'init_user'
                    order = condition + " " + order_type
                elif condition == "update_usernickname":
                    condition = 'update_user'
                    order = condition + " " + order_type
                elif condition == "signer_desc":
                    order = "signer " + order_type + ',' + 'station_desc ' + order_type
                else:
                    order = condition + " " + order_type
        return order

    def export_query_list(self, res, env):
        for r in res:
            current_account_period = []
            profit = []
            if r['current_account_period']:
                current_account_period = eval(r['current_account_period'])
            r['current_account_period'] = current_account_period
            if r['cs']:
                cs_ = self.get_cs_new(r['id'],env)
                r['registered_captial'] = cs_['registered_capital'] + cs_[
                    'registered_capital_currency']
                r['paid_capital'] = cs_['paid_capital'] + cs_['paid_capital_currency']
                r['insured_persons'] = cs_['insured_persons']
                r['listed_company'] = cs_.get('listed_company')

            else:
                res_customer = env['xlcrm.account.customer'].sudo().search_read([('review_id', '=', r['id'])])
                if res_customer:
                    res_customer = res_customer[0]
                    r['registered_captial'] = res_customer['registered_capital'] + res_customer[
                        'registered_capital_currency']
                    r['paid_capital'] = res_customer['paid_capital'] + res_customer['paid_capital_currency']
                    r['insured_persons'] = res_customer['insured_persons']
            res_fdm = env['xlcrm.account.fd'].sudo().search_read(
                [('review_id', '=', r['id']), ('station_no', '=', 36)])
            r['factoring']=''
            if res_fdm:
                res_fdm = res_fdm[0]
                r['factoring'] = res_fdm['factoring_limit'] if res_fdm['factoring'] == '有' else res_fdm[
                    'factoring']
            res_lg = env['xlcrm.account.lg'].sudo().search_read([('review_id', '=', r['id'])])
            r['consignee']=''
            if res_lg:
                res_lg = res_lg[0]
                r['consignee'] = res_lg['consignee']
            res_pm = env['xlcrm.account.pm'].sudo().search_read([('review_id', '=', r['id'])],
                                                                fields=['brandname', 'profit', 'material_profit'])
            profit = []
            if res_pm:
                for res_ in res_pm:
                    if not res_['material_profit']:
                        profit.append({'material': res_['brandname'], 'profit': res_['profit']})
                    else:
                        profit += eval(res_['material_profit'])

            r['brand_profit'] = profit
            r['others']=''
            res_csvp = env['xlcrm.account.csvp'].sudo().search_read([('review_id', '=', r['id'])])
            if res_csvp:
                res_csvp = res_csvp[0]
                r['others'] = res_csvp['content']
            self.__get_signer_desc(r)

        return res

    def __get_signer_desc(self, r):
        try:
            import re
            com = re.compile(r'(.*?)\)')
            r['station_desc'] = r['station_desc'] if r['station_desc'] else ''
            res_desc = {value: key for key, value in self.get_stations_desc().items()}
            res_station = {value: key for key, value in self.get_staions().items()}
            desc = map(lambda x: f'{x})', com.findall(r['station_desc']))
            products = eval(r['products']) if r['products'] else []
            r['signer_desc'] = r['station_desc']
            for des in desc:
                r['signer_desc'] = ''
                _desc, signers = re.findall(r'(.*?)\(', des) + re.findall(r'\((.*?)\)', des)
                _station = res_desc[_desc]
                _station_des = res_station[_station]
                signer_ = signers
                if _station in range(20, 31):
                    signer_ = ''
                    for signer in signers.split(','):
                        brand_name = ','.join(
                            map(lambda x: x['brandname'], filter(lambda x: f'{signer}(' in x[_station_des], products)))
                        signer_ += f'{signer}-{brand_name}'
                r['signer_desc'] += f'{_desc}({signer_})'
        except Exception as e:
            raise repr(e)

    def get_cs(self, review_id, env):
        res_ = {"payment": "", "on_time": ""}
        res_customer = env['xlcrm.account.customer'].sudo().search_read(
            [('review_id', '=', review_id)])
        if res_customer:
            customer_ = res_customer[0]
            res_['registered_capital'] = customer_['registered_capital']
            res_['registered_capital_currency'] = customer_['registered_capital_currency']
            res_['paid_capital'] = customer_['paid_capital']
            res_['paid_capital_currency'] = customer_['paid_capital_currency']
            res_['insured_persons'] = customer_['insured_persons']
            res_['on_time'] = customer_['on_time']
            res_['overdue30'] = customer_['overdue30']
            res_['overdue60'] = customer_['overdue60']
            res_['overdue_others'] = customer_['overdue_others']
            res_['payment'] = customer_['payment']
            res_['payment_currency'] = customer_['payment_currency']
            res_['payment_account'] = customer_['payment_account']
            res_['salesment_currency'] = customer_['salesment_currency']
            res_['salesment_account'] = customer_['salesment_account']
            res_['stock'] = customer_['stock']
            res_['guarantee'] = customer_['guarantee']

        return res_

    def get_cs_new(self, review_id, env):
        res_ = dict()
        res_customer = env['xlcrm.account.cus'].sudo().search_read(
            [('review_id', '=', review_id)])
        if res_customer:
            customer_ = res_customer[0]
            res_['registered_capital'] = customer_['registered_capital'] if customer_['registered_capital'] else ''
            res_['registered_capital_currency'] = customer_['registered_capital_currency'] if customer_[
                'registered_capital_currency'] else ''
            res_['paid_capital'] = customer_['paid_capital'] if customer_['paid_capital'] else ''
            res_['paid_capital_currency'] = customer_['paid_capital_currency'] if customer_[
                'paid_capital_currency'] else ''
            res_['insured_persons'] = customer_['insured_persons'] if customer_['insured_persons'] else ''
            res_['on_time'] = customer_['on_time'] if customer_['on_time'] else ''
            res_['overdue30'] = customer_['overdue30'] if customer_['overdue30'] else ''
            res_['overdue60'] = customer_['overdue60'] if customer_['overdue60'] else ''
            res_['overdue_others'] = customer_['overdue_others'] if customer_['overdue_others'] else ''
            res_['payment'] = customer_['payment'] if customer_['payment'] else ''
            res_['payment_currency'] = customer_['payment_currency'] if customer_['payment_currency'] else ''
            res_['payment_account'] = customer_['payment_account'] if customer_['payment_account'] else ''
            res_['salesment_currency'] = customer_['salesment_currency'] if customer_['salesment_currency'] else ''
            res_['salesment_account'] = customer_['salesment_account'] if customer_['salesment_account'] else ''
            res_['stock'] = customer_['stock'] if customer_['stock'] else ''
            res_['guarantee'] = customer_['guarantee'] if customer_['guarantee'] else ''
            res_['listed_company'] = customer_['listed_company'] if customer_['listed_company'] else ''
            res_['trade_terms'] = customer_['trade_terms'] if customer_['trade_terms'] else ''
            res_['remark'] = customer_['remark'] if customer_['remark'] else ''
            res_his = env['xlcrm.account.cus.his'].sudo().search_read(
                [('review_id', '=', review_id)])
            his = []
            for _his in res_his:
                tmp = dict()
                tmp['a_company'] = _his['a_company'] if _his['a_company'] else ''
                tmp['salesment_account'] = _his['salesment_account'] if _his['salesment_account'] else ''
                tmp['salesment_currency'] = _his['salesment_currency'] if _his['salesment_currency'] else ''
                tmp['payment_account'] = _his['payment_account'] if _his['payment_account'] else ''
                tmp['payment_currency'] = _his['payment_currency'] if _his['payment_currency'] else ''
                his.append(tmp)
            res_['historys'] = his
        return res_

    def get_si_station(self, station_no, review_id, env):
        si_station = station_no
        if station_no == 28:
            _station = env['xlcrm.account.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc',
                limit=1)
            to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
            sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                'sign_station'] else []
            ne_station = list(set(to_station) - set(sign_station))
            ne_station.sort()
            for sta in ne_station:
                sta = int(sta)
                if sta in range(20, 31):
                    sig_ = self._get_partial_signer(env, review_id, sta)
                else:
                    sig = self._search_signers([('review_id', '=', review_id), ('station_no', '=', sta)], env)
                    sig_ = sig[0]['signers'].replace('[', '').replace(']', '').split(',')
                if str(env.uid) in sig_:
                    si_station = sta
                    break
        return si_station

    def get_products_sign(self, products, si_station, init_user, env):
        products_sign = products[:]
        if products:
            log_username = env['xlcrm.users'].sudo().search([('id', '=', env.uid)])
            log_username = log_username[0]['nickname'] + '(' + log_username[0]['username'].split('@')[
                0] + ')' if '@' in log_username[0]['username'] else log_username[0]['nickname'] + '(' + \
                                                                    log_username[0]['username'] + ')'
            pm_signer = list(map(lambda x: x.get('PM'), products))
            pur_signer = list(map(lambda x: x.get('PUR'), products))
            pmm_signer = list(map(lambda x: x.get('PMM'), products))
            pmins_signer = list(map(lambda x: x.get('PMins'), products))
            if log_username in pm_signer + pur_signer + pmm_signer + pmins_signer:
                le = len(products) - 1
                for i in range(len(products)):
                    if products[le - i].get('PM') != log_username and products[le - i].get(
                            'PUR') != log_username and products[le - i].get('PMM') != log_username and \
                            products[le - i].get('PMins') != log_username and init_user != env.uid:
                        products.pop(le - i)
                    if si_station == 20 and products_sign[le - i].get('PM') != log_username:
                        products_sign.pop(le - i)
                    if si_station == 21 and products_sign[le - i].get('PMins') != log_username:
                        products_sign.pop(le - i)
                    if si_station == 25 and products_sign[le - i].get('PUR') != log_username:
                        products_sign.pop(le - i)
                    if si_station == 30 and products_sign[le - i].get('PMM') != log_username:
                        products_sign.pop(le - i)
        return products_sign

    def get_current_account_period(self, obj_temp):
        current_account_period = []
        temp = {}
        temp['kc_company'] = obj_temp['a_company']
        temp['release_time'] = obj_temp['release_time'] if obj_temp['release_time'] else ''
        temp['payment_method'] = obj_temp['payment_method'] if obj_temp['payment_method'] else ''
        telegraphic_days = obj_temp['telegraphic_days'] if obj_temp['telegraphic_days'] else ''
        acceptance_days = obj_temp['acceptance_days'] if obj_temp[
            'acceptance_days'] else ''
        days = '' if temp['payment_method'] == '100%电汇' or not temp['payment_method'] else '天'
        temp['payment_method'] += telegraphic_days + acceptance_days + days
        temp['credit_limit_now'] = obj_temp['credit_limit_now'] if obj_temp[
            'credit_limit_now'] else ''
        current_account_period.append(temp)
        return current_account_period

    def get_detail_by_id(self, obj_temp, env, **kwargs):
        ret_temp = {
            "id": obj_temp["id"],
            "review_type": obj_temp["review_type"],
            "apply_user": obj_temp["apply_user"],
            "department": obj_temp["department"],
            "apply_date": obj_temp["apply_date"],
            "a_company": obj_temp["a_company"],
            "a_companycode": kwargs['companycode'],
            "kc_company": obj_temp["kc_company"],
            "ccusabbname": obj_temp["ccusabbname"],
            "ccuscode": obj_temp["ccuscode"] if obj_temp["ccuscode"] else '',
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
            "reconciliation_date": obj_temp["reconciliation_date"],
            "payment_date": obj_temp["payment_date"],
            "station_no": int(obj_temp["station_no"]),
            "status_id": obj_temp["status_id"],
            "nowStage": self.get_stations_desc(obj_temp["station_no"]),
            "account_attend_user_ids": obj_temp["account_attend_user_ids"],
            "signer": obj_temp['signer'],
            "loguser": env.uid,
            'from_station': kwargs['from_station'] if kwargs['from_station'] else obj_temp["station_no"],
            'si_station': int(kwargs['si_station']),
            'reviewers': self.literal_eval(obj_temp['reviewers']) if obj_temp['reviewers'] else {},
            'products': kwargs['products'],
            'remark': obj_temp['remark'] if obj_temp['remark'] else '',
            'products_sign': kwargs['products_sign'],
            'kehu': obj_temp['kehu'] if obj_temp['kehu'] else '',
            'unit': obj_temp['unit'] if obj_temp['unit'] else '',
            'release_time': obj_temp['release_time'] if obj_temp['release_time'] else '',
            'payment_method': obj_temp['payment_method'] if obj_temp['payment_method'] else '',
            'telegraphic_days': obj_temp['telegraphic_days'] if obj_temp['telegraphic_days'] else '',
            'release_time_apply': obj_temp['release_time_apply'] if obj_temp['release_time_apply'] else '',
            'release_time_applyM': obj_temp['release_time_applyM'] if obj_temp[
                'release_time_applyM'] else '',
            'release_time_applyO': obj_temp['release_time_applyO'] if obj_temp[
                'release_time_applyO'] else '',
            'payment_method_apply': obj_temp['payment_method_apply'] if obj_temp[
                'payment_method_apply'] else '',
            'acceptance_days_apply': obj_temp['acceptance_days_apply'] if obj_temp[
                'acceptance_days_apply'] else '',
            'acceptance_days': obj_temp['acceptance_days'] if obj_temp[
                'acceptance_days'] else '',
            'telegraphic_days_apply': obj_temp['telegraphic_days_apply'] if obj_temp[
                'telegraphic_days_apply'] else '',
            'others_apply': obj_temp['others_apply'] if obj_temp[
                'others_apply'] else '',
            'credit_limit': obj_temp['credit_limit'] if obj_temp[
                'credit_limit'] else '',
            'credit_limit_now': obj_temp['credit_limit_now'] if obj_temp[
                'credit_limit_now'] else '',
            'current_account_period': kwargs['current_account_period'],
            'cusdata': kwargs['cusdata'],
            'protocol_code': obj_temp['protocol_code'] if obj_temp[
                'protocol_code'] else '',
            'protocol_detail': obj_temp['protocol_detail'] if obj_temp[
                'protocol_detail'] else '',
            'cs': obj_temp['cs'],
            'affiliates': self.get_affiliates(obj_temp['id'], env),
            'payment': eval(obj_temp['payment']) if obj_temp['payment'] else [],
            'overdue': eval(obj_temp['overdue']) if obj_temp['overdue'] else [],
            're_payments': eval(obj_temp['re_payments']) if obj_temp['re_payments'] else [],
            're_overdues': eval(obj_temp['re_overdues']) if obj_temp['re_overdues'] else [],
            'overdue_arrears': obj_temp['overdue_arrears'],
            're_overdue_arrears': obj_temp['re_overdue_arrears'],
            'overdue_payment': obj_temp['overdue_payment'],
            're_overdue_payment': obj_temp['re_overdue_payment'],
            'end_recive_date': obj_temp['end_recive_date'],
            'end_date': obj_temp['end_date'],
            'latest_receipt_date': obj_temp['latest_receipt_date'],
            'receipt_confirmer': obj_temp['receipt_confirmer'],
            'release_time_apply_new': obj_temp['release_time_apply_new'],
            'release_time_apply_remark': obj_temp['release_time_apply_remark'],
            'account_type': obj_temp['account_type'],
            'wire_apply_per': obj_temp['wire_apply_per'],
            'wire_apply_type': obj_temp['wire_apply_type'],
            'wire_apply_days': obj_temp['wire_apply_days'],
            'days_apply_type': obj_temp['days_apply_type'],
            'days_apply_days': obj_temp['days_apply_days'],
            'payment_method_apply_new': obj_temp['payment_method_apply_new']
        }
        return ret_temp

    @staticmethod
    def get_affiliates(review_id, env):
        results = env['xlcrm.account.affiliates'].sudo().search_read([('account', '=', review_id)])

        return results

    def get_partial_signer(self, to_station, to_brand, review_id, env):
        signer, station_desc = [], ''
        signers = self._search_signers([('review_id', '=', review_id)], env)
        to_station = to_station.split(',')
        to_station.remove('')
        for station in to_station:
            station = int(station)
            si = list(filter(lambda x: x['station_no'] == station, signers))[0]
            sig = si['signers'].replace('[', '').replace(']', '').split(',')
            sig_ = sig
            if to_brand.get(station):
                sig_ = []
                brand_name = to_brand.get(station).split(',')
                sys_names = si['brandname'].split(',')
                brand_name.remove('')
                # brand_names.remove('')
                for brand in brand_name:
                    index = sys_names.index(brand)
                    sig_.append(sig[index])

            signer += sig_
            station_desc += '%s(%s)' % (
                self.get_stations_desc(station), self._get_user_nickname([('id', 'in', sig_)], 'nickname', env, True))
        return ',' + ','.join(signer) + ',', station_desc

    def update_current_signer(self, env):
        try:
            next_signer, station_desc = '', ''
            res = env['xlcrm.account'].sudo().search_read(
                [('status_id', '=', 1)])
            for re in res:
                station_no = re['station_no']
                review_id = re['id']

                if station_no == 28:
                    sign_back = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    if sign_back and sign_back[0]['sign_over'] == 'N':
                        signed_station = set(sign_back[0]['sign_station'].split(',')) if sign_back[0][
                            'sign_station'] else set()
                        to_station = set(sign_back[0]['to_station'].split(','))
                        ne_station = tuple(to_station - signed_station)
                        tar_set = {'20', '21', '25', '30'}
                        common_station = tuple(set(ne_station) - tar_set)
                        next_signer, station_desc = self._get_common_signer(review_id, common_station, env)
                        for ne in set(ne_station) & tar_set:
                            next_signer_tmp = []
                            backs = env['xlcrm.account.partial.sec'].sudo().search_read(
                                [('review_id', '=', review_id), ('station_no', '=', ne)],
                                order='init_time desc', limit=1)
                            if backs[0]['sign_over'] == 'N':
                                to_brand = backs[0]['to_brand'].split(',') if backs[0]['to_brand'] else {}
                                sign_brand = backs[0]['sign_brand'].split(',') if backs[0]['sign_brand'] else {}
                                ne_brands = set(to_brand) - set(sign_brand)
                                ne_brands.remove('')
                                sig = self._search_signers([('review_id', '=', review_id), ('station_no', '=', ne)],
                                                           env)
                                for tar_brand in ne_brands:
                                    uid_index = self._compute_partial_singer(tar_brand, sig[0]['brandname'].split(','))
                                    next_signer_tmp.append(sig[0]['signers'].split(',')[uid_index])
                            next_signer += next_signer_tmp
                            station_desc += '%s(%s)' % (self.get_stations_desc(ne),
                                                        self._get_user_nickname([('id', 'in', next_signer_tmp)],
                                                                                'nickname', env, True))
                        # next_signer = ','.join(next_signer)
                        station_desc += '-回签'
                elif station_no in range(20, 46):
                    signer_ = self._search_signers(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)], env)
                    if station_no == 45:
                        signer_tmp = signer_[0]['signers'].split('],')
                        next_signer = signer_tmp[0]
                        if len(signer_tmp) > 1:
                            risk_res = env['xlcrm.account.risk'].sudo().search_read(
                                [('review_id', '=', review_id), ('init_user', '=', signer_tmp[-1])])
                            if risk_res:
                                next_signer = signer_tmp[-1]
                        next_signer = next_signer.replace('[', '').replace(']', '').split(',')
                        station_desc = '%s(%s)' % (self.get_stations_desc(station_no),
                                                   self._get_user_nickname([('id', 'in', next_signer)],
                                                                           'nickname', env, True))
                    elif station_no < 35:
                        if signer_:
                            if signer_[0]['sign_over'] == 'N':
                                signed = set(signer_[0]['signed'].split(',')) if signer_[0]['signed'] else set()
                                signers = set(signer_[0]['signers'].split(','))
                                next_signer = ','.join(signers - signed)
                                next_signer = next_signer.replace('[', '').replace(']', '').split(',')
                                station_desc = '%s(%s)' % (self.get_stations_desc(station_no),
                                                           self._get_user_nickname([('id', 'in', next_signer)],
                                                                                   'nickname', env,
                                                                                   True))
                    else:
                        next_signer = signer_[0]['signers'] if signer_ else ''
                        next_signer = next_signer.replace('[', '').replace(']', '').split(',') if next_signer else []
                        station_desc = '%s(%s)' % (self.get_stations_desc(station_no),
                                                   self._get_user_nickname([('id', 'in', next_signer)], 'nickname',
                                                                           env, True))
                else:
                    next_signer = self._search_signers(
                        ['&', ('review_id', '=', review_id), ('station_no', '=', station_no)], env)
                    next_signer = next_signer[0]['signers'] if next_signer else ''
                    next_signer = next_signer.replace('[', '').replace(']', '').split(',') if next_signer else []
                    station_desc = '%s(%s)' % (self.get_stations_desc(station_no),
                                               self._get_user_nickname([('id', 'in', next_signer)], 'nickname', env,
                                                                       True))
                if next_signer:
                    next_signer = ',' + ','.join(next_signer) + ','
                    self.update('xlcrm.account', review_id, {'signer': next_signer, 'station_desc': station_desc}, env)
        except Exception as e:
            raise Exception(repr(e))

    @staticmethod
    def update_pm_profit(result, look_profit, env):
        for res in result:
            if env.uid in res['signer_id']:
                look_profit = True
            res['profit'] = '' if not look_profit else res['profit']
            res['look_profit'] = look_profit

    @staticmethod
    def _get_pm_profit(res_tmp, env):
        for res_ in res_tmp:
            res_['material_profit'] = env['xlcrm.material.profit'].sudo().search_read([('pm_id', '=', res_['id'])],
                                                                                      fields=['material', 'profit',
                                                                                              'compliance'])
            # if res_['profit']:
            #     res_['material_profit'] = [{'material': '', 'profit': res_['profit']}]
            # elif res_['material_profit']:
            #     res_['material_profit'] = eval(res_['material_profit'])

    @staticmethod
    def _get_sign_brand_name(products):
        for index, product in enumerate(products):
            product['sign_brand_name'] = '%s_index%d' % (product['brandname'], index)

    @staticmethod
    def insert_brandnamed_toU8(res):
        try:
            ccustype = res['a_company']
            company_res = request.env['xlcrm.user.ccfnotice'].sudo().search_read([('a_company', '=', ccustype)])
            companycode = company_res[0]['a_companycode'] if company_res else ''
            ccuscode = res['ccuscode']
            ccusname = res['kc_company']
            products = eval(res['products']) if res['products'] else []
            data = []
            from . import connect_mssql
            mssql = connect_mssql.Mssql('sales_')
            mssql.in_up_de(
                "delete from ccf_brandnamed where companycode='%s' and ccuscode='%s'" % (companycode, ccuscode))
            for item in products:
                brandname = item.get('brandname') if item.get('brandname') else ''
                material = item.get('material') if item.get('material') else ''
                if material:
                    for mat in material:
                        data.append((ccustype, companycode, ccuscode, ccusname, brandname, mat))
                else:
                    data.append((ccustype, companycode, ccuscode, ccusname, brandname, ''))

            mssql.batch_in_up_de(
                [[
                    "insert into ccf_brandnamed(ccustype,companycode,ccuscode,ccusname,brandname,material_no)values(%s,%s,%s,%s,%s,%s)",
                    data]])
            mssql.commit()
            mssql.close()
        except Exception as e:
            print('=======', e)

    @staticmethod
    def insert_brandlimit_toU8(review_id, env):
        res = env['xlcrm.account'].sudo().browse(review_id)
        doc = env['xlcrm.documents'].sudo().search(
            [('res_id', '=', review_id), ('res_model', '=', 'xlcrm.account'), ('description', '!=', '')])
        ccuscode = res.ccuscode
        company_res = env['xlcrm.user.ccfnotice'].sudo().search([('a_company', '=', res.a_company)],
                                                                order='write_date desc')
        if ccuscode and company_res and res.status_id == 3:
            editor = res.init_user.nickname
            editdate = res.update_time
            pm_res = env['xlcrm.account.pm'].sudo().search([('review_id', '=', res['id'])])
            for p_res in pm_res:
                if p_res and pm_res.compliance == '是':
                    from . import connect_mssql
                    brand_name, init_user, init_time = p_res.brandname.split('_index')[0].replace('amp;', '&').replace(
                        'eq;', '=').replace('plus;', '+').replace('per;',
                                                                  '%'), p_res.init_user.nickname, p_res.init_time
                    auditer, auditdate = init_user if doc else '', datetime.datetime.strftime(doc[0].write_date,
                                                                                              '%Y-%m-%d') if doc else ''
                    con_str = '154_999' if odoo.tools.config["enviroment"] == 'PRODUCT' else '158_999'
                    mssql = connect_mssql.Mssql(con_str)
                    data = []
                    mssql.in_up_de(
                        f"delete from EF_BrandLimit where companyCode='{company_res[0].a_companycode}' and cCusCode='{ccuscode}' and cBrand='{brand_name}'")
                    mssql.in_up_de(
                        "insert into EF_BrandLimit(companyCode,cCusCode,cBrand,cEditor,cEditDate,cAuditer,cAuditDate)"
                        f"values('{company_res[0].a_companycode}','{ccuscode}','{brand_name}','{editor}','{datetime.datetime.strftime(editdate, '%Y-%m-%d')}','{init_user}','{datetime.datetime.strftime(editdate, '%Y-%m-%d')}')")
                    if pm_res.compliance_material == '是':
                        material = env['xlcrm.material.profit'].sudo().search_read(
                            [('pm_id', '=', p_res.id), ('compliance', '=', '是')], fields=['material', 'init_time'])
                        for item in material:
                            material = item.get('material').replace('amp;', '&').replace('eq;', '=').replace('plus;',
                                                                                                             '+').replace(
                                'per;', '%')
                            start_date = datetime.datetime.strftime(editdate, '%Y-%m-%d')
                            end_date = datetime.datetime.strftime(editdate.replace(year=editdate.year + 99), '%Y-%m-%d')
                            doc_material = list(filter(lambda x: material in x.description.split('，'), doc))
                            auditer, auditdate = auditer if doc_material else '', doc_material[
                                0].write_date if doc_material else ''
                            if material:
                                data.append((company_res[0].a_companycode, ccuscode, material,
                                             start_date, end_date, editor,
                                             start_date, auditer,
                                             datetime.datetime.strftime(auditdate, '%Y-%m-%d') if auditdate else ''))

                    mssql.batch_in_up_de(
                        [["delete from EF_InvPermit where companyCode=%s and cCusCode=%s and cInvCode=%s",
                          list(map(lambda x: (x[0], x[1], x[2]), data))], [
                             "insert into EF_InvPermit(companyCode,cCusCode,cInvCode,cStartDate,cEndDate,cEditor,cEditDate,cAuditer,cAuditDate)values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                             data]])
                    mssql.commit()
                    mssql.close()
