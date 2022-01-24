# -*- coding: utf-8 -*-
from odoo import http
import ast
import datetime as dt

from .public import *


class xlRepair(http.Controller):
    @http.route([
        '/api/v11/repair/createRepair'
    ], auth='none', type='http', csrf=False, methods=['POST', 'GET'])
    def create_repair(self, model=None, ids=None, **kw):
        model = 'repair.baseinfo'
        token = kw.pop('token')
        kws = list(kw.keys())[0].replace('null', 'None').replace('false', 'None')
        data = ast.literal_eval(kws).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kws):
            return no_sign()
        try:
            type = 'add'
            record_status = data.get('record_status')
            code = data.get('rep_no')
            res_ex = env[model].sudo().search_read([('code', '=', code)])
            data['testing_engineer'] = ','.join(map(lambda x: str(x), data.get('testing_engineer'))) if data.get(
                'testing_engineer') else ''
            data['customer_service'] = ','.join(map(lambda x: str(x), data.get('customer_service'))) if data.get(
                'customer_service') else ''
            if data['testing_engineer']:
                data['testing_engineer'] = data['testing_engineer'] + ','
            if data['customer_service']:
                data['customer_service'] = data['customer_service'] + ','
            id = 0
            if res_ex:
                id = res_ex[0]['id']
            data['update_user'] = env.uid
            data['update_time'] = dt.datetime.now() + dt.timedelta(hours=8)
            data['station_no'] = 1
            data['status'] = 1
            if record_status == 1:
                data['station_no'] = 5
                data['status'] = 2
                data['signers'] = data.get('testing_engineer', data.get('customer_service', ''))
            if not id:
                data['init_user'] = env.uid
                data['init_time'] = dt.datetime.now() + dt.timedelta(hours=8)
                data['create_date'] = dt.datetime.strptime(str(data['init_time'])[:10], '%Y-%m-%d')
                result_cre = env[model].sudo().create(data)
                id = result_cre.id
            else:
                type = 'set'
                data.pop('init_user')
                env[model].sudo().browse(id).write(data)
            result = env[model].sudo().search_read([('id', '=', id)])
            if result:
                result = result[0]
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message, 'type': type,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getRepairList'
    ], auth='none', type='http', csrf=False, methods=['POST', 'GET'])
    def get_repair_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        model = 'repair.baseinfo'
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        try:
            domain, domain_cs = [], []
            fields = eval(kw.get('fields',
                                 "[]"))
            order = kw.get('order', "update_time desc")
            data = ast.literal_eval(kw.get("data").replace('null', 'None'))
            offset = data.pop("page_no") - 1
            limit = data.pop("page_size")
            if data and data.get('code'):
                domain.append(('code', 'ilike', data.get('code')))
            if data and data.get('customer'):
                domain.append(('customer', 'ilike', data.get('customer')))
            if data and data.get('serial_number'):
                domain.append(('serial_number', 'ilike', data.get('serial_number')))
            if data and data.get('sdate'):
                domain.append(("create_date", '>=', data.get('sdate')))
            if data and data.get('edate'):
                domain.append(("create_date", '<=', data.get('edate')))
            if data and data.get('back_sdate'):
                domain_cs.append(('back_date', '>=', data.get('back_sdate')))
            if data and data.get('back_edate'):
                domain_cs.append(('back_date', '<=', data.get('back_edate')))
            if domain_cs:
                cs_res = env['repair.cs'].sudo().search_read(domain_cs)
                if cs_res:
                    main_id = tuple(map(lambda x: x['review_id'][0], cs_res))
                    domain.append(('id', 'in', main_id))
            # if data and data.get("order_field"):
            #     order = data.get("order_field") + " " + data.get("order_type")
            records_ref = env['xlcrm.users'].sudo().search([("id", '=', env.uid)])
            if (records_ref.group_id.id != 1):
                if (len(domain) > 0):
                    domain = ['&'] + domain
                domain += ['|']
                domain += [('init_user', '=', records_ref.id)]
                domain += ['&', ('record_status', '=', 1), '|', '|',
                           ('testing_engineer', 'ilike', str(records_ref.id) + ','),
                           ('customer_service', 'ilike', str(records_ref.id) + ',')]
                # domain += ['|']
                domain += [('init_user', 'in', records_ref.child_ids_all.ids)]
                # domain += [('customer_service', 'ilike', records_ref.id)]
            count = env[model].sudo().search_count(domain)
            result = env[model].sudo().search_read(domain=domain)
            res_data = []
            for item in result:
                res_tmp = {}
                res_tmp['code'] = item['code']
                res_tmp['customer'] = item['customer']
                res_tmp['maintenance_model'] = item['maintenance_model']
                res_tmp['serial_number'] = item['serial_number']
                res_tmp['create_date'] = item['create_date']
                res_tmp['leading_cadre'] = item['leading_cadre']
                res_tmp['engineer_name'] = item['engineer_name']
                res_tmp['customer_service_name'] = item['customer_service_name']
                res_tmp['sales_business'] = item['sales_business']
                res_tmp['station_no'] = item['station_no']
                res_tmp['init_user'] = item['init_user']
                res_tmp['signers'] = item['signers']
                res_tmp['id'] = item['id']
                res_tmp['totalcount'] = ''
                res_tmp['functional_testing'] = ''
                res_tmp['test_date'] = ''
                res_tmp['led_display'] = ''
                res_tmp['appearance'] = ''
                res_tmp['reproducibility'] = ''
                res_tmp['alarm_record'] = ''
                res_tmp['result'] = ''
                res_tmp['analysis'] = ''
                res_tmp['repair_content'] = ''
                res_tmp['repair_instructions'] = ''
                res_tmp['repair_cost'] = ''
                res_tmp['repair_maintenance_plan'] = ''
                res_tmp['reback'] = ''
                res_tmp['repair'] = ''
                res_tmp['charging_method'] = ''
                res_tmp['charge_date'] = ''
                res_tmp['maintenancea_mount'] = ''
                res_tmp['charge_mount'] = ''
                res_tmp['back_date'] = ''
                res_tmp['remark'] = ''
                ts = env['repair.testing'].sudo().search_read([('review_id', '=', item['id'])])
                if ts:
                    ts = ts[0]
                    totalcount = env['repair.products'].sudo().search_read([('ts_id', '=', ts['id'])])
                    if totalcount:
                        res_tmp['totalcount'] = sum(
                            [int(item_count['count']) if item_count['count'] else 0 for item_count in totalcount])
                    res_tmp['functional_testing'] = ts['functional_testing']
                    res_tmp['test_date'] = ts['test_date']
                    res_tmp['led_display'] = ts['led_display']
                    res_tmp['appearance'] = ts['appearance']
                    res_tmp['reproducibility'] = ts['reproducibility']
                    res_tmp['alarm_record'] = ts['alarm_record']
                    res_tmp['result'] = ts['result']
                    res_tmp['analysis'] = ts['analysis']
                    res_tmp['repair_content'] = ts['repair_content']
                    res_tmp['repair_instructions'] = ts['repair_instructions']
                    res_tmp['repair_cost'] = ts['repair_cost']
                    res_tmp['repair_maintenance_plan'] = ts['repair_maintenance_plan']
                cs = env['repair.cs'].sudo().search_read([('review_id', '=', item['id'])])
                if cs:
                    cs = cs[0]
                    res_tmp['reback'] = cs['reback']
                    res_tmp['repair'] = cs['repair']
                    res_tmp['charging_method'] = cs['charging_method']
                    res_tmp['charge_date'] = cs['charge_date']
                    res_tmp['maintenancea_mount'] = cs['maintenancea_mount']
                    res_tmp['charge_mount'] = cs['charge_mount']
                    res_tmp['back_date'] = cs['back_date']
                    res_tmp['remark'] = cs['remark']
                res_data.append(res_tmp)
            if data.get("order_field"):
                st = False if not data.get("order_type") or data.get("order_type") == "asc" else True
                res_data.sort(key=lambda x: x[data.get("order_field")], reverse=st)
            start = offset * limit
            end = count if count <= offset * limit + limit else offset * limit + limit
            result = res_data[start:end]
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message, 'total': count,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/getRepairDetailById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_repair_detail_by_id(self, model=None, ids=None, **kw):
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
                    # obj_temp['customer'] = obj_temp['customer']['display_name']
                    obj_temp['rep_no'] = obj_temp['code']
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': obj_temp}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getCustomerListBysql'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_getCustomerListBysql(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        try:
            from .connect_psql import Psql
            psql = Psql("ErpCrmDB")
            result = psql.query(
                'select cCusName,cCusPerson,cCusHand,cPersonName,cCusOAddress From v_Customer_CCF')
            psql.close()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/objUpdate/repairReview/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_repair(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        kws = list(kw.keys())[0].replace('null', 'None').replace('false', 'None')
        data = ast.literal_eval(kws).get("data")
        if not env:
            return no_token()
        if not check_sign(token, kws):
            return no_sign()
        try:
            review_id = data.get('review_id')
            station_no = data.get("station_no")
            repair = Stations('维修申请单')
            record_status = data.get('record_status')
            station_model = repair.getModel(station_no)
            result = env[station_model].sudo().search_read([('review_id', '=', review_id), ('init_user', '=', env.uid)])
            if result:
                if data.get('init_user'):
                    data.pop('init_user')
                if data.get('init_time'):
                    data.pop('init_time')
                data.pop('record_status')
                data["update_user"] = env.uid
                data["update_time"] = dt.datetime.now() + dt.timedelta(hours=8)
                env[station_model].sudo().browse(result[0]['id']).write(data)
                if station_model == 'repair.testing':
                    env['repair.products'].sudo().search([('ts_id', '=', result[0]['id'])]).unlink()
                    result_product = [env['repair.products'].sudo().create(dict(item, **{'ts_id': result[0]['id']})) for
                                      item in
                                      data.get('products', [])]
            else:
                data['review_id'] = review_id
                data["init_user"] = env.uid
                data["init_time"] = dt.datetime.now() + dt.timedelta(hours=8)
                data["update_user"] = env.uid
                data["update_time"] = dt.datetime.now() + dt.timedelta(hours=8)
                result = env[station_model].sudo().create(data)
                if station_model == 'repair.testing':
                    result_product = [env['repair.products'].sudo().create(dict(item, **{'ts_id': result.id})) for item
                                      in
                                      data.get('products', [])]
            success_email = True
            if record_status > 0:
                date_main = {}
                if record_status == 1:
                    next_signer = ''
                    next_station = 0
                    current_sig = 'testing_engineer' if station_no == 5 else 'customer_service'
                    while not next_signer:
                        # 首先判断下一站是否有签核人
                        next_station = repair.getnextstation(station_no)
                        next_signer = request.env['repair.baseinfo'].sudo().search_read(
                            [('id', '=', review_id)], ['customer_service'])
                        if next_signer:
                            next_signer = next_signer[0]['customer_service']
                        else:
                            next_signer = ''

                        station_no = next_station
                        if station_no == 99:
                            date_main['status_id'] = 3
                            next_signer = ''
                            break
                    date_main['station_no'] = next_station
                    date_main['signers'] = next_signer
                    date_main['station_desc'] = repair.getStionsDesc(next_station)

                date_main["update_user"] = env.uid
                date_main["update_time"] = dt.datetime.now() + dt.timedelta(hours=8)
                result = env['repair.baseinfo'].sudo().browse(review_id).write(date_main)
            result = env['repair.baseinfo'].sudo().search_read([('id', '=', review_id)])
            for r in result:
                r["station_desc"] = repair.getStionsDesc(r["station_no"])
                ts = env['repair.testing'].sudo().search_read([('review_id', '=', r['id'])])
                if ts:
                    totalcount = env['repair.products'].sudo().search_read([('ts_id', '=', ts[0]['id'])])
                    if totalcount:
                        r['totalcount'] = sum(
                            [int(item_count['count']) if item_count['count'] else 0 for item_count in totalcount])
                cs = env['repair.cs'].sudo().search_read([('review_id', '=', r['id'])])
                if cs:
                    r['reback'] = cs[0]['reback']
            if result:
                result = result[0]
                result['type'] = "set"
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
        return json_response(rp)

    @http.route([
        '/api/v11/getRepairReviewById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_review_by_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []
        filters = []
        result = {}
        id = int(kw.get("id"))
        if id:
            domain.append(('id', '=', id))
            domain = searchargs(domain)
            try:
                station_no = request.env[model].sudo().search_read(domain, ['station_no'])[0]['station_no']
                repair = Stations('维修申请单')
                dict_model = repair.getModelByStaion(station_no)
                base_model = 'repair.'
                for value in dict_model.values():
                    res = env[base_model + value].sudo().search_read([('review_id'
                                                                       , '=', id)], filters)
                    if res:
                        result[value] = res[0]
                        if value == 'testing':
                            ts_id = result[value]['id']  # 查看是否有产品
                            products = env['repair.products'].sudo().search_read([('ts_id', '=', ts_id)])
                            result[value]['products'] = products
                    else:
                        result[value] = {'id': ''}
                message = "success"
                success = True

            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getRepairModel'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_RepairModel(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "['maintenance_model']"))
        try:
            from functools import reduce
            result = [{'value': item['maintenance_model'], 'label': item['maintenance_model']} for item in
                      env['repair.baseinfo'].sudo().search_read(fields=fields)]
            result = list(filter(lambda x: x['value'], reduce(lambda x, y: x if y in x else x + [y], [[], ] + result)))
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getProductList/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_repair_product_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []

        if kw.get("data"):
            queryFilter = ast.literal_eval(kw.get("data"))
            offset = queryFilter.pop("page_no") - 1
            limit = queryFilter.pop("page_size")
            if queryFilter and queryFilter.get("name"):
                domain += ['|']
                domain.append(('name', 'like', queryFilter.get("name")))
                domain.append(('product_no', 'like', queryFilter.get("name")))

        domain = searchargs(domain)
        if ids:
            ids = map(int, ids.split(','))
            domain += [('id', 'in', ids)]
        try:

            result = request.env[model].sudo().search_read(domain, offset=offset * limit, limit=limit)
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

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getProductCount'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_repair_product_count(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()
        domain = []

        try:
            if kw.get("data"):
                queryFilter = ast.literal_eval(kw.get("data"))
                if queryFilter and queryFilter.get("ids"):
                    domain.append(('review_id', 'in', queryFilter.get("ids")))
            domain += [('repair', '=', '是')]
            domain = searchargs(domain)
            result = []
            result_cs = request.env['repair.cs'].sudo().search_read(domain)
            if result_cs:
                review_ids = map(lambda x: x['review_id'][0], result_cs)
                result_ts = env['repair.testing'].sudo().search_read([('review_id', 'in', review_ids)])
                if result_ts:
                    ts_ids = map(lambda x: x['id'], result_ts)
                    result = env['repair.products'].sudo().search_read([('ts_id', 'in', ts_ids)])
                    if result:
                        result = filter(lambda x: int(x['count'] if x['count'] else 0) > 0, result)

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'page': offset + 1,
              'per_page': limit}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getRepairReports'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def getRepairReport(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        data = ast.literal_eval(kw.get("data"))
        ids = data.get('ids')
        try:
            result = env['repair.baseinfo'].sudo().search_read([('station_no', '>', 5), ('id', 'in', ids)])
            if result:
                for item in result:
                    testing = env['repair.testing'].sudo().search_read([('review_id', '=', item['id'])])
                    if testing:
                        testing[0].pop('id')
                        item.update(testing[0])
                    item['repair'] = ''
                    cs = env['repair.cs'].sudo().search_read([('review_id', '=', item['id'])])
                    if cs:
                        cs[0].pop('id')
                        item.update(cs[0])

            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/getChoiceColumns'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_Choice_Columns(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', [], 0, 0, 50
        token = kw.pop('token')
        env = authenticate(token)
        if not env:
            return no_token()

        domain = []
        fields = eval(kw.get('fields', "[]"))
        try:
            result = env['repair.choices'].sudo().search_read([('uid', '=', env.uid)])
            if result:
                result = eval(result[0]['columns'])
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': result, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/repair/saveChoiceColumns'
    ], auth='none', type='http', csrf=False, methods=['POST', 'GET'])
    def save_choice(self, model=None, ids=None, **kw):
        model = 'repair.choices'
        token = kw.pop('token')
        kws = list(kw.keys())[0].replace('null', 'None').replace('false', 'None')
        data = ast.literal_eval(kws).get("data")
        env = authenticate(token)
        if not env:
            return no_token()
        if not check_sign(token, kws):
            return no_sign()
        try:
            res_ex = env[model].sudo().search_read([('uid', '=', env.uid)])
            id = 0
            if res_ex:
                id = res_ex[0]['id']
            data['update_user'] = env.uid
            data['uid'] = env.uid
            data['update_time'] = dt.datetime.now() + dt.timedelta(hours=8)
            if not id:
                data['init_user'] = env.uid
                result_cre = env[model].sudo().create(data)
                id = result_cre.id
            else:
                env[model].sudo().browse(id).write(data)
            message = "success"
            success = True
            env.cr.commit()
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message,
              'success': success}
        return json_response(rp)

    @http.route([
        '/api/v11/saveRepairPart'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def save_repair_part(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = authenticate(token)
        kws = list(kw.keys())[0].replace('null', 'None').replace('false', 'None')
        data = ast.literal_eval(kws).get("data")
        if not env:
            return no_token()
        if not check_sign(token, kws):
            return no_sign()
        try:
            review_id = ''
            repair = Stations('维修申请单')
            for model, val in data.items():
                id = val['id']
                if not review_id:
                    review_id = val.get('id') if model == 'baseinfo' else val.get('review_id')
                if val.get('init_user'):
                    val.pop('init_user')
                if val.get('init_time'):
                    val.pop('init_time')
                val["update_user"] = env.uid
                val["update_time"] = dt.datetime.now() + dt.timedelta(hours=8)
                env['repair.%s' % model].sudo().browse(id).write(val)
                if model == 'testing':
                    products = val.get('products', [])
                    env['repair.products'].sudo().search([('ts_id', '=', id)]).unlink()
                    [env['repair.products'].sudo().create(dict(item, **{'ts_id': id})) for
                     item in products]

            result = env['repair.baseinfo'].sudo().search_read([('id', '=', review_id)])
            for r in result:
                for f in r.keys():
                    if f == "station_no":
                        r["station_desc"] = repair.getStionsDesc(r[f])
                ts = env['repair.testing'].sudo().search_read([('review_id', '=', r['id'])])
                if ts:
                    totalcount = env['repair.products'].sudo().search_read([('ts_id', '=', ts[0]['id'])])
                    if totalcount:
                        r['totalcount'] = sum(
                            [int(item_count['count']) if item_count['count'] else 0 for item_count in totalcount])
                cs = env['repair.cs'].sudo().search_read([('review_id', '=', r['id'])])
                if cs:
                    r['reback'] = cs[0]['reback']
            if result:
                result = result[0]
                result['type'] = "set"
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
        return json_response(rp)
