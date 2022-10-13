# -*- coding: utf-8 -*-
from odoo import http, tools
from odoo.http import request

from .public import *
from .connect_mssql import Mssql
import datetime


class Reports(http.Controller):
    @http.route([
        '/api/v11/report/salesStatistics'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_sales_statistics_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("sales")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'cDLCode desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # MKTVP只能看自己对应的brandName资料
            if users.group_id.id != 1:
                if users.group_id.id == 4:
                    brandname = mssql.query(
                        "select distinct BrandName from UFDATA_999_2017.dbo.v_BrandName_VP_sdo where MKTVPname is not null and MKTVPname='" + users.nickname + "' ")
                    if brandname:
                        brandname = map(lambda x: x[0], brandname)
                        sql_add += " and brandName in ('" + "','".join(
                            brandname) + "')"
                    else:
                        rp = {'status': 200, 'message': '您无权限查看该报表或查无数据', 'success': False, 'data': {}, 'total': 0,
                              'page': offset + 1,
                              'per_page': limit}
                        return json_response(rp)
                else:  # 业务
                    child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
                    child_names = map(lambda x: x['nickname'], child_names)
                    sql_add += " and ( cUser_Name='" + users.nickname + "'"
                    if child_names:
                        sql_add += " or cUser_Name in ('" + "','".join(
                            child_names) + "')"
                    sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no")
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get('sdate'):
                    sql_add += " and dDate>='" + queryFilter.get('sdate') + "'"
                if queryFilter and queryFilter.get('edate'):
                    sql_add += " and dDate<='" + queryFilter.get('edate') + "'"
                if queryFilter and queryFilter.get('cDept'):
                    sql_add += " and cDept like '%" + queryFilter.get('cDept') + "%'"
                if queryFilter and queryFilter.get('MKTVP'):
                    sql_add += " and MKTVP like '%" + queryFilter.get('MKTVP') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

            sql_base = "select *from (select cDLCode,dDate,cCusName,cDept,cUser_Name,cInvCode,brandName,MKTVP,iquantity,iPriceUSD,iMoneyUSD,cInvCName,ROW_NUMBER() OVER(order by %s) as rid from V_DispatchLists_all where 1=1" % order
            sql_count = ") t where t.rid>%d and t.rid<=%d" % ((offset - 1) * limit, offset * limit)
            sql = sql_base + sql_add + sql_count
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cDLCode": item[0],
                    "dDate": item[1],
                    "cCusName": item[2],
                    "cDept": item[3],
                    "cUser_Name": item[4],
                    "cInvCode": item[5],
                    "brandName": item[6],
                    "MKTVP": item[7],
                    "iquantity": item[8],
                    "iPriceUSD": item[9],
                    "iMoneyUSD": item[10],
                    "cInvCName": item[11],
                }
                result.append(dict_)
            count = mssql.query("select count(*) from V_DispatchLists_all where 1=1 %s" % sql_add)[0][0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/salesStatisticsCount'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_sales_statistics_count(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("sales")
        if not env:
            return no_token()
        # domain = []
        # fields = eval(kw.get('fields', "[]"))
        # order = kw.get('order', 'cDLCode desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # MKTVP只能看自己对应的brandName资料
            if users.group_id.id != 1:
                if users.group_id.id == 4:
                    brandname = mssql.query(
                        "select distinct BrandName from UFDATA_999_2017.dbo.v_BrandName_VP_sdo where MKTVPname is not null and MKTVPname='" + users.nickname + "' ")
                    if brandname:
                        brandname = map(lambda x: x[0], brandname)
                        sql_add += " and brandName in ('" + "','".join(
                            brandname) + "')"
                    else:
                        rp = {'status': 200, 'message': '您无权限查看该报表或查无数据', 'success': False, 'data': {}, 'total': 0,
                              'page': offset + 1,
                              'per_page': limit}
                        return json_response(rp)
                else:  # 业务
                    child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
                    child_names = map(lambda x: x['nickname'], child_names)
                    sql_add += " and ( cUser_Name='" + users.nickname + "'"
                    if child_names:
                        sql_add += " or cUser_Name in ('" + "','".join(
                            child_names) + "')"
                    sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('sdate'):
                    sql_add += " and dDate>='" + queryFilter.get('sdate') + "'"
                if queryFilter and queryFilter.get('edate'):
                    sql_add += " and dDate<='" + queryFilter.get('edate') + "'"
                if queryFilter and queryFilter.get('cDept'):
                    sql_add += " and cDept like '%" + queryFilter.get('cDept') + "%'"
                if queryFilter and queryFilter.get('MKTVP'):
                    sql_add += " and MKTVP like '%" + queryFilter.get('MKTVP') + "%'"

            count = mssql.query("select count(*) from V_DispatchLists_all where 1=1 %s" % sql_add)[0][0]
            message = "success"
            success = True
        except Exception as e:
            count, success, message = 0, False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/salesOutstandingOrders'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_sales_OutstandingOrders_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("sales")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'cSocode desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            if users.group_id.id != 1:
                child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
                child_names = map(lambda x: x['nickname'], child_names)
                sql_add += " and ( cUser_Name='" + users.nickname + "'"
                if child_names:
                    sql_add += " or cUser_Name in ('" + "','".join(
                        child_names) + "')"
                sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no")
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get('sdate'):
                    sql_add += " and sodate>='" + queryFilter.get('sdate') + "'"
                if queryFilter and queryFilter.get('edate'):
                    sql_add += " and sodate<='" + queryFilter.get('edate') + "'"
                if queryFilter and queryFilter.get('cDept'):
                    sql_add += " and cDept like '%" + queryFilter.get('cDept') + "%'"
                if queryFilter and queryFilter.get('cUser_Name'):
                    sql_add += " and cUser_Name = '" + queryFilter.get('cUser_Name') + "'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

            sql_base = "select *from (select cSocode,ccuscode,ccusname,cCusAbbName,sodate,CusPo,cInvCode,iQuantity,soNoFinishQty,iunitPriceUSD,iunitMoneyUSD,soNoFinishMoneyUSD,cUser_Name,cDept,ROW_NUMBER() OVER(order by %s) as rid from v_notFinished_so_sunray where 1=1" % order
            sql_count = ") t where t.rid>%d and t.rid<=%d" % ((offset - 1) * limit, offset * limit)
            sql = sql_base + sql_add + sql_count
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cSocode": item[0],
                    "ccuscode": item[1],
                    "ccusname": item[2],
                    "cCusAbbName": item[3],
                    "sodate": item[4],
                    "CusPo": item[5],
                    "cInvCode": item[6],
                    "iQuantity": item[7],
                    "soNoFinishQty": item[8],
                    "iunitPriceUSD": item[9],
                    "iunitMoneyUSD": item[10],
                    "soNoFinishMoneyUSD": item[11],
                    "cUser_Name": item[12],
                    "cDept": item[13],
                }
                result.append(dict_)
            count = mssql.query("select count(*) from v_notFinished_so_sunray where 1=1 %s" % sql_add)[0][0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/salesOutstandingOrdersCount'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_sales_OutstandingOrders_count(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("sales")
        if not env:
            return no_token()

        domain = []
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            if users.group_id.id != 1:
                child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
                child_names = map(lambda x: x['nickname'], child_names)
                sql_add += " and ( cUser_Name='" + users.nickname + "'"
                if child_names:
                    sql_add += " or cUser_Name in ('" + "','".join(
                        child_names) + "')"
                sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('sdate'):
                    sql_add += " and sodate>='" + queryFilter.get('sdate') + "'"
                if queryFilter and queryFilter.get('edate'):
                    sql_add += " and sodate<='" + queryFilter.get('edate') + "'"
                if queryFilter and queryFilter.get('cDept'):
                    sql_add += " and cDept like '%" + queryFilter.get('cDept') + "%'"
                if queryFilter and queryFilter.get('cUser_Name'):
                    sql_add += " and cUser_Name = '" + queryFilter.get('cUser_Name') + "'"

            count = mssql.query("select count(*) from v_notFinished_so_sunray where 1=1 %s" % sql_add)[0][0]
            message = "success"
            success = True
        except Exception as e:
            total, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getCrmProject'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_crm_project(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'project_no desc')
        try:
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get("name"):
                    domain.append(('name', 'ilike', queryFilter.get("name")))
                if queryFilter and queryFilter.get("stage_id_name"):
                    domain.append(('stage_id', '=', queryFilter.get("stage_id_name")))
                if queryFilter and queryFilter.get("sdate"):
                    domain.append(('date_from', '>=', queryFilter.get("sdate")))
                if queryFilter and queryFilter.get("edate"):
                    domain.append(('date_to', '<=', queryFilter.get("edate")))
                if queryFilter and queryFilter.get("brandname"):
                    products = request.env["sdo.product"].sudo().search_read(
                        [('brand_name', 'ilike', queryFilter.get("brandname"))], fields=['id'])
                    ids = request.env["sdo.product.line"].sudo().search_read(
                        [('product_id', 'in', list(map(lambda x: x['id'], products))), ('project_id', '!=', False)],
                        fields=['project_id'])
                    if ids:
                        domain.append(('id', 'in', list(map(lambda x: x['project_id'][0], ids))))
                    else:
                        domain.append(('id', '=', 0))
                if queryFilter and queryFilter.get("product_no"):
                    ids = request.env["sdo.product.line"].sudo().search_read(
                        [('product_no', 'ilike', queryFilter.get("product_no")), ('project_id', '!=', False)],
                        fields=['project_id'])
                    if ids:
                        domain.append(('id', 'in', map(lambda x: x['project_id'][0], ids)))
                    else:
                        domain.append(('id', '=', 0))
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['|']
                domain += ['&', ('record_status', '=', 1), ('project_attend_user_ids', 'ilike', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]

            result = env['xlcrm.project'].sudo().search_read(domain, fields, order=order, offset=offset * limit,
                                                             limit=limit)
            count = env['xlcrm.project'].sudo().search_count(domain)
            for item in result:
                item['category'] = item['category_id'][1]
                item['customer'] = item['customer_id'][1]
                item['status'] = item['status_id'][1]
                # item['cycle'] = item['date_from']+'->'+item['date_to']
                users = env['xlcrm.users'].sudo().search_read([('id', 'in', item['project_attend_user_ids'])])
                attends = ''
                for user in users:
                    if not attends:
                        attends = user['nickname'] + '-' + user['user_group_name']
                    else:
                        attends = attends + ',' + user['nickname'] + '-' + user['user_group_name']
                item['attends'] = attends
                item['write_date'] = item['write_date'] + datetime.timedelta(hours=8)
                reviewers = eval(item['reviewers']) if item['reviewers'] else item['reviewers']
                manage = item['create_user_nick_name']
                if reviewers and reviewers.get('Manage'):
                    m_user = env['xlcrm.users'].sudo().search_read([('id', '=', reviewers['Manage'])])
                    manage = ','.join(list(map(lambda x: x['nickname'], m_user)))
                item['Manage'] = manage
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
        '/api/v11/report/getCrmProjectCount'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_crm_project_count(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'project_no desc')
        try:
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                # offset = queryFilter.pop("page_no") - 1
                # limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get("name"):
                    domain.append(('name', 'ilike', queryFilter.get("name")))
                if queryFilter and queryFilter.get("stage_id_name"):
                    domain.append(('stage_id', '=', queryFilter.get("stage_id_name")))
                if queryFilter and queryFilter.get("sdate"):
                    domain.append(('date_from', '>=', queryFilter.get("sdate")))
                if queryFilter and queryFilter.get("edate"):
                    domain.append(('date_to', '<=', queryFilter.get("edate")))
                if queryFilter and queryFilter.get("product_no"):
                    ids = request.env["sdo.product.line"].sudo().search_read(
                        [('product_no', 'ilike', queryFilter.get("product_no"))], fields=['project_id'])
                    if ids:
                        domain.append(('id', 'in', map(lambda x: x['project_id'][0], ids)))
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['|']
                domain += ['&', ('record_status', '=', 1), ('project_attend_user_ids', 'ilike', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]

            count = env['xlcrm.project'].sudo().search_count(domain)

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getCrmProjectOut'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_crm_project_Out(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'project_no desc')
        try:
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get("name"):
                    domain.append(('name', 'ilike', queryFilter.get("name")))
                if queryFilter and queryFilter.get("stage_id_name"):
                    domain.append(('stage_id', '=', queryFilter.get("stage_id_name")))
                if queryFilter and queryFilter.get("sdate"):
                    domain.append(('date_from', '>=', queryFilter.get("sdate")))
                if queryFilter and queryFilter.get("edate"):
                    domain.append(('date_to', '<=', queryFilter.get("edate")))
                if queryFilter and queryFilter.get("brandname"):
                    products = request.env["sdo.product"].sudo().search_read(
                        [('brand_name', 'ilike', queryFilter.get("brandname"))], fields=['id'])
                    ids = request.env["sdo.product.line"].sudo().search_read(
                        [('product_id', 'in', list(map(lambda x: x['id'], products)))], fields=['project_id'])
                    if ids:
                        domain.append(('id', 'in', list(map(lambda x: x['project_id'][0], ids))))
                    else:
                        domain.append(('id', '=', 0))
                if queryFilter and queryFilter.get("product_no"):
                    ids = request.env["sdo.product.line"].sudo().search_read(
                        [('product_no', 'ilike', queryFilter.get("product_no"))], fields=['project_id'])
                    if ids:
                        domain.append(('id', 'in', list(map(lambda x: x['project_id'][0], ids))))
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('create_user_id', '=', records_ref.id)]
                domain += ['|']
                domain += ['&', ('record_status', '=', 1), ('project_attend_user_ids', 'ilike', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), ('create_user_id', 'in', records_ref.child_ids_all.ids)]

            result = env['xlcrm.project'].sudo().search_read(domain, fields, order=order, offset=offset * limit,
                                                             limit=limit)
            count = env['xlcrm.project'].sudo().search_count(domain)
            for item in result:
                item['category'] = item['category_id'][1]
                item['customer'] = item['customer_id'][1]
                item['status'] = item['status_id'][1]
                item['cycle'] = datetime.datetime.strftime(item['date_from'],
                                                           '%Y-%m-%d') + '->' + datetime.datetime.strftime(
                    item['date_to'], '%Y-%m-%d')
                users = env['xlcrm.users'].sudo().search_read([('id', 'in', item['project_attend_user_ids'])])
                attends = ''
                for user in users:
                    if not attends:
                        attends = user['nickname'] + '-' + user['user_group_name']
                    else:
                        attends = attends + ',' + user['nickname'] + '-' + user['user_group_name']
                item['attends'] = attends
                product_result = request.env["sdo.product.line"].sudo().search_read([('project_id', '=', item['id'])])
                model_fields = request.env["sdo.product.line"].fields_get()
                for r in product_result:
                    for f in r.keys():
                        if model_fields[f]['type'] == 'many2one':
                            if r[f]:
                                r[f] = {'id': r[f][0], 'display_name': r[f][1]}
                            else:
                                r[f] = ''

                    if records_ref.group_id.id not in (1, 2, 4):
                        r['product_price'] = ''
                    if records_ref.group_id.id not in (1, 4):
                        r['product_profit'] = ''
                remarks_result = request.env['xlcrm.project.remark'].sudo().search_read(
                    [('project_id', '=', item['id'])])
                remarks = ''
                if remarks_result:
                    for remark in remarks_result:
                        remarks = (remarks + '；' + '日志操作时间：%s;日志内容：%s' % (
                            datetime.datetime.strftime(remark['update_time'], '%Y-%m-%d %H:%M:%S'),
                            remark['content'])) if remarks else '日志操作时间：%s;日志内容：%s' % (
                            datetime.datetime.strftime(remark['update_time'], '%Y-%m-%d %H:%M:%S'), remark['content'])
                item['remarks'] = remarks
                if ids and product_result and len(ids) == 1:
                    product_result = product_result[0]
                item['product_line'] = product_result
                item['logtime'] = ''
                remark_res = env['xlcrm.project.remark'].sudo().search_read([('project_id', '=', item['id'])],
                                                                            order='write_date desc')
                if remark_res:
                    item['logtime'] = remark_res[0]['update_time'] + datetime.timedelta(hours=8)
                reviewers = eval(item['reviewers']) if item['reviewers'] else {}
                manage = item['create_user_nick_name']
                if reviewers.get('Manage'):
                    m_user = env['xlcrm.users'].sudo().search_read([('id', '=', reviewers['Manage'])])
                    manage = ','.join(list(map(lambda x: x['nickname'], m_user)))
                item['Manage'] = manage
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
        '/api/v11/report/getPurchaseTotal'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseTotal(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order_field = kw.get('order', 'TGAPQty')
        order_type = kw.get('order', '')
        result_so = []
        result_po = []
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode like '%" + queryFilter.get('cinvCode') + "%'"
                if queryFilter and queryFilter.get('cCusName'):
                    sql_add += " and cCusName like '%" + queryFilter.get('cCusName') + "%'"
                if queryFilter and queryFilter.get('BrandName'):
                    sql_add += " and BrandName like '%" + queryFilter.get('BrandName') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order_field = queryFilter.get("order_field")
                    order_type = queryFilter.get("order_type")
            sql_base = "select distinct cinvCode,PL from v_GetGap where 1=1 "
            # sql_base = "select *from (select cinvCode,PL,sum(SO) as SO,sum(PO) as PO,sum(HKST) as HKST,sum(SZST) as SZST," \
            #            "sum(BGQty) as BGQty,sum(GAPQty) as GAPQty,ROW_NUMBER() OVER(order by %s) as rid from v_GetGap where 1=1" % order
            # sql_count = " group by cinvCode,PL) t where t.rid>%d and t.rid<=%d" % ((offset - 1) * limit, offset * limit)
            # sql_count = " t"
            sql = sql_base + sql_add
            result_base = mssql.query(sql)
            # result_base_ = map(lambda x: x[0].decode(), result_base) if result_base else []

            # 算汇总数据
            sql_temp = ""
            for index, te in enumerate(result_base):
                if index == 0:
                    sql_temp += "('%s'," % te[0]
                if index == len(result_base) - 1:
                    sql_temp += "'%s')" % te[0]
                if index > 0 and index < len(result_base) - 1:
                    sql_temp += "'%s'," % te[0]

            sql_total = "select cinvCode,PL,sum(SO) as SO,sum(PO) as PO,sum(HKST) as HKST,sum(SZST) as SZST," \
                        "sum(BGQty) as BGQty,sum(GAPQty) as GAPQty,BrandName from v_GetGap where cinvCode in %s group by cinvCode,PL,BrandName" % sql_temp

            result_total_ = mssql.query(sql_total)
            gap = queryFilter.get('gap', [])
            gap = '' if not gap or len(gap) > 1 else gap[0]
            result_total_ = filter(lambda x: x[7] >= 0, result_total_) if gap == "正数" else filter(lambda x: x[7] < 0,
                                                                                                  result_total_) if gap else result_total_
            result_total = []
            for item in result_total_:
                dict_ = {
                    "TcinvCode": item[0],
                    "TPL": item[1],
                    "TSO": item[2],
                    "TPO": item[3],
                    "THKST": item[4],
                    "TSZST": item[5],
                    "TBGQty": item[6],
                    "TGAPQty": item[7],
                    "BrandName": item[8],
                    "id": item[0] + item[1]
                }
                result_total.append(dict_)
            result_total.sort(key=lambda x: x[order_field], reverse=True if order_type == 'desc' else False)
            start = offset * limit
            count = len(result_total_)
            end = count if count <= offset * limit + limit else offset * limit + limit
            result_total = result_total[start:end]
            # 获取明细
            sql_temp = ""
            for index, te in enumerate(result_total):
                if index == 0:
                    sql_temp += "('%s'," % te['TcinvCode']
                if index == len(result_total) - 1:
                    sql_temp += "'%s')" % te['TcinvCode']
                if index > 0 and index < len(result_total) - 1:
                    sql_temp += "'%s'," % te['TcinvCode']
            sql_detail = "select cinvCode,PL,SO,PO,HKST,SZST," \
                         "BGQty,GAPQty,cCusCode,cCusName,cCusExch_name,SPI,BrandName from v_GetGap where cinvCode in %s" % sql_temp
            result_detail = mssql.query(sql_detail)
            result = []
            for item in result_detail:
                dict_ = {
                    "cinvCode": item[0],
                    "PL": item[1],
                    "SO": item[2],
                    "PO": item[3],
                    "HKST": item[4],
                    "SZST": item[5],
                    "BGQty": item[6],
                    "GAPQty": item[7],
                    "cCusCode": item[8],
                    "cCusName": item[9],
                    "cCusExch_name": item[10],
                    "SPI": item[11],
                    "BrandName": item[12]
                }
                result.append(dict_)
            for tl in result_total:
                tep_result = filter(lambda x: x['cinvCode'] == tl['TcinvCode'] and x['PL'] == tl['TPL'], result)
                tl['TSO'] = sum(map(lambda x: x['SO'], tep_result))
                tl['TPO'] = sum(map(lambda x: x['PO'], tep_result))
                tl['THKST'] = sum(map(lambda x: x['HKST'], tep_result))
                tl['TSZST'] = sum(map(lambda x: x['SZST'], tep_result))
                tl['TBGQty'] = sum(map(lambda x: x['BGQty'], tep_result))
                tl['TGAPQty'] = sum(map(lambda x: x['GAPQty'], tep_result))
            # 获取PO
            sql_po = "select * from v_Gap_PO where cinvCode in %s" % sql_temp
            result_po_ = mssql.query(sql_po)

            for item in result_po_:
                dict_ = {
                    "cPOID": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cVenCode": item[2],
                    "cVenName": item[3],
                    "cCusCode": item[4],
                    "cCusName": item[5],
                    "cInvCode": item[6],
                    "brandname": item[7],
                    "Qty": item[8],
                }
                result_po.append(dict_)
            # 获取SO
            sql_so = "select * from v_Gap_SO where cinvCode in %s" % sql_temp
            result_so_ = mssql.query(sql_so)

            for item in result_so_:
                dict_ = {
                    "cSoCode": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cCusCode": item[2],
                    "cCusName": item[3],
                    "cInvCode": item[4],
                    "brandname": item[5],
                    "Qty": item[6],
                }
                result_so.append(dict_)

            count = len(result_total_)
            message = "success"
            success = True
        except Exception as e:
            detail_data, total_data, so_data, po_data, success, message = '', '', '', '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'detail_data': result, 'total_data': result_total,
              'total': count, 'page': offset + 1, 'so_data': result_so, 'po_data': result_po,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v12/report/getPurchaseTotal'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseTotal12(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order_field = kw.get('order', 'TcinvCode')
        order_type = kw.get('order', 'desc')
        result_so = []
        result_po = []
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no") - 1
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode like '%" + queryFilter.get('cinvCode') + "%'"
                if queryFilter and queryFilter.get('cCusName'):
                    sql_add += " and cCusName like '%" + queryFilter.get('cCusName') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order_field = queryFilter.get("order_field")
                    order_type = queryFilter.get("order_type")
            # sql_base = "select distinct cinvCode,PL from v_GetGap where 1=1 "
            # sql = sql_base + sql_add
            # result_base = mssql.query(sql)
            # # 算汇总数据
            # sql_temp = ""
            # for index, te in enumerate(result_base):
            #     if index == 0:
            #         sql_temp += "('%s'," % te[0]
            #     if index == len(result_base) - 1:
            #         sql_temp += "'%s')" % te[0]
            #     if index > 0 and index < len(result_base) - 1:
            #         sql_temp += "'%s'," % te[0]

            sql_total = "select cinvCode,PL,sum(SO) as SO,sum(PO) as PO,sum(HKST) as HKST,sum(SZST) as SZST," \
                        "sum(BGQty) as BGQty,sum(GAPQty) as GAPQty from v_GetGap where 1=1 %s group by cinvCode,PL" % sql_add

            result_total_ = mssql.query(sql_total)
            result_total = []
            for item in result_total_:
                dict_ = {
                    "TcinvCode": item[0],
                    "TPL": item[1],
                    "TSO": item[2],
                    "TPO": item[3],
                    "THKST": item[4],
                    "TSZST": item[5],
                    "TBGQty": item[6],
                    "TGAPQty": item[7],
                    "id": item[0] + item[1]
                }
                result_total.append(dict_)
            result_total.sort(key=lambda x: x[order_field], reverse=True if order_type == 'desc' else False)
            start = offset * limit
            count = len(result_total_)
            end = count if count <= offset * limit + limit else offset * limit + limit
            result_total = result_total[start:end]
            # 获取明细
            sql_temp = ""
            for index, te in enumerate(result_total):
                if index == 0:
                    sql_temp += "('%s'," % te['TcinvCode']
                if index == len(result_total) - 1:
                    sql_temp += "'%s')" % te['TcinvCode']
                if index > 0 and index < len(result_total) - 1:
                    sql_temp += "'%s'," % te['TcinvCode']
            sql_detail = "select cinvCode,PL,SO,PO,HKST,SZST," \
                         "BGQty,GAPQty,cCusCode,cCusName,cCusExch_name from v_GetGap where 1=1 %s" % sql_add
            result_detail = mssql.query(sql_detail)
            result = []
            for item in result_detail:
                dict_ = {
                    "cinvCode": item[0],
                    "PL": item[1],
                    "SO": item[2],
                    "PO": item[3],
                    "HKST": item[4],
                    "SZST": item[5],
                    "BGQty": item[6],
                    "GAPQty": item[7],
                    "cCusCode": item[8],
                    "cCusName": item[9],
                    "cCusExch_name": item[10],
                }
                result.append(dict_)
            # for tl in result_total:
            #     tep_result = filter(lambda x: x['cinvCode'] == tl['TcinvCode'] and x['PL'] == tl['TPL'], result)
            #     tl['TSO'] = sum(map(lambda x: x['SO'], tep_result))
            #     tl['TPO'] = sum(map(lambda x: x['PO'], tep_result))
            #     tl['THKST'] = sum(map(lambda x: x['HKST'], tep_result))
            #     tl['TSZST'] = sum(map(lambda x: x['SZST'], tep_result))
            #     tl['TBGQty'] = sum(map(lambda x: x['BGQty'], tep_result))
            #     tl['TGAPQty'] = sum(map(lambda x: x['GAPQty'], tep_result))
            # 获取PO
            sql_po = "select * from v_Gap_PO where cinvCode in %s" % sql_temp
            result_po_ = mssql.query(sql_po)

            for item in result_po_:
                dict_ = {
                    "cPOID": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cVenCode": item[2],
                    "cVenName": item[3],
                    "cCusCode": item[4],
                    "cCusName": item[5],
                    "cInvCode": item[6],
                    "brandname": item[7],
                    "Qty": item[8],
                }
                result_po.append(dict_)
            # 获取SO
            sql_so = "select * from v_Gap_SO where cinvCode in %s" % sql_temp
            result_so_ = mssql.query(sql_so)

            for item in result_so_:
                dict_ = {
                    "cSoCode": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cCusCode": item[2],
                    "cCusName": item[3],
                    "cInvCode": item[4],
                    "brandname": item[5],
                    "Qty": item[6],
                }
                result_so.append(dict_)

            count = len(result_total_)
            message = "success"
            success = True
        except Exception as e:
            detail_data, total_data, so_data, po_data, success, message = '', '', '', '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'detail_data': result, 'total_data': result_total,
              'total': count, 'page': offset + 1, 'so_data': result_so, 'po_data': result_po,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPurchaseDetail'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseDetail(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'cinvCode,cCusName,GAPQty desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode like '%" + queryFilter.get('cinvCode') + "%'"
                if queryFilter and queryFilter.get('cCusName'):
                    sql_add += " and cCusName like '%" + queryFilter.get('cCusName') + "%'"
                if queryFilter and queryFilter.get('BrandName'):
                    sql_add += " and BrandName like '%" + queryFilter.get('BrandName') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

            sql_base = "select cinvCode,PL,SO,PO,HKST,SZST," \
                       "BGQty,GAPQty,cCusName,cCusExch_name,SPI,BrandName from v_GetGap where 1=1"
            sql = sql_base + sql_add + " order by %s" % order
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cinvCode": item[0],
                    "PL": item[1],
                    "SO": item[2],
                    "PO": item[3],
                    "HKST": item[4],
                    "SZST": item[5],
                    "BGQty": item[6],
                    "GAPQty": item[7],
                    "cCusName": item[8],
                    "cCusExch_name": item[9],
                    "SPI": item[10],
                    "BrandName": item[11]
                }
                result.append(dict_)
            # count = mssql.query(
            #     "select count(*) from v_GetGap where 1=1 %s ) r " % sql_add)[
            #     0][0]
            count = 0
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'detail_data': result, 'total': count,
              'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/createPurchase',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_purchase(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        insert_data = data.get('data')
        so_data = data.get('so_data')
        po_data = data.get('po_data')
        mssql = Mssql("stock")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            result_object = {}
            import datetime
            version = 'V%s%s' % (
                str(env.uid), (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y%m%d%H%M%S'))
            sqllist, sqllist_so, sqllist_po = [], [], []
            PM = env['xlcrm.users'].sudo().search_read([('id', '=', data.get('PMSigner'))])[0]
            pmsigner = PM['nickname'] + '_%d' % data.get('PMSigner')
            pm_email = PM['email']
            for values in insert_data:
                val = []
                val.append(version)
                val.append(values['cinvCode'])
                val.append(values['HKST'])
                val.append(values['PL'].decode())
                val.append(values['SO'])
                val.append(values['SZST'])
                val.append(values['BGQty'])
                val.append(values['cCusName'].decode())
                val.append(values['PO'])
                val.append(values['GAPQty'])
                val.append(values['cCusExch_name'].decode())
                val.append(values['cCusCode'].decode())
                val.append(values['SPI'])
                val.append(values['BrandName'])
                sqllist.append(tuple(val))
            for values in so_data:
                val = []
                val.append(version)
                val.append(values['cSoCode'])
                val.append(values['dDate'])
                val.append(values['cCusCode'].decode())
                val.append(values['cCusName'].decode())
                val.append(values['cInvCode'])
                val.append(values['brandname'].decode())
                val.append(values['Qty'])
                sqllist_so.append(tuple(val))
            for values in po_data:
                val = []
                val.append(version)
                val.append(values['cPOID'])
                val.append(values['dDate'])
                val.append(values['cVenCode'].decode())
                val.append(values['cVenName'].decode())
                val.append(values['cCusCode'])
                val.append(values['cCusName'].decode())
                val.append(values['cInvCode'])
                val.append(values['brandname'].decode())
                val.append(values['Qty'])
                sqllist_po.append(tuple(val))
            init_user = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])[0]['nickname'] + '_%d' % env.uid
            result_object = mssql.batch_in_up_de([["insert into PurchaseDetail(versions,cinvCode,HKST,PL,SO,SZST,BGQty,"
                                                   "cCusName,PO,GAPQty,cCusExch_name,cCusCode,SPI,BrandName)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                                   sqllist], [
                                                      "insert into PurchasePO(versions,cPOID,dDate,cVenCode,cVenName,cCusCode,cCusName,cInvCode,brandName,Qty)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                                      sqllist_po]
                                                     , [
                                                      "insert into PurchaseSO(versions,cSoCode,dDate,cCusCode,cCusName,cInvCode,brandName,Qty)values(%s,%s,%s,%s,%s,%s,%s,%s)",
                                                      sqllist_so], [
                                                      "insert into PurchaseMain(versions,cinvCode,PMsigner,init_user)values(%s,%s,%s,%s)",
                                                      [(version, insert_data[0]['cinvCode'], pmsigner, init_user)]]])

            success_email = True
            if result_object:
                if pm_email:
                    from . import send_email, public
                    email_obj = send_email.Send_email()
                    uid = data.get('PMSigner')
                    sbuject = "U8采购订单确认通知"
                    # to = ["yangyouhui@szsunray.com"]
                    to = ["leihui@szsunray.com"]
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        to = [pm_email]
                    token = public.get_token(env, uid)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/reports-U8-purchase_order-list/0/' + json.dumps(token)
                    content = """
                            <html lang="en">
                            <body>
                                <div>
                                    您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待确认U8采购订单申请单，请点击
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
            if success_email and result_object:
                mssql.commit()
                success = True
                message = "success"
            else:
                success = False
                message = "通知邮件发送失败"
        except Exception as e:
            result_object, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
            mssql.close()
        rp = {'status': 200, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPurchaseList'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseList(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'init_time desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                offset = queryFilter.pop("page_no")
                limit = queryFilter.pop("page_size")
                if queryFilter and queryFilter.get('status'):
                    sql_add += " and status = %d" % queryFilter.get('status')
                if queryFilter and queryFilter.get('init_user'):
                    sql_add += " and init_user = '" + queryFilter.get('init_user') + "'_%d" % env.uid
                if queryFilter and queryFilter.get('update_user'):
                    sql_add += " and update_user like '%" + queryFilter.get('update_user') + "%'"
                if queryFilter and (queryFilter.get('cCusName') or queryFilter.get('cinvCode')):
                    con = 'cinvCode' if queryFilter.get('cinvCode') else 'cCusName'
                    cinSql = "select versions from PurchaseDetail where %s='%s'" % (
                        con,
                        queryFilter.get('cinvCode') if queryFilter.get('cinvCode') else queryFilter.get('cCusName'))
                    versions = mssql.query(cinSql)
                    sql_add += " and versions in ("
                    for index, ver in enumerate(versions):
                        sql_add += "'%s'" % ver[0] if not index else ",'%s'" % ver[0]
                    sql_add += ")"
                if queryFilter and queryFilter.get('sdate'):
                    column = 'init_time' if queryFilter.get('init_user') else 'update_time'
                    sql_add += " and %s >= '" + queryFilter.get('sdate') + "'" % column
                if queryFilter and queryFilter.get('edate'):
                    sql_add += " and init_time <= '" + queryFilter.get('edate') + "'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field")
                    order += " " + queryFilter.get("order_type")

            sql_base = "select *from (select versions,cinvCode,status,PMsigner,init_user,init_time,update_user,update_time,ROW_NUMBER() OVER(order by %s) as rid from PurchaseMain where 1=1 " % order
            sql_count = " ) t where t.rid>%d and t.rid<=%d" % ((offset - 1) * limit, offset * limit)
            sql = sql_base + sql_add + sql_count
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "versions": item[0],
                    "cinvCode": item[1],
                    "status": item[2],
                    "PMsigner": self.translation(item[3]).split('_')[0] if item[3] else '',
                    "init_user": self.translation(item[4]).split('_')[0] if item[4] else '',
                    "init_time": item[5],
                    "update_user": self.translation(item[6]).split('_')[0] if item[6] else '',
                    "update_time": item[7],
                    "PMsigner_uid": self.translation(item[3]).split('_')[1] if item[3] else '',
                    "cinvCode_query": queryFilter.get('cinvCode') if queryFilter and queryFilter.get('cinvCode') else ''
                }
                result.append(dict_)
            count = mssql.query(
                "select count(*) from PurchaseMain where 1=1 %s " % sql_add)[
                0][0]
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPOBaseData'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPOBaseData(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        try:
            sql_add = ""
            sql_base = "select cVenCode,cVenName,cContactCode,cContactName,cVenDepart,cVenPUOMProtocol,cVenPPerson,cVenExch_name,cname from v_Vendor"
            sql = sql_base
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cvencode": item[0],
                    "cvenname": item[1],
                    "ccontactcode": item[2],
                    "cvenperson": item[3],
                    "cdepcode": item[4],
                    "cvenpuomprotocol": item[5],
                    "cpersoncode": item[6],
                    "cexch_name": item[7],
                    "cname": item[8]
                }
                result.append(dict_)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPools'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPools(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        try:
            sql_add = ""
            sql_base = "select cNo,QuoteNumber,cCusCode,cCusAbbName,brandName,case isBom when 'Y' then '是' else '否' end as isbom,cInvCode,Cost from v_Pool"
            sql = sql_base
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cbdefine25": item[0],
                    "cdefine31": item[1],
                    "cbdefine20": item[2],
                    "cbdefine21": item[3],
                    "brandName": item[4],
                    "isBom": item[5],
                    "cinvcode": item[6],
                    "cbdefine23": item[7],
                }
                result.append(dict_)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getBoms'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getBoms(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()
        try:
            sql_add = ""
            sql_base = "select Mcinvcode,cInvCode,iquantity,BaseMoney from v_Bom"
            sql = sql_base
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "Mcinvcode": item[0],
                    "cInvCode": item[1],
                    "iquantity": item[2],
                    "BaseMoney": item[3],
                }
                result.append(dict_)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPurchaseDetailVer'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseDetailVer(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'GAPQty desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('versions'):
                    sql_add += " and versions like '%" + queryFilter.get('versions') + "%'"
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode like '%" + queryFilter.get('cinvCode') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

            sql_base = "select cinvCode,PL,SO,PO,HKST,SZST," \
                       "BGQty,GAPQty,cCusName,cCusExch_name,cCusCode,id,confirm,SPI,BrandName,remark from PurchaseDetail where 1=1"
            sql = sql_base + sql_add + " order by %s" % order
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cinvCode": item[0],
                    "PL": item[1],
                    "SO": item[2],
                    "PO": item[3],
                    "HKST": item[4],
                    "SZST": item[5],
                    "BGQty": item[6],
                    "GAPQty": item[7],
                    "cCusName": self.translation(item[8]),
                    "cCusExch_name": self.translation(item[9]),
                    "cCusCode": item[10],
                    "id": item[11],
                    "confirm": item[12],
                    "SPI": item[13],
                    "BrandName": item[14],
                    "remark": item[15]
                }
                result.append(dict_)
            # count = mssql.query(
            #     "select count(*) from v_GetGap where 1=1 %s ) r " % sql_add)[
            #     0][0]
            count = 0
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPurchaseDetailVerPO'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPurchaseDetailVerPO(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'a.versions desc')
        try:
            user = env['xlcrm.users'].sudo()
            users = user.search([('id', '=', env.uid)])
            sql_add = ""
            # 非管理员只能看自己或下属的资料
            # if users.group_id.id != 1:
            #     child_names = user.search_read([('id', 'in', users.child_ids_all.ids)])
            #     child_names = map(lambda x: x['nickname'], child_names)
            #     sql_add += " and ( cUser_Name='" + users.nickname + "'"
            #     if child_names:
            #         sql_add += " or cUser_Name in ('" + "','".join(
            #             child_names) + "')"
            #     sql_add += ")"
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and a.cinvCode like '%" + queryFilter.get('cinvCode') + "%'"
                if queryFilter and queryFilter.get('cCusName'):
                    sql_add += " and a.cCusName like '%" + queryFilter.get('cCusName') + "%'"
                if queryFilter and queryFilter.get('update_user'):
                    sql_add += " and update_user like '%" + queryFilter.get('update_user') + "%'"
                if queryFilter and queryFilter.get("order_field"):
                    order = queryFilter.get("order_field") + " " + queryFilter.get("order_type")

            sql_base = "select a.cinvCode,a.PL,a.SO,a.PO,a.HKST,a.SZST," \
                       "a.BGQty,a.GAPQty,a.cCusName,a.cCusExch_name,a.cCusCode,a.id,a.confirm,a.SPI,a.BrandName,a.remark,a.versions,b.update_user,b.update_time from PurchaseDetail a join PurchaseMain b on a.versions=b.versions where b.status=1 and a.confirm>0"
            sql = sql_base + sql_add + " order by %s" % order
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cinvCode": item[0],
                    "PL": item[1],
                    "SO": item[2],
                    "PO": item[3],
                    "HKST": item[4],
                    "SZST": item[5],
                    "BGQty": item[6],
                    "GAPQty": item[7],
                    "cCusName": self.translation(item[8]),
                    "cCusExch_name": self.translation(item[9]),
                    "cCusCode": item[10],
                    "id": item[11],
                    "confirm": item[7] if not item[12] else item[12],
                    "SPI": item[13],
                    "BrandName": self.translation(item[14]) if item[14] else '',
                    "remark": self.translation(item[15]) if item[15] else '',
                    "versions": item[16],
                    "update_user": self.translation(item[17]).split('_')[0] if item[17] else '',
                    "update_time": item[18]
                }
                result.append(dict_)
            # count = mssql.query(
            #     "select count(*) from v_GetGap where 1=1 %s ) r " % sql_add)[
            #     0][0]
            count = 0
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/updatePurchase',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def update_purchase(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0].replace('null', '""')).get("data")
        insert_data = data.get('data')

        mssql = Mssql("stock")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            result_obj = {}
            versions = data.get('versions')
            detail_data = data.get('detail_data')
            detail_ = []
            for it in detail_data:
                val = []
                val.append(it['confirm'])
                val.append(it['remark'].decode())
                val.append(it['id'])
                detail_.append(tuple(val))
            user = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])[0]
            update_user = user['nickname'] + '_%d' % env.uid
            import datetime
            update_time = datetime.datetime.now() + datetime.timedelta(hours=8)
            result = mssql.in_up_de(
                "update PurchaseMain set update_user=%s,update_time=%s,status=%s where versions=%s",
                (update_user, update_time, 1, versions))
            result_up_del = mssql.batch_in_up_de(
                [["update PurchaseDetail set confirm=%s,remark=%s where id=%s", detail_]])
            if result and result_up_del:
                mssql.commit()
                sql = "select update_user,update_time,status from PurchaseMain where versions = '%s'" % versions
                result_ = mssql.query(sql)
                if result_:
                    item = result_[0]
                    result_obj['update_user'] = item[0].split('_')[0] if item[0] else ''
                    result_obj['update_time'] = item[1] if item[1] else ''
                    result_obj['status'] = item[2] if item[2] else ''

            success = True
            message = "success"
        except Exception as e:
            result_obj, status, success, message = {}, 200, False, str(e)
        finally:
            env.cr.close()
            mssql.close()
        rp = {'status': 200, 'message': message, 'data': result_obj, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPODetail'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getPODetail(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        try:
            sql_add = ""
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode= '" + queryFilter.get('cinvCode') + "'"
                if queryFilter and queryFilter.get('versions'):
                    sql_add += " and versions= '" + queryFilter.get('versions') + "'"
                if queryFilter and queryFilter.get('cCusCode'):
                    sql_add += " and cCusCode= '" + queryFilter.get('cCusCode') + "'"

            sql_base = "select cPOID,dDate,cVenCode,cVenName,cCusCode,cCusName,cInvCode,brandname,Qty from PurchasePO where 1=1"
            sql = sql_base + sql_add
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cPOID": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cVenCode": item[2],
                    "cVenName": item[3],
                    "cCusCode": item[4],
                    "cCusName": item[5],
                    "cInvCode": item[6],
                    "brandname": item[7],
                    "Qty": item[8],
                }
                result.append(dict_)
            # count = mssql.query(
            #     "select count(*) from v_GetGap where 1=1 %s ) r " % sql_add)[
            #     0][0]
            count = 0
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getSODetail'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getSODetail(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        try:
            sql_add = ""
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data").replace('null', 'None'))
                if queryFilter and queryFilter.get('cinvCode'):
                    sql_add += " and cinvCode= '" + queryFilter.get('cinvCode') + "'"
                if queryFilter and queryFilter.get('versions'):
                    sql_add += " and versions= '" + queryFilter.get('versions') + "'"
                if queryFilter and queryFilter.get('cCusCode'):
                    sql_add += " and cCusCode= '" + queryFilter.get('cCusCode') + "'"

            sql_base = "select cSoCode,dDate,cCusCode,cCusName,cInvCode,brandname,Qty from PurchaseSO where 1=1"
            sql = sql_base + sql_add
            result_ = mssql.query(sql)
            result = []
            for item in result_:
                dict_ = {
                    "cSoCode": item[0],
                    "dDate": item[1].strftime('%Y-%m-%d'),
                    "cCusCode": item[2],
                    "cCusName": item[3],
                    "cInvCode": item[4],
                    "brandname": item[5],
                    "Qty": item[6],
                }
                result.append(dict_)
            # count = mssql.query(
            #     "select count(*) from v_GetGap where 1=1 %s ) r " % sql_add)[
            #     0][0]
            count = 0
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/report/createPO/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_po(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            data['station_no'] = 1
            data["init_user"] = env.uid
            data["update_user"] = env.uid
            data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            data['po_attend_user_ids'] = [[6, 0, []]]
            # from . import public
            sta = Stations('PO申请单')
            # recode_status=0表示保存，1表示提交，草稿无下一站签核人
            record_status = data.get('record_status')
            type = 'add'
            if not data['id']:
                if record_status == 0:
                    data['signer'] = env.uid
                    review_id = env[model].sudo().create(data).id
                else:
                    signers = data.get('reviewers', {})
                    data['station_no'] = 5
                    data['status_id'] = 2
                    data['signer'] = signers.get('pm')
                    data['station_desc'] = sta.getStionsDesc(5)
                    review_id = env[model].sudo().create(data).id
                    # env['report.pobase'].sudo().create(
                    #     {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
                    # 写入签核人信息
                    for key, values in signers.items():
                        station_no = sta.getStaions(key)
                        station_desc = sta.getStionsDesc(station_no)
                        signer = values
                        signer = [signer] if isinstance(signer, int) else signer
                        if signer:
                            for s in signer:
                                data['po_attend_user_ids'][0][2].append(s)
                            env['report.po.signers'].sudo().create(
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
                    signers = data.get('reviewers', {})
                    data['station_no'] = 5
                    data['status_id'] = 2
                    data['signer'] = signers.get('pm')
                    review_id = data['id']
                    # 判断是否回签
                    sign_back = env['reports.po.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    if sign_back and sign_back[0]['sign_over'] == 'N':
                        next_signer = ''
                        sign_station = sign_back[0]['sign_station'] + str(1) + ',' if sign_back[0][
                            'sign_station'] else '' + str(1) + ','
                        env['reports.po.partial'].sudo().browse(sign_back[0]['id']).write(
                            {'sign_station': sign_station})
                        ne_station = list(
                            set(sign_back[0]['to_station'].split(',')) - set(sign_station.split(',')))
                        if not ne_station or ne_station == [str(1)]:
                            next_station = sign_back[0]['from_station']
                            next_signer = env['report.po.signers'].sudo().search_read(
                                ['&', ('review_id', '=', review_id), ('station_no', '=', next_station)],
                                ['signers'])
                            if next_signer:
                                next_signer = next_signer[0]['signers']
                        else:
                            next_station = 28
                        data['signer'] = next_signer
                        data['station_no'] = next_station
                    data['station_desc'] = sta.getStionsDesc(data['station_no'])
                    env[model].sudo().browse(review_id).write(data)
                    # env['report.pobase'].sudo().search([('review_id', '=', review_id)]).unlink()
                    # env['report.pobase'].sudo().create(
                    #     {'review_id': review_id, 'station_no': 1, 'init_user': env.uid, 'update_user': env.uid})
                    sta_list = []
                    # 写入签核人信息
                    for key, values in signers.items():
                        station_no = sta.getStaions(key)
                        station_desc = sta.getStionsDesc(station_no)
                        signer = values
                        signer = [signer] if isinstance(signer, int) else signer
                        # if signer and 4 in signer:
                        #     signer.remove(4)
                        if signer:
                            for s in signer:
                                data['po_attend_user_ids'][0][2].append(s)
                            sign_result = env['report.po.signers'].sudo().search_read(
                                [('review_id', '=', review_id), ('station_no', '=', station_no)])
                            if sign_result:
                                write_data = {}
                                signers = ','.join(map(lambda x: str(x), signer))
                                if sign_result[0]['signers'] == signers:
                                    write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                                else:
                                    write_data['update_time'] = datetime.datetime.now() + datetime.timedelta(hours=8)
                                    write_data['signers'] = signers
                                env['report.po.signers'].sudo().browse(sign_result[0]['id']).write(write_data)
                            else:
                                env['report.po.signers'].sudo().create(
                                    {"review_id": review_id, "station_no": station_no, 'station_desc': station_desc,
                                     'signers': ','.join(map(lambda x: str(x), signer))})
                            station_model = sta.getModel(station_no)
                            dom = [('id' if station_no == 1 else 'review_id', '=', review_id),
                                   ('station_no', '=', station_no)]
                            signed_result = env[station_model].sudo().search_read(dom)
                            if signed_result and signed_result[0]['init_user'][0] not in signer:
                                env[station_model].sudo().browse(signed_result[0]['id']).unlink()

                            sta_list.append(station_no)
                    # 删除不在这次签核人
                    no_station = env['report.po.signers'].sudo().search_read(
                        [('review_id', '=', review_id), ('station_no', 'not in', sta_list)])
                    env['report.po.signers'].sudo().search(
                        [('review_id', '=', review_id), ('station_no', 'not in', sta_list)]).unlink()

                    # 删除不在这次签核签核记录
                    if no_station:
                        for no_st in no_station:
                            no_model = sta.getModel(no_st['station_no'])
                            env[no_model].sudo().search([('review_id', '=', review_id)]).unlink()

            env[model].sudo().browse(review_id).write({"po_attend_user_ids": data['po_attend_user_ids']})
            result_object = env[model].sudo().search_read([('id', '=', review_id)])
            if record_status == 1:
                status = changeCount(env, result_object[0])
                if not status['success']:
                    rp = {'status': 200, 'data': [], 'dataProject': [], 'message': status['message'],
                          'success': False}
                    return json_response(rp)
            getSigner(env, result_object)
            for r in result_object:
                for f in r.keys():
                    if f == "station_no":
                        r["station_desc"] = sta.getStionsDesc(r[f])
                if r["signer"] and r["signer"][0] == env.uid and r["status_id"] != 1:
                    r["status_id"] = 0
            success_email = True
            if result_object:
                result_object = result_object[0]
                result_object['type'] = type
                if result_object['signer'] and record_status > 0:
                    from . import send_email
                    email_obj = send_email.Send_email()
                    uid = result_object['signer'][0]
                    # fromaddr = "crm@szsunray.com"
                    # qqCode = "Sunray201911"
                    sbuject = "PO申请单待审核通知"
                    # to = ["yangyouhui@szsunray.com"]
                    to = ["leihui@szsunray.com"]
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        to = [request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)["email"]]
                    token = get_token(env, uid)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/reports-U8-PO-list/' + str(
                        review_id) + "/" + json.dumps(token)
                    content = """
                            <html lang="en">            
                            <body>
                                <div>
                                    您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核采购PO申请单，请点击
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

    @http.route([
        '/api/v11/report/getPoList/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_po_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        # token = token if token else get_token(1).pop('token').pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        fields = eval(kw.get('fields',
                             "['iscreatepo','id','cpoid','cvencode','cvenname','signer','signer_nickname','status_id','station_no','init_usernickname','init_time','init_user','update_time','update_usernickname','isback','po_attend_user_ids']"))
        order = kw.get('order', "update_time desc")
        if kw.get("data"):
            json_data = kw.get("data").replace('null', 'None')
            queryFilter = ast.literal_eval(json_data)
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("cvenname"):
                domain.append(('cvenname', 'ilike', queryFilter.get("cvenname")))
            if queryFilter and queryFilter.get("init_usernickname"):
                domain.append(('init_usernickname', 'ilike', queryFilter.get("init_usernickname")))
            if queryFilter and queryFilter.get("status_id"):
                if queryFilter.get("status_id") != '':
                    if queryFilter.get("status_id") == 0:  # 0表示待签核人
                        domain.append(('signer', '=', env.uid))
                    else:
                        domain.append(('status_id', '=', queryFilter.get("status_id")))

            if queryFilter and queryFilter.get("sdate"):
                domain.append(('init_time', '>=', queryFilter.get("sdate")))
            if queryFilter and queryFilter.get("edate"):
                domain.append(('init_time', '<=', queryFilter.get("edate")))
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
                domain += ['&', ('record_status', '=', 1), '|', ('po_attend_user_ids', 'ilike', records_ref.id)]
                domain += [('init_user', 'in', records_ref.child_ids_all.ids)]
            count = request.env[model].sudo().search_count(domain)
            if queryFilter.get("order_field") and queryFilter.get("order_field") != 'status_id':
                result = request.env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            else:
                result = request.env[model].sudo().search_read(domain, fields, order=order)
            getSigner(env, result)
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

    @http.route([
        '/api/v11/report/getPoReview',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_po_review(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        result = env['report.pobase'].sudo().search_read([('id', '=', kw.get('id'))])[0]
        result['others'] = eval(result['others'])
        result['reviewers'] = eval(result['reviewers'])
        result = dict(filter(lambda x: x[1], result.items()))
        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getPoReviewDetail',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_po_review_detail(self, model=None, ids=None, **kw):
        success, message, ret_temp, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        review_id = int(kw.get("id"))
        if review_id:
            domain.append(('id', '=', review_id))
            domain = searchargs(domain)
            try:
                result = request.env['report.pobase'].sudo().search_read(domain)
                if result:
                    obj_temp = result[0]
                    ap = Stations('帐期额度申请单')
                    # 判断signer
                    signer = str(obj_temp["signer"][0]) if obj_temp["signer"] else obj_temp["signer"]
                    station_no = obj_temp["station_no"]
                    si_station = station_no
                    if station_no and station_no == 28:
                        _station = env['reports.po.partial'].sudo().search_read(
                            [('review_id', '=', review_id)], order='init_time desc',
                            limit=1)
                        _station = _station if _station and _station[0]['sign_over'] == 'N' else ''
                        to_station = _station[0]['to_station'].split(',')[:-1] if _station else []
                        sign_station = _station[0]['sign_station'].split(',')[:-1] if _station and _station[0][
                            'sign_station'] else []
                        ne_station = list(set(to_station) - set(sign_station))
                        signer = ''
                        for sta in ne_station:
                            sig = env['report.po.signers'].sudo().search_read(
                                [('review_id', '=', review_id), ('station_no', '=', int(sta))])
                            if sig:
                                if signer:
                                    signer = signer + ',' + sig[0]['signers']
                                else:
                                    signer = sig[0]['signers']

                                if str(env.uid) in signer.split(',') and str(env.uid) in sig[0]['signers'].split(','):
                                    si_station = int(sta)

                    # 判断是否有回签
                    from_station_ = env['reports.po.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    from_station = from_station_[0]['from_station'] if from_station_ and from_station_[0][
                        'sign_over'] == 'N' else ''
                    # PM 填写
                    pm_res = env['report.popm'].sudo().search_read([('review_id', '=', review_id)])
                    pm = dict(filter(lambda x: x[1], pm_res[0].items())) if pm_res else {}
                    if not pm:
                        others = []
                        base_others = eval(obj_temp['others'])
                        for res in base_others:
                            pools = res['pools']
                            for pol in pools:
                                oth_tmp = {}
                                oth_tmp['cinvcode'] = pol['cbdefine22']
                                oth_tmp['count'] = pol['cbdefine27']
                                oth_tmp['unit_price'] = pol['cbdefine23']
                                oth_tmp['money'] = res['imoney']
                                oth_tmp['end_customers'] = pol['cbdefine21']
                                oth_tmp['cpoid'] = obj_temp['cpoid']
                                others.append(oth_tmp)
                        pm['others'] = others
                        pm['supplier_c'] = obj_temp['cvenname']
                        pm['apply_user'] = obj_temp['init_usernickname']
                        pm['apply_date'] = datetime.date.today()
                        pm['amount'] = sum(map(lambda x: x['money'], others))
                        pm['a_company'] = '香港新蕾'
                    else:
                        pm['others'] = eval(pm['others'])

                    pm['account'] = obj_temp['cname']
                    # PMM 填写
                    pmm_res = env['report.popmm'].sudo().search_read([('review_id', '=', review_id)])
                    pmm = dict(filter(lambda x: x[1], pmm_res[0].items())) if pmm_res else {}
                    # coo 填写
                    coo_res = env['report.pocoo'].sudo().search_read([('review_id', '=', review_id)])
                    coo = dict(filter(lambda x: x[1], coo_res[0].items())) if coo_res else {}
                    # ceo 填写
                    ceo_res = env['report.poceo'].sudo().search_read([('review_id', '=', review_id)])
                    ceo = dict(filter(lambda x: x[1], ceo_res[0].items())) if ceo_res else {}
                    ret_temp = {
                        "id": obj_temp["id"],
                        "pm": pm,
                        "pmm": pmm,
                        "coo": coo,
                        "ceo": ceo,
                        'from_station': from_station if from_station else obj_temp["station_no"],
                        'si_station': si_station,
                        'signer': signer
                    }
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': ret_temp}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/poReview/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_poReview(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            account = Stations('PO申请单')
            data = ast.literal_eval(list(kw.keys())[0].replace('null', '')).get("data")
            data.pop('backreason')
            updatePOReview(model, data, env)
            review_id = data.get('review_id')
            result = env[model].sudo().search_read([('id', '=', review_id)])
            getSigner(env, result)
            if result:
                result = result[0]

        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getCommitListByPOId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_commit_list_by_po_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        result = []
        rejects_result = []
        if not env:
            return no_token()
        if kw.get("review_id"):
            review_id = int(kw.get("review_id"))
            try:
                account = Stations("PO申请单")
                current_sta = env['report.pobase'].sudo().search([("id", '=', review_id)])
                if current_sta:
                    current_sta = current_sta[0]
                    current_station = current_sta["station_no"]
                    records_ref = env['report.po.signers'].sudo().search_read([("review_id", '=', review_id)])
                    records_ref = filter(lambda x: x['station_no'] > 1, records_ref)
                    if records_ref:
                        for item in records_ref:
                            station_no = item["station_no"]
                            signer_model = account.getModel(station_no)
                            domain = [("review_id", '=', review_id)]
                            signer_info = env[signer_model].sudo().search_read(domain)
                            uid = item["signers"]
                            station_desc = account.getStionsDesc(station_no)
                            timestamp = ''
                            signed = False
                            if current_station == 28:
                                back = env['reports.po.partial'].sudo().search_read([('review_id', '=', review_id)],
                                                                                    order='init_time desc',
                                                                                    limit=1)
                                if back and back[0]['from_station'] > station_no:
                                    signed = True
                            elif current_station > station_no:
                                signed = True
                            if signer_info:
                                # if station_no == 45:
                                #     uid =
                                if '[' in str(uid):
                                    uid = eval(str(uid))
                                    uid = [uid] if isinstance(uid, list) else list(uid)
                                else:
                                    uid = str(uid).split(',')

                                for item in signer_info:
                                    uid_a = item["update_user"][0]
                                    signer = env['xlcrm.users'].sudo().search([("id", '=', uid_a)])
                                    description = signer[0]['nickname'] + ' (' + station_desc + ')'
                                    if current_station == station_no:
                                        if item["update_time"].split(':')[:-1] == current_sta['update_time'].split(':')[
                                                                                  :-1]:
                                            signed = True
                                        else:
                                            signed = False
                                    if signed:
                                        timestamp = item["update_time"]
                                    result.append(
                                        {"station_no": station_no, "description": description, "timestamp": timestamp,
                                         "signed": signed})
                                    if isinstance(uid[0], str):
                                        if str(uid_a) in uid:
                                            uid.remove(str(uid_a))
                                        if uid_a in uid:
                                            uid.remove(uid_a)
                                    elif isinstance(uid[0], list) or isinstance(uid, list):
                                        if uid_a == uid[0] or uid_a in uid[0]:
                                            uid.remove(uid[0])

                                for u in uid:
                                    signed = False
                                    signer = env['xlcrm.users'].sudo().search([("id", '=', u)])
                                    description = signer[0]['nickname'] + ' (' + station_desc + ')'
                                    result.append(
                                        {"station_no": station_no, "description": description, "timestamp": '',
                                         "signed": signed})
                            else:
                                uid = list(set(str(uid).split(',')))
                                nickname = ','.join(
                                    map(lambda x: x['nickname'], env['xlcrm.users'].sudo().search_read(
                                        [('id', 'in', filter(lambda x: x, uid))])))
                                if nickname:
                                    description = nickname + ' (' + station_desc + ')'
                                    result.append(
                                        {"station_no": station_no, "description": description,
                                         "timestamp": timestamp,
                                         "signed": signed})
                    init_user = env["xlcrm.users"].sudo().search_read([("id", "=", current_sta["init_user"]["id"])])[0][
                        "nickname"]
                    init_time = current_sta["init_time"]
                    # result.append(
                    #     {"station_no": 1, "description": str(init_user) + " (送出)", "timestamp": init_time})
                rejects = env['report.po.reject'].sudo().search_read([('review_id', '=', review_id)])
                if rejects:
                    for reject in rejects:
                        station_desc = account.getStionsDesc(reject['station_no']).replace('签核', '')
                        reason = [reject['reason']]
                        init_user = env["xlcrm.users"].sudo().search_read([("id", "=", reject["init_user"][0])])[0][
                            "nickname"]
                        init_time = reject["init_time"]
                        rejects_result.append(
                            {"description": station_desc + ' ' + init_user + " (驳回)", "timestamp": init_time,
                             'reason': reason})
                partials = env['reports.po.partial'].sudo().search_read([('review_id', '=', review_id)])
                if partials:
                    for partial in partials:
                        station_desc = account.getStionsDesc(partial['from_station']).replace('签核', '')
                        init_user = env["xlcrm.users"].sudo().search_read([("id", "=", partial["init_user"][0])])[0][
                            "nickname"]
                        init_time = partial["init_time"]
                        reason = []
                        to_station = partial["to_station"].split(',')[:-1]
                        a = -1
                        for i in range(len(to_station)):
                            desc = account.getStionsDesc(int(to_station[i])).replace('签核', '')
                            a += 1
                            remark = partial["remark"].split("\p")[:-1]
                            reason.append(desc + '::--->' + remark[a])
                        rejects_result.append(
                            {"description": station_desc + ' ' + init_user + " (部分驳回)", "timestamp": init_time,
                             'reason': reason})

                success = True
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        result.sort(key=lambda x: x["station_no"])
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'rejects_data': rejects_result,
              'total': count}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/reCallByPOId',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def recall_po(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            review_id = ast.literal_eval(kw.get("review_id"))
            data = {}
            model = 'report.pobase'
            data['station_no'] = 1
            data['signer'] = env.uid
            data["update_user"] = env.uid
            data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            data['signer'] = env.uid
            data['status_id'] = 1
            data['isback'] = 2
            data['station_desc'] = '申请者填单'
            env[model].sudo().browse(review_id).write(data)
            # 判断是否回签
            sign_back = env['reports.po.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)
            if sign_back and sign_back[0]['sign_over'] == 'N':
                env['reports.po.partial'].sudo().browse(sign_back[0]['id']).write(
                    {'sign_station': sign_back[0]['to_station']})
            result_object = env[model].sudo().search_read([('id', '=', review_id)])
            status = changeCount(env, result_object[0], 'plus')
            if not status['success']:
                rp = {'status': 200, 'message': status['message'], 'data': '', 'success': False}
                return json_response(rp)
            success_email = True
            if result_object:
                result_object = result_object[0]
                result_object['login_user'] = env.uid
                result_object['type'] = 'set'
                if result_object['signer']:
                    from . import send_email
                    email_obj = send_email.Send_email()
                    uid = result_object['signer'][0]
                    # fromaddr = "crm@szsunray.com"
                    # qqCode = "Sunray201911"
                    sbuject = "采购PO申请单待审核通知"
                    to = ["leihui@szsunray.com"]
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        to = [request.env['xlcrm.users'].sudo().search([('id', '=', uid)], limit=1)["email"]]
                    token = get_token(env, uid)
                    href = request.httprequest.environ[
                               "HTTP_ORIGIN"] + '/#/public/reports-U8-PO-list/' + str(
                        review_id) + "/" + json.dumps(token)
                    content = """
                                <html lang="en">            
                                <body>
                                    <div>
                                        您好：<br><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;您有待审核采购PO申请单，请点击
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
        rp = {'status': 200, 'message': message, 'data': result_object, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/partialPORejection',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_popartial(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = ast.literal_eval(list(kw.keys())[0]).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kw):
            return no_sign()
        try:
            ap = Stations('PO申请单')
            review_id = int(data.pop('review_id'))
            from_station = data.pop('from_station')
            record_status = data.pop('record_status')
            par = env['reports.po.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)
            p_id = par[0]['id'] if par else ''
            if par:
                data['from_id'] = par[0]['id']
                if par[0]['from_station'] == from_station and par[0]['sign_over'] == 'N':
                    env['reports.po.partial'].sudo().browse(par[0]['id']).write(data)
                else:
                    p_id = env['reports.po.partial'].sudo().create(data).id
            else:
                p_id = env['reports.po.partial'].sudo().create(data).id
            to_station = ''
            remark = ''
            if data:
                from_id = data.pop('from_id') if data.get('from_id') else ''
                for key, value in data.items():
                    station = ap.getStaionsReject(key)
                    remark += value['back_remark'] + '\p'
                    to_station += str(station) + ','
            data['review_id'] = review_id
            data['from_station'] = from_station
            data['to_station'] = to_station
            data['remark'] = remark
            data["init_user"] = env.uid
            env['reports.po.partial'].sudo().browse(p_id).write(data)

            if record_status == 1:
                data_up = {'station_no': 28, 'station_dec': ap.getStionsDesc(28),
                           'update_time': datetime.datetime.now() + datetime.timedelta(hours=8),
                           'update_user': env.uid, 'signer': ''}
                env['report.pobase'].sudo().browse(review_id).write(data_up)
                env.cr.commit()
            result = env['report.pobase'].sudo().search_read([('id', '=', review_id)])
            getSigner(env, result)
            from . import send_email
            email_obj = send_email.Send_email()
            success_email, send_wechart = True, True
            if result:
                result = result[0]
            if result['signer']:
                uid = result['signer']
                for ui in uid:
                    sbuject = "采购PO申请单待审核通知"
                    to = ["leihui@szsunray.com"]
                    to_wechart = '雷辉，lucas'
                    cc = []
                    if odoo.tools.config["enviroment"] == 'PRODUCT':
                        user = env['xlcrm.users'].sudo().search([('id', '=', ui)], limit=1)
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
                    msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                    if msg["code"] == 500:  # 邮件发送失败
                        success_email = False

            message = "success"
            success = True
            if success_email and send_wechart:
                env.cr.commit()

        except Exception as e:
            result, message, success = '', str(e), False
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success, 'dataProject': result}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/createU8PO',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_U8PO(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            import requests, urllib.parse, time, json
            data = ast.literal_eval(kw.get("data"))
            model = 'report.pobase'
            url = "http://192.168.0.159:8049"
            review_id = int(data['review_id'])
            UserID = data.get('UserID')
            Password = data.get('Password')
            params = {
                'loginInfo': {'sAccID': '601',
                              'sLoginDate': datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d'),
                              'sUserID': UserID, 'sPassword': Password}}

            response = requests.get(url=url + '/api/Login?%s' % urllib.parse.urlencode(params))

            if response.status_code == 200:
                content = response.json()
                token = content['ccode']
                res = env[model].sudo().search_read([('id', '=', review_id)], limit=1)[0]
                ohters = eval(res['others'])
                podetails = []
                i = 0
                for ot in ohters:
                    for rs in ot['pools']:
                        i += 1
                        tmp = ot
                        tmp["id"] = i
                        tmp["poid"] = 1001
                        tmp["sotype"] = str(tmp['sotype'])
                        tmp["ipertaxrate"] = float(tmp['ipertaxrate'])
                        tmp["iunitprice"] = float(tmp['iunitprice'])
                        tmp["inattax"] = float(tmp['inattax'])
                        tmp["darrivedate"] = tmp['darrivedate'].split('T')[0] if tmp['darrivedate'] else ''
                        tmp.update(rs)
                        # tmp['cdemandmemo'] = 'fsd'
                        # tmp['cdemandmemo']=tmp['cdemandmemo'].decode()
                        podetails.append(tmp)
                formData = {
                    "poid": 1001,
                    "cbustype": res['cbustype'],
                    "cptcode": res['cptcode'],
                    "itaxrate": res['itaxrate'],
                    "dpodate": res['dpodate'],
                    "cpoid": res['cpoid'],
                    "cvencode": str(res['cvencode']),
                    "cvenname": res['cvenname'],
                    "ccontactcode": res['ccontactcode'],
                    "cvenperson": res['cvenperson'],
                    "cexch_name": res['cexch_name'],
                    "nflat": res['nflat'],
                    "cmaker": res['cmaker'],
                    "cdepcode": res['cdepcode'],
                    "cpersoncode": res['cpersoncode'],
                    "idiscounttaxtype": res['idiscounttaxtype'],
                    "cvenpuomprotocol": res['cvenpuomprotocol'],
                    "ufts": str(time.time()),
                    "cmemo": "",
                    "podetails": podetails
                }

                # formData = json.loads(json.dumps(formData).encode('utf-8'))
                params = {
                    "token": token,
                    "formData": formData

                }
                params = json.dumps(params)
                header = {
                    'content-type': 'application/json; charset=utf-8',
                    "Accept-Encoding": "gzip, deflate",
                    "User-Agent": "Mozilla/5.0 (X11;Ubuntu;Linux x86_64;rv:87.0) Gecko/20100101 Firefox/87.0"
                }
                response = requests.post(url='%s/api/Po/AddPoOrder' % url, data=params, headers=header)
                if response.status_code == 200:
                    res = response.json()
                    if res['result'] == 'true':
                        env['report.pobase'].sudo().browse(review_id).write(
                            {'update_time': datetime.datetime.now() + datetime.timedelta(hours=8),
                             'update_user': env.uid, 'iscreatepo': True})
                        env.cr.commit()
                        success = True
                        message = "创单成功，请进入U8确认"
                    else:
                        success = False
                        message = res['ccode']
            # token=response.text
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/report/getReportsDept'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getReportsDept(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', {}, 100, 1, 50
        token = kw.pop('token')
        env = authenticate(token)
        mssql = Mssql("stock")
        if not env:
            return no_token()

        data = eval(kw.get("data"))
        try:
            username = env['xlcrm.users'].sudo().search_read([('id', '=', env.uid)])[0]['nickname']
            sql_dept = "select distinct cDept from DispatchLists where exists (select *from DispatchLists_power where uid=%d) or cDept like '%s'" % (
                env.uid, '%' + username.encode() + '%')
            res_dept = mssql.query(sql_dept)
            result['deptdata'] = map(lambda x: x[0], res_dept) if res_dept else []
            domain = ""
            if data['dept']:
                domain = " and cDept = '%s'" % data['dept']
                if data['dept'] == '仅自己部分':
                    domain = " and cUserName ='%s' " % username
                if data['dept'] == 'ALL':
                    domain = ""
            else:
                domain = " and cDept = '%s'" % result['deptdata'][0]
                if filter(lambda x: username in x, result['deptdata']):
                    result['deptdata'].insert(0, '仅自己部分')
                    domain = " and cUserName ='%s' " % username
                else:
                    result['deptdata'].insert(0, 'ALL')
                    domain = ""
            domain += " and YEAR(dDate)=%d" % data['ydate']
            x_range = []
            sql_labels, res_labels, group_date = '', [], ''
            if data['reporttype'] == '按月分析':
                x_range = range(1, 13)
                group_date = 'MONTH(dDate)'
            if data['reporttype'] == '按季度分析':
                x_range = range(1, 5)
            if data['reporttype'] == '按周分析':
                x_range = range(1, 6)
                group_date = 'DATEPART(WK,dDate)'
                domain += " and MONTH(dDate)=%d" % data['mdate']
            analy_type = 'cCusName' if data['status_id'] == 0 else 'brandName'
            sql_labels = "select top 10 * from(select %s,sum(iMoney) as imoney from DispatchLists where 1=1 %s " \
                         "group by %s) a order by imoney desc" % (analy_type, domain, analy_type)
            res_labels = mssql.query(sql_labels)
            result['labels'] = map(lambda x: x[0], res_labels) if res_labels else []
            # group = 'cCusName' if data['status_id'] == 0 else 'brandName'
            sql_ydata = "select %s,sum(iMoney) as imoney,%s as mon from DispatchLists where 1=1 " % (analy_type,
                                                                                                     group_date) + domain + " and %s in ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') group by %s,%s" % tuple(
                [analy_type] + result['labels'] + [''] * (10 - len(result['labels'])) + [analy_type, group_date])
            if data['reporttype'] == '按季度分析':
                sql_ydata = " select %s,iMoney,case when MONTH(dDate) between 1 and 3 then 1 when MONTH(dDate) between 4 and 6 then 2 " \
                            " when MONTH(dDate) between 7 and 9 then 3 else 4 end as quart From DispatchLists where 1=1 " % analy_type + domain + " and %s in ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % tuple(
                    [analy_type] + result['labels'] + [''] * (10 - len(result['labels'])))
                sql_ydata = " select %s,sum(iMoney) as imoney,quart from (%s) a group by %s,quart" % (
                    analy_type, sql_ydata, analy_type)
            res_ydata = mssql.query(sql_ydata)
            ydata = {}
            if data['reporttype'] == '按周分析':
                x_range = map(lambda x: x[2], res_ydata)
                x_range = list(set(x_range))
                x_range.sort()
            for cus in result['labels']:
                ytmp = []
                for ran in x_range:
                    da = filter(lambda x: x[2] == ran and x[0] == cus, res_ydata)
                    ytmp.append(round(da[0][1] / 1000000, 2) if da else 0)
                ydata[cus] = ytmp
            result['ydata'] = ydata
            result['xdata'] = x_range  # map(lambda x:str(x),x_range)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            mssql.close()
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getAccountBankFromU8',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_bank(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        from .connect_mssql import Mssql
        import odoo
        con_str = '158_999'
        if odoo.tools.config["enviroment"] == 'PRODUCT':
            con_str = '154_999'
        mssql = Mssql(con_str)
        res = mssql.query("select ID,lYear,AcctName,a_company,UnitName from v_CN_AcctInfo")
        result = list(map(lambda x: {"id": x[0], "year": x[1], "bank": x[2], "a_company": x[3], "company": x[4]}, res))
        rp = {'status': 200, 'message': message, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getBankJournalList',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_bank_journal_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', [], 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            bank, period, company = '', '', ''
            if kw.get("data"):
                json_data = kw.get("data").replace('null', 'None')
                query_filter = ast.literal_eval(json_data)
                offset = query_filter.pop("page_no") - 1
                limit = query_filter.pop("page_size")
                bank = query_filter.get('bank')
                period = query_filter.get('period')
                company = query_filter.get('company')
            from .connect_mssql import Mssql
            from .public import u8_account_name, get_first_day
            import odoo
            con_str, enviroment = '158_999', odoo.tools.config["enviroment"]
            if enviroment == 'PRODUCT':
                con_str = '154_999'
            mssql = Mssql(con_str)
            start_date = f"{period[0][:4]}-{period[0][4:]}-01"
            end_date = datetime.datetime.strptime(f"{get_first_day(period[1][:4], period[1][4:])}-01",
                                                  "%Y-%m-%d") - datetime.timedelta(days=1)
            # end_date = f"{get_first_day(period[1][:4], period[1][4:])}-01"
            # 获取账套
            query_a = [" 1=1"]
            if bank:
                query_a.append(f"B.AcctName='{bank}'")
            if company:
                query_a.append(f"B.Unitname='{company}'")
            sql_a = f"select distinct B.a_company from v_CN_AcctInfo B where {' and '.join(query_a)}"
            res = mssql.query(sql_a)
            a_companys = list(map(lambda x: x[0], res))
            sql_list = []
            for a_company in a_companys:
                db = u8_account_name(a_company, enviroment)
                if "Unitname" in query_a[-1]:
                    query_a.pop()
                sql_list.append(
                    f"select B.UnitName,B.AcctName,A.CurTypeName,isnull(C.mb,0)+sum(Debit)-sum(Credit) as yu,'{a_company}' as a_company,A.lYear,A.Period,B.csAcctNum from {db}.dbo.CN_AcctBookView A"
                    f" LEFT JOIN {db}.dbo.CN_AcctInfo B on A.AcctID=B.ID"
                    f" LEFT JOIN {db}.dbo.GL_accsum C on A.Period=C.iperiod and A.lYear=C.iyear and B.SubjectCode=C.ccode"
                    f" where {' and '.join(query_a)} and A.AcctDate between '{start_date}' and '{end_date}' and A.IsDelete<>1 AND A.AcctType<>2 AND A.ID_Old=A.ID"
                    f" group by B.UnitName,B.AcctName,A.CurTypeName,C.mb,A.lYear,A.Period,B.csAcctNum")
            res = mssql.query(' union '.join(sql_list))
            for _res in res:
                tmp = {}
                period = f"{_res[5]}{str(_res[6]).zfill(2)}"
                tmp['company'] = _res[0]
                tmp['bank'] = _res[1]
                tmp['currency'] = _res[2]
                tmp['balance'] = _res[3]
                tmp['a_company'] = _res[4]
                tmp['period'] = period
                tmp['bank_code'] = _res[7]
                f_fmt = f"{period}_{tmp['a_company']}_{_res[7].replace(':', '')}"
                filename = env['xlcrm.documents'].sudo().search(
                    [('res_model', '=', 'reports.accountStatement'), ('datas_fname', '=', f_fmt)],
                    order='write_date desc', limit=1)
                files = []
                if filename:
                    files.append({
                        "filename": f"{f_fmt}.{filename.name.rsplit('.', 1)[-1]}" if filename else '',
                        "file_url": f"{odoo.tools.config['serve_url']}/smb/file/{filename.id}" if filename else ''
                    })
                filename2 = env['xlcrm.documents'].sudo().search(
                    [('res_model', '=', 'reports.accountStatement'), ('datas_fname', '=', f_fmt),
                     ('mimetype', '!=', filename.mimetype)],
                    order='write_date desc', limit=1)
                if filename2:
                    files.append({
                        "filename": f"{f_fmt}.{filename2.name.rsplit('.', 1)[-1]}" if filename2 else '',
                        "file_url": f"{odoo.tools.config['serve_url']}/smb/file/{filename2.id}" if filename2 else ''
                    })
                tmp["files"] = files
                tmp["filenames"] = '、'.join(list(map(lambda x: x["filename"], files)))
                result.append(tmp)
            message = "success"
            count = len(result)
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getBankJournalDetail',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_bank_journal_detail(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', [], 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            bank, period, company, a_company = '', '', '', ''
            if kw.get("data"):
                json_data = kw.get("data").replace('null', 'None')
                query_filter = ast.literal_eval(json_data)
                bank = query_filter.get('bank')
                period = query_filter.get('period')
                company = query_filter.get('company')
                a_company = query_filter.get('a_company')
            from .connect_mssql import Mssql
            from .public import u8_account_name
            import odoo
            import copy
            con_str, enviroment = '158_999', odoo.tools.config["enviroment"]
            if enviroment == 'PRODUCT':
                con_str = '154_999'
            mssql = Mssql(con_str)
            # lyear, lperiod = period[:4], int(period[4:])
            start_date = f"{period[:4]}-{period[4:]}-01"
            # end_date = f"{get_first_day(period[:4], period[4:])}-01"
            end_date = datetime.datetime.strptime(f"{get_first_day(period[:4], period[4:])}-01",
                                                  "%Y-%m-%d") - datetime.timedelta(days=1)
            # 获取账套
            query_a = [" 1=1"]
            if bank:
                query_a.append(f"B.AcctName='{bank}'")
            if company:
                query_a.append(f"B.Unitname='{company}'")
            db = u8_account_name(a_company, enviroment)
            sql_ = f"select A.Period,convert(date,A.AcctDate) as AcctDate,B.UnitName,A.Summary,A.CurTypeName,A.Debit,A.Credit,A.cCusName,cVenName,C.mb from {db}.dbo.CN_AcctBookView A" \
                   f" LEFT JOIN {db}.dbo.CN_AcctInfo B on A.AcctID=B.ID" \
                   f" LEFT JOIN {db}.dbo.GL_accsum C on A.Period=C.iperiod and A.lYear=C.iyear and B.SubjectCode=C.ccode " \
                   f" where {' and '.join(query_a)} and A.AcctDate between '{start_date}' and '{end_date}' and A.IsDelete<>1 AND A.AcctType<>2 AND A.ID_Old=A.ID order by A.AcctDate"
            res = mssql.query(sql_)
            for _res in res:
                tmp = {}
                tmp['period'] = period
                tmp['a_company'] = a_company
                tmp['bank'] = bank
                tmp['acctdate'] = _res[1]
                tmp['company'] = _res[2]
                tmp['summary'] = _res[3]
                tmp['currency'] = _res[4]
                tmp['debit'] = _res[5]
                tmp['credit'] = _res[6]
                tmp['ccusname'] = _res[7]
                tmp['cvenname'] = _res[8]
                tmp['mb'] = _res[9]
                result.append(tmp)
            l_res = len(result)
            mb = result[0]['mb'] if l_res > 0 and result[0]['mb'] else 0
            for index, res in enumerate(result):
                if index == 0:
                    res["yu"] = mb + res['debit'] - res['credit']
                else:
                    res["yu"] = result[index - 1]["yu"] + res['debit'] - res['credit']
            fin_res = copy.deepcopy(result)
            debit, m_debit, credit, m_credit, index = 0, 0, 0, 0, 0
            for i in range(l_res):
                debit += result[i]["debit"]
                credit += result[i]["credit"]
                m_debit += result[i]["debit"]
                m_credit += result[i]["credit"]
                if i == l_res - 1 or result[i]["acctdate"] != result[i + 1]["acctdate"]:
                    fin_res.insert(i + 1 + index, {"period": "", "a_company": "",
                                                   "debit": debit, "credit": credit, "yu": result[i]["yu"],
                                                   "bank": "", "acctdate": "日合计", "company": "",
                                                   "summary": "", "currency": "", "ccusname": "", "cvenname": ""
                                                   })
                    debit, credit = 0, 0
                    index += 1
                if i == l_res - 1:
                    fin_res.append({"period": "", "a_company": "",
                                    "debit": m_debit, "credit": m_credit, "yu": result[i]["yu"],
                                    "bank": "", "acctdate": "月合计", "company": "",
                                    "summary": "", "currency": "", "ccusname": "", "cvenname": ""
                                    })
            message = "success"
            count = len(result)
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': fin_res, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getExpenseList',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_expense_list(self, model=None, ids=None, **kw):
        success, message, result, u8_expense_data, count, offset, limit = True, '', [], [], 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            apply_name, send_time, dept_name, pay_time = '', '', '', ''
            if kw.get("data"):
                json_data = kw.get("data").replace('null', 'None')
                query_filter = ast.literal_eval(json_data)
                apply_name = query_filter.get('apply_name')
                send_time = query_filter.get('send_time')
                dept_name = query_filter.get('dept_name')
                pay_time = query_filter.get('pay_time')
            from .connect_mssql import Mssql
            from .public import u8_account_name
            import odoo
            import copy
            con_str, enviroment = '176', odoo.tools.config["enviroment"]
            if enviroment == 'PRODUCT':
                con_str = '167'
            condition_date,condition_dept = '',''
            if apply_name:
                condition_dept += f" and member.NAME='{apply_name}'"
            if dept_name:
                condition_dept += f" and orgunit.Name='{dept_name}'"
            if send_time:
                condition_date += f" and applyDate between '{send_time[0]}' and '{send_time[-1]}'"
            if pay_time:
                start_date = f"{pay_time[0][:4]}-{pay_time[0][4:]}-01"
                end_date = f"{get_first_day(pay_time[1][:4], pay_time[1][4:])}-01"
                condition_date += f" and paymentDate between '{start_date}' and '{end_date}'"
            mssql = Mssql(con_str)
            sql = f'''
            SELECT  member.Name as applyName,max(orgunit.Name) as depName,
            sum(CASE enumitem.SHOWVALUE WHEN '差旅费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_0,
            sum(CASE enumitem.SHOWVALUE WHEN '招待费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_1,
            sum(CASE enumitem.SHOWVALUE WHEN '办公费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_2,
            sum(CASE enumitem.SHOWVALUE WHEN '房租水电' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_3,
            sum(CASE enumitem.SHOWVALUE WHEN '网络费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_4,
            sum(CASE enumitem.SHOWVALUE WHEN '运输费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_5,
            sum(CASE enumitem.SHOWVALUE WHEN '保险费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_6,
            sum(CASE enumitem.SHOWVALUE WHEN '仓储费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_7,
            sum(CASE enumitem.SHOWVALUE WHEN '包装费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_8,
            sum(CASE enumitem.SHOWVALUE WHEN '装修费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_9,
            sum(CASE enumitem.SHOWVALUE WHEN '长期待摊费用' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_10,
            sum(CASE enumitem.SHOWVALUE WHEN '固定资产' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_11,
            sum(CASE enumitem.SHOWVALUE WHEN '诉讼费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_12,
            sum(CASE enumitem.SHOWVALUE WHEN '审计费 咨询费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_13,
            sum(CASE enumitem.SHOWVALUE WHEN '律师代理费 顾问费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_14,
            sum(CASE enumitem.SHOWVALUE WHEN '业务宣传费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_15,
            sum(CASE enumitem.SHOWVALUE WHEN '代理手续费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_16,
            sum(CASE enumitem.SHOWVALUE WHEN '服务费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_17,
            sum(CASE enumitem.SHOWVALUE WHEN '报关手续费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_18,
            sum(CASE enumitem.SHOWVALUE WHEN '软件服务费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_19,
            sum(CASE enumitem.SHOWVALUE WHEN '商业保险' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_20,
            sum(CASE enumitem.SHOWVALUE WHEN '福利费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_21,
            sum(CASE enumitem.SHOWVALUE WHEN '委托研发' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_22,
            sum(CASE enumitem.SHOWVALUE WHEN '设计费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_23,
            sum(CASE enumitem.SHOWVALUE WHEN '加工费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_24,
            sum(CASE enumitem.SHOWVALUE WHEN '专利费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_25,
            sum(CASE enumitem.SHOWVALUE WHEN '会务费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_26,
            sum(CASE enumitem.SHOWVALUE WHEN '修理费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_27,
            sum(CASE enumitem.SHOWVALUE WHEN '低值易耗品' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_28,
            sum(CASE enumitem.SHOWVALUE WHEN '车船使用税' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_29,
            sum(CASE enumitem.SHOWVALUE WHEN '职工福利费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_30,
            sum(CASE enumitem.SHOWVALUE WHEN '检测费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_31,
            sum(CASE enumitem.SHOWVALUE WHEN '社会保费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_32,
            sum(CASE enumitem.SHOWVALUE WHEN '住房公积金' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_33,
            sum(CASE enumitem.SHOWVALUE WHEN '银行账户内转/公司间往来款' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_34,
            sum(CASE enumitem.SHOWVALUE WHEN '技术服务费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_35,
            sum(CASE enumitem.SHOWVALUE WHEN '银行存款' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_36,
            sum(CASE enumitem.SHOWVALUE WHEN '长期股权投资' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_37,
            sum(CASE enumitem.SHOWVALUE WHEN '律师费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_38,
            sum(CASE enumitem.SHOWVALUE WHEN '审计费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_39,
            sum(CASE enumitem.SHOWVALUE WHEN '审计' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_40,
            sum(CASE enumitem.SHOWVALUE WHEN '咨询费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_41,
            sum(CASE enumitem.SHOWVALUE WHEN '上市中介机构服务费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_42,
            sum(CASE enumitem.SHOWVALUE WHEN '装备调试费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_43,
            sum(CASE enumitem.SHOWVALUE WHEN '交通费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_44,
            sum(CASE enumitem.SHOWVALUE WHEN '汽车费用' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_45,
            sum(CASE enumitem.SHOWVALUE WHEN '电话费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_46,
            sum(CASE enumitem.SHOWVALUE WHEN '快递费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_47,
            sum(CASE enumitem.SHOWVALUE WHEN '物料消耗' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_48,
            sum(CASE enumitem.SHOWVALUE WHEN '劳动保护费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_49,
            sum(CASE enumitem.SHOWVALUE WHEN '职工教育经费' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_50,
            sum(CASE enumitem.SHOWVALUE WHEN '职工薪酬' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_51,
            sum(CASE enumitem.SHOWVALUE WHEN '社会保险' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_52,
            sum(CASE enumitem.SHOWVALUE WHEN '非关联' THEN cast(costAmount AS decimal(10,2)) ELSE 0.00 END) costtype_53,
             isnull(sum(cast(costAmount AS decimal(10,2))),0.00) as costtype_54
            FROM (
            SELECT
                main52.field0002 AS applicant,
                main52.field0080 AS department,
                main52.field0003 AS applyDate,
                main52.field0087 AS paymentDate,
                son53.field0012 AS costType,
                son53.field0014 AS costAmount	
            FROM
                formmain_0104 main52
                LEFT JOIN formson_0105 son53 ON son53.formmain_id = main52.ID	
                where main52.finishedflag=1 
                {condition_date.replace('applyDate','main52.field0003').replace('paymentDate','main52.field0087')}
            UNION ALL SELECT
                main56.field0002 AS applicant,
                main56.field0068 AS department,
                main56.field0004 AS applyDate,
                main56.field0089 AS paymentDate,
                son57.field0012 AS costType,
                son57.field0018 AS costAmount	
            FROM
                formmain_0100 main56
                LEFT JOIN formson_0101 son57 ON son57.formmain_id = main56.ID	
                where main56.finishedflag=1 
                {condition_date.replace('applyDate','main56.field0004').replace('paymentDate','main56.field0089')}
             UNION ALL SELECT
                main60.field0002 AS applicant,
                main60.field0062 AS department,
                main60.field0004 AS applyDate,
                main60.field0111 AS paymentDate,
                son61.field0058 AS costType,
                son61.field0024 AS costAmount	
            FROM
                formmain_0108 main60
                LEFT JOIN formson_0109 son61 ON son61.formmain_id = main60.ID 	
                where main60.finishedflag=1  
                {condition_date.replace('applyDate','main60.field0004').replace('paymentDate','main60.field0111')}
             UNION ALL SELECT
                main64.field0002 AS applicant,
                main64.field0115 AS department,
                main64.field0004 AS applyDate,
                main64.field0057 AS paymentDate,
                son65.field0014 AS costType,
                son65.field0017 AS costAmount	
            FROM
                formmain_0113 main64
                LEFT JOIN formson_0114 son65 ON son65.formmain_id = main64.ID	
                where main64.finishedflag=1 
                {condition_date.replace('applyDate','main64.field0004').replace('paymentDate','main64.field0057')}
             ) a 
             LEFT JOIN ORG_MEMBER member ON member.ID = a.applicant
             LEFT JOIN ORG_UNIT orgunit ON orgunit.ID = a.department
             LEFT JOIN ctp_enum_item enumitem ON enumitem.ID = a.costType
             where enumitem.SHOWVALUE not in ('其他应付款','在建工程','无形资产','安防监控费(HK)','E-FAX(HK)','应交所得税(HK)','董事报酬(HK)','强积金(HK)','业务费(HK)','运输费HK','仓储费HK') 
             {condition_dept}
             GROUP BY member.NAME,orgunit.sort_id
             order by orgunit.sort_id asc
            '''
            message = "success"
            res = mssql.query(sql)
            for _res in res:
                temp = dict()
                temp['applyName'] = _res[0]
                temp['depName'] = _res[1]
                for i in range(55):
                    temp[f"costtype_{i}"] = _res[2 + i]
                result.append(temp)
            start_period = ''.join(pay_time[0].split('-')[:2])
            end_period = ''.join(pay_time[1].split('-')[:2])
            u8_expense_data = get_u8_expense(start_period, end_period)

            count = len(result)
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result,'u8_expense':u8_expense_data, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/reports/getExpenseDetail',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_expense_detail(self, model=None, ids=None, **kw):
        success, message, result, u8_expense_data, count, offset, limit = True, '', [], [], 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            apply_name, send_time, dept_name, pay_time,cost_type = '','', '', '', ''
            if kw.get("data"):
                json_data = kw.get("data").replace('null', 'None')
                query_filter = ast.literal_eval(json_data)
                apply_name = query_filter.get('apply_name')
                dept_name = query_filter.get('dept_name')
                cost_type = query_filter.get('cost_type')
            from .connect_mssql import Mssql
            from .public import u8_account_name
            import odoo
            import copy
            con_str, enviroment = '176', odoo.tools.config["enviroment"]
            if enviroment == 'PRODUCT':
                con_str = '167'
            condition_date,condition_dept = '',''
            if cost_type:
                condition_dept += f" and enumitem.SHOWVALUE='{cost_type}'"
            if apply_name:
                condition_dept += f" and member.NAME='{apply_name}'"
            if dept_name:
                condition_dept += f" and orgunit.Name='{dept_name}'"
            mssql = Mssql(con_str)
            sql = f'''
                SELECT  member.Name as applyName,orgunit.Name as depName,
                a.applyDate,a.paymentDate,enumitem.SHOWVALUE as costType,a.costAmount
                FROM (
                SELECT
                    main52.field0002 AS applicant,
                    main52.field0080 AS department,
                    main52.field0003 AS applyDate,
                    main52.field0087 AS paymentDate,
                    son53.field0012 AS costType,
                    son53.field0014 AS costAmount	
                FROM
                    formmain_0104 main52
                    LEFT JOIN formson_0105 son53 ON son53.formmain_id = main52.ID	
                    where main52.finishedflag=1                     
                UNION ALL SELECT
                    main56.field0002 AS applicant,
                    main56.field0068 AS department,
                    main56.field0004 AS applyDate,
                    main56.field0089 AS paymentDate,
                    son57.field0012 AS costType,
                    son57.field0018 AS costAmount	
                FROM
                    formmain_0100 main56
                    LEFT JOIN formson_0101 son57 ON son57.formmain_id = main56.ID	
                    where main56.finishedflag=1
                 UNION ALL SELECT
                    main60.field0002 AS applicant,
                    main60.field0062 AS department,
                    main60.field0004 AS applyDate,
                    main60.field0111 AS paymentDate,
                    son61.field0058 AS costType,
                    son61.field0024 AS costAmount	
                FROM
                    formmain_0108 main60
                    LEFT JOIN formson_0109 son61 ON son61.formmain_id = main60.ID 	
                    where main60.finishedflag=1
                 UNION ALL SELECT
                    main64.field0002 AS applicant,
                    main64.field0115 AS department,
                    main64.field0004 AS applyDate,
                    main64.field0057 AS paymentDate,
                    son65.field0014 AS costType,
                    son65.field0017 AS costAmount	
                FROM
                    formmain_0113 main64
                    LEFT JOIN formson_0114 son65 ON son65.formmain_id = main64.ID	
                    where main64.finishedflag=1
                 ) a 
                 LEFT JOIN ORG_MEMBER member ON member.ID = a.applicant
                 LEFT JOIN ORG_UNIT orgunit ON orgunit.ID = a.department
                 LEFT JOIN ctp_enum_item enumitem ON enumitem.ID = a.costType
                 where enumitem.SHOWVALUE not in ('其他应付款','在建工程','无形资产','安防监控费(HK)','E-FAX(HK)','应交所得税(HK)','董事报酬(HK)','强积金(HK)','业务费(HK)','运输费HK','仓储费HK') 
                 {condition_dept}
                 order by orgunit.sort_id asc
                '''
            message = "success"
            res = mssql.query(sql)
            for _res in res:
                temp = dict()
                temp['applyName'] = _res[0]
                temp['depName'] = _res[1]
                temp['applyDate'] = _res[2]
                temp['paymentDate'] = _res[3]
                temp['costType'] = _res[4]
                temp['costAmount'] = _res[5]
                result.append(temp)
            count = len(result)
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'data': result, 'u8_expense': u8_expense_data, 'total': count,
              'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/upload/accountStatement'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_account_statement(self, success=False, message='', ret_data='', file='', **kw):
        files = list()
        if file:
            filename = file.filename
            token = kw.pop('token')
            size = kw.pop('fileSize')
            env = authenticate(token)
            if not env:
                return no_token()
            try:
                from .public import save_file
                success, url, name, message = save_file(env.uid, file, 'CRM',
                                                        f"accountStatement/{tools.config['enviroment']}")
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return json_response(rp)
                file_data = {'name': name,
                             'datas_fname': filename.rsplit('.', 1)[0],
                             'res_model': 'reports.accountStatement',
                             'mimetype': file.mimetype,
                             'create_user_id': env.uid,
                             'file_size': size,
                             'type': 'url',
                             'url': url.replace("/", "\\")}
                file1 = env['xlcrm.documents'].sudo().create(file_data)
                files.append({
                    "filename": filename,
                    "file_url": f"{odoo.tools.config['serve_url']}/smb/file/{file1.id}"
                })
                filename2 = env['xlcrm.documents'].sudo().search(
                    [('res_model', '=', 'reports.accountStatement'), ('datas_fname', '=', file1.datas_fname),
                     ('mimetype', '!=', file1.mimetype)],
                    order='write_date desc', limit=1)
                if filename2:
                    files.append({
                        "filename": f"{filename2.datas_fname}.{filename2.name.rsplit('.', 1)[-1]}",
                        "file_url": f"{odoo.tools.config['serve_url']}/smb/file/{filename2.id}"
                    })
                env.cr.commit()
                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'files': files, 'success': success, 'message': message}
        return json_response(rp)

    @http.route(['/smb/file/<int:id>'], csrf=False, type='http', auth="public", cors='*')
    def smb_content_file(self, id, width=0, height=0, download=True, **kw):
        res = request.env['xlcrm.documents'].sudo().search([('id', '=', id)])
        status, headers, content = download_smb_file(res)
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
            image_base64 = content
        else:
            image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
            headers = self.force_contenttype(headers, contenttype='image/png')

        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        aa = response.data
        return response
