# -*- coding: utf-8 -*-
from odoo import http
from .public import *
from .controllers_base import Base


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
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_overdue(self, model=None, success=True, message='', **kw):
        success, message, re_overdue, overdue, overdue_arrears, re_overdue_arrears = True, '', [], [], '无', '无'
        token = kw.pop('token')
        data = self.literal_eval(kw.get('data'))
        public = Public()
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from . import connect_mssql
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
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_payment(self, model=None, success=True, message='', **kw):
        success, message, re_payment, payment, overdue_payment, re_overdue_payment = True, '', [], [], '无', '无'
        token = kw.pop('token')
        data = self.literal_eval(kw.get('data'))
        public = Public()
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from . import connect_mssql
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
