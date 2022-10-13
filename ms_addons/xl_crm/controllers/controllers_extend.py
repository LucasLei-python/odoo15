# -*- coding: utf-8 -*-
from odoo import http, api, registry
from odoo import tools
from ..public import public as p, connect_mssql as con

from .controllers_base import Base
import datetime


class XlCrmExtend(http.Controller, Base):
    @http.route([
        '/api/v11/changeProjectManage',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def change_project_manage(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            mul_id = data['mul_selects']
            users = data['user']
            res = env['xlcrm.project'].sudo().search_read([('id', 'in', mul_id)])
            for re in res:
                update_data = {}
                reviewers = eval(re['reviewers'])
                project_attend_user_ids = re['project_attend_user_ids']
                if re['create_user_id'][0] in project_attend_user_ids:
                    project_attend_user_ids.remove(re['create_user_id'][0])
                if reviewers['Manage']:
                    for man in reviewers['Manage']:
                        if man in project_attend_user_ids:
                            project_attend_user_ids.remove(man)
                update_data['project_attend_user_ids'] = [[6, 0, project_attend_user_ids + users]]
                reviewers['Manage'] = users
                update_data['reviewers'] = reviewers
                env['xlcrm.project'].sudo().browse(re['id']).write(update_data)
            env.cr.commit()
            success, message = True, '更新成功'
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
            return self.json_response({'status': 200, 'success': success, 'message': message})

    @http.route([
        '/api/v11/changeManage',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def change_customer_manage(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            mul_id = data['mul_selects']
            users = data['user']
            update_data = {}
            res = env['xlcrm.customer'].sudo().search_read([('id', 'in', mul_id)])
            for re in res:
                update_data['create_user_id'] = users
                update_data['create_user_old'] = re['create_user_id'][0]
                env['xlcrm.customer'].sudo().browse(re['id']).write(update_data)
            env.cr.commit()
            success, message = True, '更新成功'
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
            return self.json_response({'status': 200, 'success': success, 'message': message})

    @http.route([
        '/api/v11/getOverdue',
    ], auth='none', type='http', csrf=False, methods=['GET','POST'])
    def get_overdue(self, model=None, success=True, message='', **kw):
        success, message, re_overdue, overdue, overdue_arrears, re_overdue_arrears = True, '', [], [], '无', '无'
        token = kw.pop('token')
        data = self.literal_eval(
            list(kw.keys())[0].replace('null', '""')).get("data")
        public = p.Public()
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            mssql = connect_mssql.Mssql('stock')
            cus = data.get('cus')
            re_cus = data.get('re_cus') if data.get('re_cus') else []
            re_cus.append(cus)
            review_id = data.get('review_id')
            # 计算超期欠款
            overdues = public.get_overdue(re_cus, mssql)
            for item in overdues:
                if item['ccusName'] == cus['name']:
                    overdue = item['data']
                else:
                    re_overdue.append(item)
            overdue_arrears = '有' if len(overdue) > 0 else '无'
            re_overdue_arrears = '有' if len(re_overdue) > 0 else '无'
            if review_id:
                env['xlcrm.account'].sudo().browse(review_id).write({
                    "overdue": overdue,
                    "re_overdues": re_overdue,
                    "overdue_arrears": overdue_arrears,
                    "re_overdue_arrears": re_overdue_arrears
                })
                env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
            return self.json_response({'status': 200, 'overdue': overdue, "re_overdues": re_overdue,
                                       "overdue_arrears": overdue_arrears, "re_overdue_arrears": re_overdue_arrears,
                                       'success': success, 'message': message})

    @http.route([
        '/api/v11/getPayment',
    ], auth='none', type='http', csrf=False, methods=['GET','POST'])
    def get_payment(self, model=None, success=True, message='', **kw):
        success, message, re_payment, payment, overdue_payment, re_overdue_payment = True, '', [], [], '无', '无'
        token = kw.pop('token')
        data = self.literal_eval(
            list(kw.keys())[0].replace('null', '""')).get("data")
        public = p.Public()
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            mssql = connect_mssql.Mssql('stock')
            cus = data.get('cus')
            re_cus = data.get('re_cus') if data.get('re_cus') else []
            re_cus.append(cus)
            review_id = data.get('review_id')
            # 计算超期欠款
            payment, re_payment = [], []
            payments = public.get_payment(re_cus, mssql)
            for item in payments:
                if item['ccusName'] == cus['name']:
                    payment = item['data']
                else:
                    re_payment.append(item)
            overdue_payment = '有' if len(payment) > 0 else '无'
            re_overdue_payment = '有' if len(re_payment) > 0 else '无'
            if review_id:
                env['xlcrm.account'].sudo().browse(review_id).write({
                    "payment": payment,
                    "re_payments": re_payment,
                    "overdue_payment": overdue_payment,
                    "re_overdue_payment": re_overdue_payment
                })
                env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
            return self.json_response(
                {'status': 200, 'overdue_payment': overdue_payment, 're_overdue_payment': re_overdue_payment,
                 'payment': payment, 're_payments': re_payment, 'success': success, 'message': message})

    @http.route([
        '/api/v11/getLastLog',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_last_log(self, model=None, success=True, message='', **kw):
        success, message, content = True, '', []
        token = kw.pop('token')
        _ID = kw.get('id')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            res = env['xlcrm.project.remark'].sudo().search_read([('project_id', '=', int(_ID))],
                                                                 order='update_time desc', limit=2)
            if res:
                content = res
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
            return self.json_response(
                {'status': 200, 'content': content, 'success': success, 'message': message})

    @http.route([
        '/api/v10/unlink/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def unlink_objects_10(self, model=None, ids=None, success=True, message='', **kw):
        token = kw.pop('token')
        env = self.authenticate(token)
        ids = self.literal_eval(list(kw.keys())[0]).get("ids")
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        # ids = map(int,ids.split(','))
        try:
            result = env[model].sudo().browse(ids).unlink()
            env.cr.commit()
            message = "操作成功！"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result, 'success': success, 'message': message}
        return self.json_response(rp)

    @http.route([
        '/api/v10/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_objects_10(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        import smtplib
        if not env:
            return self.no_token()
        try:
            data["create_user_id"] = env.uid
            create_id = env[model].sudo().create(data).id
            result_object = env[model].sudo().search_read([('id', '=', create_id)])[0]
            model_fields = env[model].fields_get()
            for f in result_object.keys():
                if model_fields[f]['type'] == 'many2one':
                    if result_object[f]:
                        result_object[f] = {'id': result_object[f][0], 'display_name': result_object[f][1]}
                    else:
                        result_object[f] = ''
            if model == "xlcrm.project":
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
            if model == "xlcrm.customer":
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
            if model == "xlcrm.visit":
                operation_log = {
                    'name': '新增客户拜访：' + result_object['title'],
                    'operator_user_id': env.uid,
                    'content': '新增客户拜访：' + result_object['title'],
                    'res_id': result_object['id'],
                    'res_model': 'xlcrm.visit',
                    'res_id_related': result_object['customer_id']['id'],
                    'res_model_related': 'xlcrm.customer',
                    'operation_level': 0,
                    'operation_type': 0
                }
                env["xlcrm.operation.log"].sudo().create(operation_log)
                user = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])[0]
                if not user['email']:
                    rp = {'status': 200, 'data': '', 'message': '您的邮箱地址为空，请联系系统管理员维护您的邮箱地址', 'success': False}
                    return self.json_response(rp)
                if not user['email_password']:
                    rp = {'status': 200, 'data': '', 'message': '邮箱密码为空', 'success': False}
                    return self.json_response(rp)
                result_file = env['xlcrm.documents'].sudo().search_read(
                    [('res_id', '=', create_id), ('res_model', '=', 'xlcrm.visit')])
                res_data = []
                import odoo
                for res in result_file:
                    res_tmp = {'id': res['id'],
                               'name': res['datas_fname'],
                               'url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                   res['id'])
                               }
                    res_data.append(res_tmp)
                result_object['filelist'] = res_data
            env.cr.commit()
            success = True
            message = "新增成功！"
        except smtplib.SMTPAuthenticationError as e:
            result_object, success, message = '', False, '邮箱密码错误'
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v10/<string:model>',
        '/api/v10/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def read_objects_10(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 80
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        domain = eval(kw.get('filter', "[]"))
        fields = eval(kw.get('fields', "[]"))
        offset = int(kw.get('page_no', '1')) - 1
        limit = int(kw.get('page_size', '25'))
        order = kw.get('order', 'id desc')

        if kw.get("data"):
            queryFilter = self.literal_eval(kw.get("data"))
            if queryFilter and queryFilter.get("status"):
                domain.append(('status', '=', queryFilter.get("status")))
            if queryFilter and queryFilter.get("order_field"):
                order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

        if len(domain) == 0:
            domain = [('write_uid', '=', 1)]
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:
            count = env[model].sudo().search_count(domain)
            result = env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            model_fields = env[model].fields_get()
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
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return self.json_response(rp)

    @http.route([
        '/api/v10/update/<string:model>',
        '/api/v10/update/<string:model>/<string:ids>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def update_objects(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        # ids = map(int, ids.split(','))
        try:
            obj_id = data["id"]
            data["write_user_id"] = env.uid
            result = env[model].sudo().browse(obj_id).write(data)
            env.cr.commit()
            if result:
                ret_object = env[model].sudo().search_read([('id', '=', obj_id)])[0]
                model_fields = env[model].fields_get()
                for f in ret_object.keys():
                    if model_fields[f]['type'] == 'many2one':
                        if ret_object[f]:
                            ret_object[f] = {'id': ret_object[f][0], 'display_name': ret_object[f][1]}
                        else:
                            ret_object[f] = ''

                message = "success"
                success = True
        except Exception as e:
            ret_object, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': ret_object, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/getAccountToOA',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_to_oa(self, model=None, success=True, message='', **kw):
        success, message, data = True, '', []
        token, types = kw.pop('token'), kw.pop('types')
        if token != tools.config['api_key']:
            return self.json_response({'status': 200, 'data': data, 'success': False, 'message': 'token错误'})
        try:
            db = tools.config['db_name']
            cr = registry(db).cursor()
            env = api.Environment(cr, '', {})
            res = env['xlcrm.account'].sudo().search([('status_id', '=', 3)])
            data_account, data_payment, data_profit = '<tb_account>', '<tb_payment>', '<tb_profit>'
            for _res in res:
                tmp, tmp_payment, tmp_profit = '', '', ''
                if types == 'account':
                    tmp += f'<row>'
                    tmp += f'<id>{_res.id}</id>'
                    sales = env['xlcrm.account.sales'].sudo().search([('review_id', '=', _res.id)], limit=1)
                    tmp += f'<apply_user>{_res.apply_user}</apply_user>'
                    tmp += f'<department>{_res.department}</department>'
                    tmp += f'<kc_company>{_res.kc_company}</kc_company>'
                    tmp += f'<sales_nickname>{sales.init_user.nickname}</sales_nickname>'
                    tmp += f'<sales_dept>{sales.init_user.department_id.name}</sales_dept>'
                    tmp += f'<currency>{_res.currency}</currency>'
                    tmp += f"<status>{'未建档' if _res.kehu == '新客户' else '已建档'}</status>"
                    tmp += f"<account>{_res.release_time_apply}</account>"
                    payment = ''
                    if _res.release_time_apply:
                        payment = _res.release_time_apply.replace('amp;', '&').replace('eq;', '='). \
                            replace('plus;', '+').replace('per;', '%')
                        if _res.acceptance_days_apply or _res.telegraphic_days_apply:
                            payment += _res.acceptance_days_apply + _res.telegraphic_days_apply + '天'
                        else:
                            payment += _res.others_apply if _res.others_apply else ''
                    elif _res.release_time_apply_new:
                        payment = _res.release_time_apply_new.replace('amp;', '&').replace('eq;', '='). \
                            replace('plus;', '+').replace('per;', '%')
                        if _res.wire_apply_type:
                            payment += _res.wire_apply_type + str(_res.wire_apply_days) + '天'
                        elif _res.days_apply_type:
                            payment += _res.days_apply_type + str(_res.days_apply_days) + '天'
                        else:
                            payment += _res.others_apply
                    tmp += f"<payment>{payment}</payment>"
                payment_status = ''
                cs = eval(_res.cs) if _res.cs else ''
                if cs:
                    payment_status = cs.get('on_time')
                    his = cs.get('historys', [])
                    if types == 'payment':
                        for item in his:
                            if item:
                                tmp_payment += f"<row><a_id>{_res.id}</a_id>" \
                                               f"<account>{item.get('a_company', _res.a_company)}</account>" \
                                               f"<payment>{str(item.get('payment_account', '')) + item.get('payment_currency', '')}</payment></row>"
                tmp += f"<payment_status>{payment_status}</payment_status>"
                pm = env['xlcrm.account.pm'].sudo().search([('review_id', '=', _res.id)])
                brandname = ''
                for _pm in pm:
                    brandname_ = _pm.brandname.split('_index')[0] if _pm.brandname else ''
                    brandname = brandname + ',' + brandname_ if brandname else brandname_
                    if types == 'profit':
                        mater_profit = env['xlcrm.material.profit'].sudo().search([('pm_id', '=', _pm.id)])
                        for m_p in mater_profit:
                            tmp_profit += f"<row><a_id>{_res.id}</a_id><brandname>{brandname_}</brandname>" \
                                          f"<material>{m_p.material}</material><profit>{m_p.profit}</profit></row>"
                tmp += f"<brandname>{brandname}</brandname>"
                data_account += tmp + '</row>'
                data_payment += tmp_payment
                data_profit += tmp_profit
            if types == 'account':
                data = data_account
            elif types == 'payment':
                data = data_payment
            else:
                data = data_profit
            data = f"<root>{data}</tb_{types}></root>"
            # data = f"<root>{data_account}</tb_account>{data_profit}</tb_profit></root>"
            env.cr.close()
            # data = json_to_xml('root', data)
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.xml_response(data)

    @http.route([
        '/api/v11/getCusList',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_cus_list(self, model=None, success=True, message='', **kw):
        success, message, result, company, count, offset, limit = True, '', [], [], 0, 0, 5000
        try:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            if kw.get("data"):
                query_filter = self.literal_eval(kw.get("data"))
                offset = query_filter.pop("page_no") - 1
                limit = query_filter.pop("page_size")
                db_str = '161' if tools.config['enviroment'] == 'PRODUCT' else '168'
                pgsql = con.Mssql(db_str)
                query, query_company = '', ''
                user = env['xlcrm.users'].sudo().search([('id', '=', env.uid)])
                if user:
                    sign_power = 1
                    if query_filter.get('a_company'):
                        query_company = f" and a.a_company='{query_filter.get('a_company')}'"
                    if user.group_id.name != 'Manager':
                        header = pgsql.query(f"select name from person_header_u8 where header='{user.nickname}'")
                        if header:
                            tmp_query = f" and a.cpersonname in {tuple(map(lambda x: x[0], header))}"
                        else:
                            sign_power = 0
                            tmp_query = f" and a.cpersonname='{user.nickname}'"
                        power_res = pgsql.query(
                            f"select distinct a.caccode from person_from_u8 a where 1=1 {tmp_query}{query}")
                        if power_res:
                            power = list(map(lambda x: x[0], power_res))
                            query += f" and privilege_id in {tuple(power)}"
                    if query_filter.get('status') in (0, 1, 2, 3, 4):
                        query += f' and COALESCE (b.status, 0)={query_filter.get("status")}'

                    if query_filter.get('ccusname'):
                        query += f" and ccusname like '%{query_filter.get('ccusname')}%'"

                    if query_filter.get('cdepname'):
                        query += f" and cdepname like '%{query_filter.get('cdepname')}%'"

                    if query_filter.get('cpersonname'):
                        query += f" and cpersonname like '%{query_filter.get('cpersonname')}%'"

                    base_sql = f"select distinct a.a_company,a.ccuscode,a.ccusname,a.ccusdefine7,a.ccdefine3,COALESCE(b.ccusmnemcode, a.ccusmnemcode),a.cdepname,a.cpersonname," \
                               f"COALESCE (b.status, 0) as status from cus_from_u8 a left join u8_cus_synchronize b on a.a_company=b.a_company and a.ccuscode=b.code where 1=1 "
                    res = pgsql.query(
                        f"{base_sql}{query_company}{query} order by a.ccuscode offset {offset * limit} limit {limit}")
                    # print(f"{base_sql}{query_company}{query} order by a.ccuscode offset {offset * limit} limit {limit}")
                    for item in res:
                        # belong = True
                        # if res[9] and res[9] != user.nickname:
                        #     belong = False
                        result.append(
                            {'a_company': item[0], 'ccuscode': item[1], 'ccusname': item[2], 'ccusdefine7': item[3]
                                , 'ccdefine3': item[4], 'ccusmnemcode': item[5], 'sales_dept': item[6],
                             'spec_operator': item[7], 'status': item[8], 'sign_power': sign_power})
                    res_count = pgsql.query(f"select count(1) from ({base_sql}{query_company}{query}) a")
                    count = res_count[0][0] if res_count else 0
                    company = list(
                        map(lambda x: x[0], pgsql.query(f'select distinct a_company from ({base_sql}) a')))

                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'company': company, 'total': count,
              'page': offset + 1,
              'per_page': limit}
        return self.json_response(rp)

    @http.route([
        '/api/v11/setCusItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def set_cus_item(self, model=None, success=True, message='', **kw):
        success, message = True, ''
        try:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            data = self.literal_eval(list(kw.keys())[0].replace('null', "''").replace('false', "''")).get("data")
            a_company = data.get('a_company')
            code = data.get('ccuscode')
            name = data.get('ccusname')
            abbrname = data.get('ccusabbname')
            ccusdefine7 = data.get('ccusdefine7')
            ccusdefine3 = data.get('ccusdefine3')
            ccusmnemcode = data.get('ccusmnemcode')
            status = data.get("status")
            nickname = env['xlcrm.users'].sudo().search([('id', '=', env.uid)], limit=1).nickname
            for company in (a_company, '999'):
                res = env['u8.cus.synchronize'].sudo().search(
                    [('a_company', '=', company), ('code', '=', code), ('status', '<', 5)])
                if not res or (res.status == 4 and company != '999'):
                    save_time, save_user = datetime.datetime.now(), nickname
                    if res.status == 4 and company != '999':
                        res.status = 5
                    env['u8.cus.synchronize'].sudo().create({'a_company': company, 'code': code,
                                                             'name': name, 'abbrname': abbrname,
                                                             'ccusdefine7': ccusdefine7, 'ccusdefine3': ccusdefine3,
                                                             'ccusmnemcode': ccusmnemcode, 'status': status,
                                                             'save_time': save_time, 'save_user': save_user})
                else:
                    save_time, save_user = datetime.datetime.now(), nickname
                    write_data = {'a_company': company, 'code': code,
                                  'name': name, 'abbrname': abbrname,
                                  'ccusdefine7': ccusdefine7, 'ccusdefine3': ccusdefine3,
                                  'ccusmnemcode': ccusmnemcode, 'status': status, 'save_time': save_time,
                                  'save_user': save_user}
                    if status == 3:
                        write_data.pop('save_time')
                        write_data.pop('save_user')
                        write_data['approval_time'], write_data['approval_user'] = datetime.datetime.now(), env.uid
                    res.write(write_data)
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/setCusConsolidatedItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def set_cus_item(self, model=None, success=True, message='', **kw):
        success, message = True, ''
        try:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            data = self.literal_eval(list(kw.keys())[0].replace('null', "''").replace('false', "''")).get("data")
            res = env['u8.cus.consolidated'].sudo().search([('id', '=', data.get("id"))])
            res.brand_limit = data.get("brand_limit")
            res.status = data.get("status")
            brand_res = env['u8.cus.consolidated.brand'].sudo().search([("cus_con_id", "=", data.get("id"))])
            for brand in brand_res:
                env['u8.cus.consolidated.material'].sudo().search([("brand_con_id", "=", brand.id)]).unlink()
                brand.unlink()
            for b_d in data.get("brandData"):
                b_d["cus_con_id"] = data.get("id")
                b_d["init_user"] = env.uid
                b_id = env['u8.cus.consolidated.brand'].sudo().create(b_d).id
                material = b_d.get("material")
                if material:
                    material_data = list(map(lambda x: {"brand_con_id": b_id, "material_limit": x}, material))
                    env['u8.cus.consolidated.material'].sudo().create(material_data)
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/batchSetCusItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def batch_set_cus_item(self, model=None, success=True, message='', **kw):
        success, message = True, ''
        try:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            data = self.literal_eval(
                list(kw.keys())[0].replace('null', "''").replace('false', "''").replace('true', "''")).get("data")
            status = 2 if data.get('action') == 'save' else 3
            nickname = env['xlcrm.users'].sudo().search([('id', '=', env.uid)], limit=1).nickname
            for item in data.get('data'):
                a_company = item.get('a_company')
                code = item.get('ccuscode')
                name = item.get('ccusname')
                abbrname = item.get('ccusabbname')
                ccusdefine7 = item.get('ccusdefine7')
                ccusdefine3 = item.get('ccusdefine3')
                ccusmnemcode = item.get('ccusmnemcode')
                for company in (a_company, '999'):
                    res = env['u8.cus.synchronize'].sudo().search(
                        [('a_company', '=', company), ('code', '=', code), ('status', '<', 5)])
                    if not res or (res.status == 4 and company != '999'):
                        save_time, save_user = datetime.datetime.now(), nickname
                        if res.status == 4 and company != '999':
                            res.status = 5
                        env['u8.cus.synchronize'].sudo().create({'a_company': company, 'code': code,
                                                                 'name': name, 'abbrname': abbrname,
                                                                 'ccusdefine7': ccusdefine7, 'ccusdefine3': ccusdefine3,
                                                                 'ccusmnemcode': ccusmnemcode, 'status': status,
                                                                 'save_time': save_time, 'save_user': save_user})
                    else:
                        save_time, save_user = datetime.datetime.now(), nickname
                        write_data = {'a_company': company, 'code': code,
                                      'name': name, 'abbrname': abbrname,
                                      'ccusdefine7': ccusdefine7, 'ccusdefine3': ccusdefine3,
                                      'ccusmnemcode': ccusmnemcode, 'status': status, 'save_time': save_time,
                                      'save_user': save_user}
                        if status == 3:
                            write_data.pop('save_time')
                            write_data.pop('save_user')
                            write_data['approval_time'], write_data['approval_user'] = datetime.datetime.now(), nickname
                        res.write(write_data)
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/getConsolidated',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_consolidated(self, model=None, success=True, message='', **kw):
        success, message, result, company, count, offset, limit = True, '', [], [], 0, 0, 5000
        try:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            if kw.get("data"):
                query_filter = self.literal_eval(kw.get("data"))
                offset = query_filter.pop("page_no") - 1
                limit = query_filter.pop("page_size")
                domain = []
                if query_filter.get("source"):
                    domain.append(("source", "=", query_filter.get("source")))
                if query_filter.get("name"):
                    domain.append(("name", "ilike", query_filter.get("name")))
                if query_filter.get("status") != "":
                    domain.append(("status", "=", query_filter.get("status")))
                result = env['u8.cus.consolidated'].sudo().search_read(domain, offset=offset * limit, limit=limit)
                for res in result:
                    res['brandData'] = list()
                    res_brand = env['u8.cus.consolidated.brand'].sudo().search(
                        [('cus_con_id', '=', res["id"])])
                    for brand in res_brand:
                        tmp = dict()
                        tmp['brand_name'] = brand.brand_name
                        tmp['pm'] = brand.pm
                        material_limit = env["u8.cus.consolidated.material"].sudo().search_read(
                            [("brand_con_id", "=", brand.id)], fields=["material_limit"])
                        tmp['material'] = list(map(lambda x: x["material_limit"], material_limit))
                        res['brandData'].append(tmp)
                count = env['u8.cus.consolidated'].sudo().search_count(domain)
                message = "success"
                success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'company': company, 'total': count,
              'page': offset + 1,
              'per_page': limit}
        return self.json_response(rp)
