# -*- coding: utf-8 -*-
from odoo import http
import odoo
from .controllers_base import Base
import datetime
from ..public import CCF


class XlCrmCCF(http.Controller, Base, CCF):
    @http.route([
        '/api/v12/createAccount/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_account2(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0].replace('null', '""')).get("data")
        env = self.authenticate(token)
        env = env
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            data['station_no'] = 1
            data["init_user"] = env.uid
            data["update_user"] = env.uid
            data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            record_status = data.get('record_status')
            data['account_attend_user_ids'] = [[6, 0, []]]
            # data['affiliates'] = [[6, 0, data['affiliates']]]
            self._get_sign_brand_name(data['products'])
            products = data['products']
            data['reviewers']['PM'] = list(map(lambda x: x.get('PM'), products))
            pm_inspector_brand_names, pmins = self.get_pmins(products, env)
            data['reviewers']['PMins'] = pmins
            data['reviewers']['PMM'] = list(map(lambda x: x.get('PMM'), products))
            data['reviewers']['PUR'] = list(map(lambda x: x.get('PUR'), products))
            signers = self.get_user_id(data['reviewers'], env)
            data['signers'] = signers
            if record_status == 1:
                data['reviewers']['Base'] = env.uid
                data['station_no'] = 5
                data['status_id'] = 2
                data['signer'] = ',%s,' % str(signers.get('Sales'))
                data['station_desc'] = '%s(%s)' % (
                    self.get_stations_desc(5),
                    self._get_user_nickname([('id', '=', signers.get('Sales'))], 'nickname', env))
            if not data.get('id'):
                types = 'add'
                data['account_attend_user_ids'][0][2], review_id = self.add(data, products, pm_inspector_brand_names,
                                                                            env)
            else:
                types = 'set'
                data['account_attend_user_ids'][0][2], review_id = self.set(data, products, pm_inspector_brand_names,
                                                                            env)
            env['xlcrm.account.affiliates'].sudo().search([('account', '=', review_id)]).unlink()
            for item in data['affiliates']:
                item['account'] = review_id
                self.create('xlcrm.account.affiliates', item, env)
            env['xlcrm.account.cus'].sudo().search([('review_id', '=', review_id)]).unlink()
            env['xlcrm.account.cus.his'].sudo().search([('review_id', '=', review_id)]).unlink()
            cs, historys = data['cs'], data['cs']['historys']
            if cs:
                cs['review_id'] = review_id
                self.create('xlcrm.account.cus', cs, env)
                for his in historys:
                    his['review_id'] = review_id
                    self.create('xlcrm.account.cus.his', his, env)
            cusdata = data.get('cusdata')
            if cusdata:
                cusdata_999 = dict()
                company_code = env['xlcrm.user.ccfnotice'].sudo().search([('a_company', '=', data['a_company'])],
                                                                         limit=1)
                cusdata['review_id'] = review_id
                cusdata['name'] = data['kc_company']
                cusdata['abbrname'] = data['ccusabbname']
                cusdata['ccusexch_name'] = data['currency']
                cusdata['a_company'] = company_code.a_companycode if company_code else ''
                cusdata_999['review_id'] = review_id
                cusdata_999['name'] = data['kc_company']
                cusdata_999['abbrname'] = data['ccusabbname']
                cusdata_999['ccusexch_name'] = data['currency']
                cusdata_999['a_company'] = '999'
                cusdata_999['sort_code'] = cusdata.get('sort_code')
                cusdata_999['payment'] = cusdata.get('payment')
                cusdata_999['ccusmngtypecode'] = cusdata.get('ccusmngtypecode')
                cusdata_999['account_remark'] = cusdata.get('account_remark')
                cusdata_999['ccdefine2'] = cusdata.get('ccdefine2')
                cusdata_999['ccusexch_name'] = cusdata.get('ccusexch_name')
                cusdata_999['seed_date'] = cusdata.get('seed_date')
                for company in ('999', cusdata['a_company']):
                    tar_data = cusdata_999 if company == '999' else cusdata
                    cus = env['xlcrm.u8_customer'].sudo().search(
                        [('review_id', '=', review_id), ('a_company', '=', company)])
                    if cus:
                        if cus.status == 0:
                            self.update('xlcrm.u8_customer', cus.id, tar_data, env)
                    else:
                        self.create('xlcrm.u8_customer', tar_data, env)
                    # env.cr.commit()
            env[model].sudo().browse(review_id).write({"account_attend_user_ids": data['account_attend_user_ids']})
            result_object = env[model].sudo().search_read([('id', '=', review_id)])
            # 更新documents
            self.change_documents(review_id, data.get('filedata', []), env)
            for r in result_object:
                r["station_desc"] = '%s(%s)' % (self.get_stations_desc(r['station_no']), self._get_user_nickname(
                    [('id', '=', r['signer'].split(',')[1])], 'nickname', env))
                signer = str(env.uid)
                if r['status_id'] == 2 and r['signer'] and signer in r['signer']:
                    r['status_id'] = 0
            if result_object:
                result_object = result_object[0]
                result_object['type'] = types
                if result_object['signer'] and record_status > 0:
                    self.send_email(result_object['signer'].split(',')[1], review_id, env)
                    self.send_wechat(result_object['signer'].split(',')[1], review_id, env)

            env.cr.commit()
            success = True
            message = "success"
        except Exception as e:
            result_object, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'dataProject': result_object, 'message': message,
              'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/getCommitListByAccountId'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_commit_list_by_account_id(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = self.authenticate(token)
        env = env
        result = []
        rejects_result = []
        if not env:
            return self.no_token()
        if kw.get("review_id"):
            review_id = int(kw.get("review_id"))
            try:
                current_sta = env['xlcrm.account'].sudo().search([("id", '=', review_id)])
                result += self.get_flow_list(current_sta, env)
                rejects = env['xlcrm.account.reject'].sudo().search_read([('review_id', '=', review_id)])
                rejects_result += self.get_flow_reject(rejects, env)
                partials = env['xlcrm.account.partial'].sudo().search_read([('review_id', '=', review_id)])
                rejects_result += self.get_flow_partial(partials, env)
                success = True
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()
        result.sort(key=lambda x: x["station_no"])
        rp = {'status': 200, 'success': success, 'message': message, 'data': result, 'rejects_data': rejects_result,
              'total': count}
        return self.json_response(rp)

    @http.route([
        '/api/v12/objUpdate/accountReview/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def obj_update_account12(self, model=None, ids=None, **kw):
        success, message, result, ret_object, count, offset, limit = True, '', '', '', 0, 0, 80
        token = kw.pop('token')
        env = self.authenticate(token)
        env = env
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            data = self.literal_eval(
                list(kw.keys())[0].replace('null', '""')).get("data")
            data.pop('backreason')
            if '0' in data.keys():
                review_id = data['0'].get('review_id')
                for da in data.values():
                    self.next_form(model, da, env)
            else:
                review_id = data.get('id') if data.get('si_station') == 1 else data.get('review_id')
                self.next_form(model, data, env)
            result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            if result:
                result = result[0]
                result['type'] = 'set'
                if result['station_no'] == 99 and odoo.tools.config["enviroment"] == 'PRODUCT':
                    self.insert_brandnamed_toU8(result)
                    # self.insert_brandlimit_toU8(review_id, env)
                si_ = str(env.uid)
                if result['signer'] and si_ in result['signer'].split(','):
                    result['status_id'] = 0

        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'success': success, 'message': message, 'dataProject': result}
        return self.json_response(rp)

    @http.route([
        '/api/v12/getAccountList/<string:model>',
        '/api/v12/getAccountList/<string:model>/<string:ids>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_list12(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        fields = eval(kw.get('fields', "[]"))
        order, query_filter = '', ''
        if kw.get("data"):
            json_data = kw.get("data").replace('null', 'None')
            query_filter = self.literal_eval(json_data)
            offset = query_filter.pop("page_no") - 1
            limit = query_filter.pop("page_size")
        try:
            domain = self.get_query_list_domain(query_filter, env)
            order = self.get_query_list_order(query_filter)
            count = env[model].sudo().search_count(domain)
            result = env[model].sudo().search_read(domain, fields, offset * limit, limit, order)
            if query_filter.get("export"):
                result = self.export_query_list(result, env)
            else:
                for r in result:
                    signer = str(env.uid)
                    if r['status_id'] == 2 and r['signer'] and signer in r['signer'].split(','):
                        r['status_id'] = 0
                    if r['station_no'] in range(20, 35):
                        pass
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
        '/api/v11/getAccountDetailByCustomer/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_detail_by_customer(self, model=None, ids=None, **kw):
        success, message, result, ret_temp, count, offset, limit = True, '', '', {}, 0, 0, 25
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        domain, domain_c = [], []
        if kw.get("customer"):
            customer = self.literal_eval(kw.get("customer"))
            domain_base = [('status_id', '>', 1)]
            domain = [('kc_company', '=', customer.get("kc_company")), ('a_company', '=', customer.get("a_company")),
                      ]
            domain_c = [('kc_company', '=', customer.get("kc_company"))]
            try:
                result = env[model].sudo().search_read(domain + domain_base, order='init_time desc', limit=1)
                if not result:
                    result = env[model].sudo().search_read(domain_c + domain_base, order='init_time desc',
                                                           limit=1)
                if result:
                    obj_temp = result[0]
                    model_fields = env[model].fields_get()
                    for f in obj_temp.keys():
                        if model_fields[f]['type'] == 'many2one':
                            if obj_temp[f]:
                                obj_temp[f] = {'id': obj_temp[f][0], 'display_name': obj_temp[f][1]}
                            else:
                                obj_temp[f] = ''
                    from ..public import account_public
                    current_account_period = []
                    if obj_temp['current_account_period']:
                        current_account_period = self.literal_eval(obj_temp['current_account_period'])
                    if not current_account_period:
                        temp = {}
                        temp['kc_company'] = obj_temp['kc_company']
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
                    obj_temp['cs'] = self.get_cs_new(obj_temp["id"], env)
                    ret_temp = {
                        "id": obj_temp["id"],
                        "review_type": obj_temp["review_type"],
                        "apply_user": obj_temp["apply_user"],
                        "department": obj_temp["department"],
                        "apply_date": obj_temp["apply_date"],
                        "a_company": obj_temp["a_company"],
                        "kc_company": obj_temp["kc_company"],
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
                        "station_no": obj_temp["station_no"],
                        "reconciliation_date": obj_temp["reconciliation_date"],
                        "payment_date": obj_temp["payment_date"],
                        "account_attend_user_ids": obj_temp["account_attend_user_ids"],
                        'reviewers': self.literal_eval(obj_temp['reviewers']) if obj_temp['reviewers'] else {},
                        'products': self.literal_eval(obj_temp['products']) if obj_temp['products'] else [],
                        'remark': obj_temp['remark'] if obj_temp['remark'] else '',
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
                        'credit_limit': obj_temp['credit_limit'] if obj_temp[
                            'credit_limit'] else '',
                        'credit_limit_now': obj_temp['credit_limit_now'] if obj_temp[
                            'credit_limit_now'] else '',
                        'current_account_period': current_account_period,
                        'cs': obj_temp['cs'],
                        'affiliates': eval(obj_temp['affiliates']) if obj_temp['affiliates'] else [],
                        'protocol_code': obj_temp['protocol_code']
                    }
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': ret_temp}
        return self.json_response(rp)

    @http.route([
        '/api/v12/getAccountDetailById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_detail_by_id12(self, model=None, ids=None, **kw):
        success, message, result, ret_temp, count, offset, limit = True, '', '', {}, 0, 0, 25
        token = kw.pop('token')
        env = env = self.authenticate(token)
        if not env:
            return self.no_token()
        domain = []
        if kw.get("id"):
            review_id = int(kw.get("id"))
            domain.append(('id', '=', review_id))
            try:
                result, ret = env[model].sudo().search_read(domain), {}
                if result:
                    obj_temp = result[0]
                    # if obj_temp['cs']:
                    #     obj_temp['cs'] = eval(obj_temp['cs'])
                    #     obj_temp['cs']['remark'] = obj_temp['cs']['remark'] if obj_temp['cs'].get('remark') else ''
                    #     obj_temp['cs']['trade_terms'] = obj_temp['cs']['trade_terms'] if obj_temp['cs'].get(
                    #         'trade_terms') else ''
                    # else:
                    #     obj_temp['cs'] = self.get_cs(review_id, env)
                    # if not obj_temp['cs'].get('historys'):
                    #     obj_temp['cs']['historys'] = [{'payment_account': obj_temp['cs'].get('payment_account'),
                    #                                    'payment_currency': obj_temp['cs'].get('payment_currency'),
                    #                                    'salesment_account': obj_temp['cs'].get('salesment_account'),
                    #                                    'salesment_currency': obj_temp['cs'].get('salesment_currency'),
                    #                                    }]
                    obj_temp['cs'] = self.get_cs_new(review_id, env)
                    si_station = self.get_si_station(obj_temp['station_no'], review_id, env)
                    products = self.literal_eval(obj_temp['products']) if obj_temp['products'] else []
                    products_sign = self.get_products_sign(products, si_station, obj_temp['init_user'][0], env)
                    ret['si_station'] = si_station
                    ret['products'] = products
                    ret['products_sign'] = products_sign
                    # 判断是否有回签
                    from_station_ = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', int(kw.get("id")))], order='init_time desc', limit=1)
                    ret['from_station'] = from_station_[0]['from_station'] if from_station_ and from_station_[0][
                        'sign_over'] == 'N' else ''
                    current_account_period = []
                    if obj_temp['current_account_period']:
                        current_account_period = self.literal_eval(obj_temp['current_account_period'])
                    if not current_account_period:
                        current_account_period = self.get_current_account_period(obj_temp)
                    ret['current_account_period'] = current_account_period
                    company_res = env['xlcrm.user.ccfnotice'].sudo().search_read(
                        [('a_company', '=', obj_temp['a_company'])])
                    ret['companycode'] = company_res[0]['a_companycode'] if company_res else ''
                    cusdata = env['xlcrm.u8_customer'].sudo().search_read(
                        [('review_id', '=', review_id), ('a_company', '!=', '999')],
                        fields=['sort_code', 'payment',
                                'ccusmngtypecode', 'account_remark',
                                'ccdefine2', 'seed_date'])
                    ret['cusdata'] = cusdata[0] if cusdata else {}
                    ret_temp = self.get_detail_by_id(obj_temp, env, **ret)
                message = "success"
            except Exception as e:
                result, success, message = '', False, str(e)
            finally:
                env.cr.close()

        rp = {'status': 200, 'message': message, 'data': ret_temp}
        return self.json_response(rp)

    @http.route([
        '/api/v11/sendSignOverEmail',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def sendSignOverEmail(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        env = self.authenticate(token)
        review_id = int(kw.pop('review_id'))
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            res = env['xlcrm.account'].sudo().search_read([('id', '=', review_id), ('init_user', '=', env.uid)])
            if res:
                res = res[0]
                a_company = res['a_company']
                kc_company = res['kc_company']
                release_time_apply = res['release_time_apply'] if res['release_time_apply'] else ''
                release_time_applyM = res['release_time_applyM'] if res['release_time_applyM'] else ''
                release_time_applyO = res['release_time_applyO'] if res['release_time_applyO'] else ''
                release_time_apply += release_time_applyM + release_time_applyO + '天' if release_time_apply in (
                    '月结', '其他') else ''
                credit_limit = "%s%s%s" % (res['credit_limit'] if res['credit_limit'] else '',
                                           res['unit'] if res['unit'] else '',
                                           res['currency'] if res['currency'] else '')
                payment_method_apply = res['payment_method_apply'].replace('per;', '%') if res[
                    'payment_method_apply'] else ''
                acceptance_days_apply = res['acceptance_days_apply'] if res['acceptance_days_apply'] else ''
                telegraphic_days_apply = res['telegraphic_days_apply'] if res['telegraphic_days_apply'] else ''
                payment_method_apply += acceptance_days_apply + telegraphic_days_apply + '天' if payment_method_apply in (
                    '承兑', '电汇加承兑') else ''
                kehu = res['kehu']
                from ..public import connect_mssql
                if kehu == '老客户' and res['current_account_period']:
                    kehu_ = eval(res['current_account_period'])
                    isumusd, str_, tup = 0, '', []
                    for index, item in enumerate(kehu_):
                        sum_sql = "select iSumOris,iSumUSD from v_GetSalesDetail_Group where companycodename='%s' and cCusName='%s'" % (
                            item["kc_company"], kc_company)
                        mssql_res = connect_mssql.Mssql('ErpCrmDB').query(sum_sql)
                        isumori, sd = mssql_res[0] if mssql_res else ('', 0)
                        isumusd += sd
                        if item["release_time"] == '款到发货':
                            str_ += """ <tr><td>交易主体:%s;放账时间:%s;交易情况:%s;上年度销售额(原币):%s;</td></tr> """ % \
                                    (item["kc_company"], item["release_time"], item["transaction_status"],
                                     str(isumori) if str(isumori) else '0')
                        else:
                            str_ += """ <tr><td>交易主体:%s;放账时间:%s;付款方式:%s;信用额度:%s%s;交易情况:%s;上年度销售额(原币):%s;</td></tr> """ % \
                                    (item["kc_company"], item["release_time"], item["payment_method"],
                                     item["credit_limit_now"], item["credit_limit_now_currency"],
                                     item["transaction_status"], str(isumori) if str(isumori) else '0')

                    kehu = """
                                <div style="margin-left:50px">
                                <table style="white-space: pre-wrap;">
                                <tr>
                                <td>上年度销售额合计(美金)：%s万美元</td>
                                </tr>
                            """ % str(isumusd)
                    kehu = kehu + str_ + """</table></div>"""
                # res_cus = env['xlcrm.account.customer'].sudo().search_read([('review_id', '=', review_id)])
                # res_cus = res_cus[0] if res_cus else {}
                # res_cus = eval(res['cs']) if res['cs'] else res_cus[0] if res_cus else {}
                # if not res_cus.get('historys'):
                #     res_cus['historys'] = [{'salesment_account': res_cus['salesment_account'],
                #                             'salesment_currency': res_cus['salesment_account'],
                #                             'payment_account': res_cus['salesment_account'],
                #                             'payment_currency': res_cus['salesment_currency']}]
                res_cus = self.get_cs_new(review_id, env)
                registered_capital = res_cus['registered_capital'] if res_cus.get('registered_capital') else ''
                registered_capital_currency = res_cus['registered_capital_currency'] if res_cus.get(
                    'registered_capital_currency') else ''
                registered_capital += registered_capital_currency
                paid_capital = res_cus['paid_capital'] if res_cus.get('paid_capital') else ''
                paid_capital_currency = res_cus['paid_capital_currency'] if res_cus.get('paid_capital_currency') else ''
                paid_capital += paid_capital_currency
                on_time = '%s%s%s' % (res_cus['on_time'] if res_cus.get('on_time') else '',
                                      '，%s%s%s' % ('上年至今超30天次数', res_cus['overdue30'], '次') if res_cus.get(
                                          'overdue30') else '',
                                      '，%s%s%s' % ('上年至今超60天次数', res_cus['overdue60'], '次') if res_cus.get(
                                          'overdue60') else '')
                payment_ = map(lambda x: '%s（%s%s）' % (
                    x.get('a_company') if x.get('a_company') else a_company, x.get('salesment_account') if x.get(
                        'salesment_account') else '', x.get('salesment_currency') if x.get(
                        'salesment_currency') else ''), res_cus.get('historys'))

                payment = '%s' % res_cus['payment'] if res_cus.get('payment') == '新客户' else ';'.join(payment_)
                res_pm = env['xlcrm.account.pm'].sudo().search_read([('review_id', '=', review_id)])
                pm = []
                if res_pm:
                    pm = map(lambda x: '%s(毛利率：%s%s，原厂账期：%s)' % (x['brandname'], x['profit'], "%", x['account_period']),
                             res_pm)
                res_sales = env['xlcrm.account.sales'].sudo().search_read([('review_id', '=', review_id)])[0]
                customer_type = res_sales['customer_type'] if res_sales['customer_type'] else ''
                key_customers = res_sales['key_customers'] if res_sales['key_customers'] else ''
                main_products = res_sales['main_products'] if res_sales['main_products'] else ''
                annual_turnover = '%s%s' % (res_sales['annual_turnover'] if res_sales['annual_turnover'] else '',
                                            res_sales['turnover_currency'] if res_sales[
                                                'turnover_currency'] else '')

                employees = res_sales['employees'] if res_sales['employees'] else ''
                sa = []
                if res_sales['products']:
                    sa = map(lambda x: '%s%s(品牌：%s)' % (
                        x.get('turnover'), x.get('currency') if x.get('currency') else '', x.get('brandname')),
                             eval(res_sales['products']))
                mkt = env['xlcrm.account.pmm'].sudo().search_read([('review_id', '=', review_id)])
                mkt_agree = map(lambda x: '%s(品牌：%s)/%s' % (x['content'], x['brandname'], x['update_nickname']),
                                mkt) if mkt else ''
                # MKT VP意见：%s
                coo_res = env['xlcrm.account.manage'].sudo().search_read([('review_id', '=', review_id)])
                coo_agree = 'COO意见：%s' % coo_res[0]['content'] if coo_res else ''
                from ..public import send_email
                email_obj = send_email.Send_email()
                sbuject = "申请-%s-%s-%s账期表(%s,%s,信用额度%s)" % (
                    a_company, kc_company, '新增' if res['kehu'] == '新客户' else '更新', release_time_apply,
                    payment_method_apply,
                    credit_limit)
                to = [env['xlcrm.users'].sudo().search_read([('id', '=', res['init_user'][0])])[0]['email']]
                cc = ['yangyouhui@szsunray.com', 'dengliming@szsunray.com']
                # to = ['yangwenbo@szsunray.com']
                # cc = []
                signer = env['xlcrm.users'].sudo().search_read([('id', 'in', res['account_attend_user_ids'])])
                signer = ';'.join(map(lambda x: x['email'], signer)) + ';babytse@szsunray.com'  # 添加风控主管谢蓓
                content = """<html>
                        <style>
                             table, td{ 
                          #border:1px solid black; 
                          border-collapse:collapse; 
                        }
                        </style>
                        <body>
                        <p>
                            审核人邮箱：%s
                        </p>
                        夏总，您好：
                        <p style="text-indent:2em">
                            %s<b>%s</b>申请账期表，相关信息如下，恳请审批！
                        </p>                    
                        <p>
                            <h4>1)申请项目：</h4>
                        </p>
                        <p style="text-indent:2em">
                            <b>现有账期：</b>%s 
                        </p>
                        <p style="text-indent:2em">
                            <b>申请账期：</b>%s ;信用额度：%s ;付款方式：%s
                        </p>
                        <p>
                            <h4>2)重点情况：</h4>
                        </p>
                        <p style="text-indent:2em">
                            ①注册资本：%s，实缴资本：%s，参保人数：%s人。
                        </p>
                        <p style="text-indent:2em">
                            ②产线及毛利及原厂账期：%s
                        </p>
                        <p style="text-indent:2em">
                            ③历史付款情况：%s;之前一年的销售金额：%s
                        </p>
                        <p style="text-indent:2em">
                            ④客户类型：%s
                        </p>
                        <p style="text-indent:2em">
                            ⑤客户基本情况：主要客户为%s，客户年营业额为%s，预计我司销售额为%s，员工人数%s人
                        </p>
                        <p>
                            <h4>3)其他说明：</h4>
                        </p>
                        <p style="text-indent:2em">
                            MKT VP意见：%s
                        </p>
                        <p style="text-indent:2em">
                            %s
                        </p>
                        </body>
    </ht            </html>
                    """ % (signer, a_company, kc_company, kehu, release_time_apply, credit_limit, payment_method_apply,
                           registered_capital, paid_capital, employees, '、'.join(pm), on_time, payment, customer_type,
                           key_customers, annual_turnover, '、'.join(sa), employees, '、'.join(mkt_agree), coo_agree)
                msg = email_obj.send(subject=sbuject, to=to, cc=cc, content=content, env=env)
                if msg["code"] == 500:  # 邮件发送失败
                    success = False
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message,
              'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v12/partialRejection',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_partial12(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            review_id = data.pop('review_id')
            from_station = data.pop('from_station')
            record_status = data.pop('record_status')
            par = env['xlcrm.account.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)
            p_id = par[0]['id'] if par else ''
            if par:
                data['from_id'] = par[0]['id']
                if par[0]['from_station'] == from_station and par[0]['sign_over'] == 'N':
                    env['xlcrm.account.partial'].sudo().browse(par[0]['id']).write(data)
                else:
                    p_id = env['xlcrm.account.partial'].sudo().create(data).id
            else:
                p_id = env['xlcrm.account.partial'].sudo().create(data).id
            to_station, remark, to_brand = '', '', {}
            if data:
                data.pop('from_id', None)
                for key, value in data.items():
                    station = self.get_staions_reject(key)
                    to_brand_tmp = ''
                    if key in ('pm', 'pmins', 'pur', 'pmm'):
                        b_remark = ''
                        b_data = {'init_user': env.uid}
                        for kp, vp in value.items():
                            to_brand_tmp += kp + ','
                            b_remark += vp['back_remark'] + '\p'
                        b_data['review_id'] = review_id
                        b_data['station_no'] = station
                        b_data['to_brand'] = to_brand_tmp
                        b_data['remark'] = b_remark
                        b_data['p_id'] = p_id
                        env['xlcrm.account.partial.sec'].sudo().create(b_data)
                    else:
                        remark += value['back_remark'] + '\p'
                    to_station += str(station) + ','
                    to_brand[station] = to_brand_tmp
            data['review_id'] = review_id
            data['from_station'] = from_station
            data['to_station'] = to_station
            data['remark'] = remark
            data["init_user"] = env.uid
            self.update('xlcrm.account.partial', p_id, data, env)
            signer, station_desc = self.get_partial_signer(to_station, to_brand, review_id, env)
            data_up = {'station_no': 28, 'update_time': datetime.datetime.now() + datetime.timedelta(hours=8),
                       'update_user': env.uid, 'signer': signer, 'station_desc': station_desc + '-回签'}
            self.update('xlcrm.account', review_id, data_up, env)
            env.cr.commit()
            result = env['xlcrm.account'].sudo().search_read([('id', '=', review_id)])
            if result:
                result = result[0]
            if result['signer']:
                result['type'] = 'set'
                si_ = ',' + str(env.uid) + ','
                if si_ in result['signer']:
                    result['status_id'] = 0
                for uid in result['signer'].split(','):
                    if uid:
                        self.send_email(uid, review_id, env)
            message = "success"
            success = True
        except Exception as e:
            result, message, success = '', str(e), False
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'success': success, 'dataProject': result}
        return self.json_response(rp)

    @http.route([
        '/api/v11/updateFlowerItem/<string:model>',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def update_flower(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0].replace('true', '""')).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            from collections import Iterator
            review_id = data.pop('review_id')
            signers = list(filter(lambda x: x['signer'], data.values()))
            res = env[model].sudo().search_read([('id', '=', review_id)])[0]
            reviewers = eval(res['reviewers'])
            products = eval(res['products'])
            for signer in signers:
                station_no = signer['station_no']
                station_code = self.get_station_code(station_no)
                sign = list(filter(lambda x: x['signer'], signer['signer'])) if isinstance(signer['signer'],
                                                                                           Iterator) else \
                    signer['signer']
                sign_ids = sign
                if station_no in (20, 25, 30):
                    for brand in sign:
                        brandname = brand['sign_brand_name']
                        for product in products:
                            if product['sign_brand_name'] == brandname:
                                product[station_code] = brand['signer']
                                if station_no == 20:
                                    res_ = env['xlcrm.user.ccfpminspector'].sudo().search_read(
                                        [('pm', 'ilike', brand['signer'])])
                                    if res_:
                                        product['PMins'] = res_[0]['inspector']
                                    else:
                                        product['PMins'] = ''

                    sign = list(map(lambda x: x[station_code], products))
                    sign_ids = ','.join(
                        list(map(lambda x: str(x), self.get_user_id({station_code: sign}, env)[station_code])))
                    if station_no == 20:
                        sign_ = list(map(lambda x: x.get('PMins'), products))
                        brandname_ = ','.join(list(map(lambda x: x['sign_brand_name'], products)))
                        sign_ids_ = ','.join(
                            list(map(lambda x: str(x), self.get_user_id({'PMins': sign_}, env)['PMins'])))
                        res_s_ = env['xlcrm.account.signers'].sudo().search(
                            [('review_id', '=', review_id), ('station_no', '=', 21)])
                        if res_s_:
                            if sign_ids_:
                                res_s_.write({'signers': sign_ids_})
                            else:
                                res_s_.unlink()
                        else:
                            env['xlcrm.account.signers'].sudo().create({'review_id': review_id,
                                                                        'station_no': 21, 'station_desc': 'PM总监签核',
                                                                        'signers': sign_ids_,
                                                                        'brandname': brandname_})
                        reviewers['PMins'] = sign_
                res_s = env['xlcrm.account.signers'].sudo().search(
                    [('review_id', '=', review_id), ('station_no', '=', station_no)])
                res_s.write({'signers': sign_ids})
                reviewers[station_code] = sign
            attend_res = env['xlcrm.account.signers'].sudo().search_read([('review_id', '=', review_id)])
            attend_res = list(filter(lambda x: x['signers'], attend_res))
            attend_ids = ','.join(list(map(lambda x: x['signers'], attend_res))).replace('[', '').replace(']', '')
            attend_ids = list(map(lambda x: int(x), attend_ids.split(',')))
            env[model].sudo().browse(review_id).write(
                {'reviewers': reviewers, 'products': products, 'account_attend_user_ids': [[6, 0, attend_ids]]})
            env.cr.commit()
            message = '变更成功'
        except Exception as e:
            success, message, reviewers, products, account_attend_user_ids = False, str(e), [], [], []
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message,
              'success': success, 'reviewers': reviewers, 'products': products, 'account_attend_user_ids': attend_ids}
        return self.json_response(rp)

    @http.route([
        '/api/v11/update_signer',
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def update_signer(self, model=None, success=True, message='', **kw):
        success, message = True, ''
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            self.update_current_signer(env)
            message = '变更成功'
        except Exception as e:
            success, message = False, str(e)
        finally:
            env.cr.commit()

        rp = {'status': 200, 'message': message,
              'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/reCallByAccountId',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def recall_account(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import account_public
            review_id = self.literal_eval(kw.get("review_id"))
            data = {}
            model = 'xlcrm.account'
            data['station_no'] = 1
            data['signer'] = ',%d,' % env.uid
            data["update_user"] = env.uid
            data["update_time"] = datetime.datetime.now() + datetime.timedelta(hours=8)
            data['status_id'] = 1
            data['isback'] = 2
            data['station_desc'] = '申请者填单'
            env[model].sudo().browse(review_id).write(data)
            # 判断是否回签
            sign_back = env['xlcrm.account.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)
            if sign_back and sign_back[0]['sign_over'] == 'N':
                env['xlcrm.account.partial'].sudo().browse(sign_back[0]['id']).write(
                    {'sign_station': sign_back[0]['to_station']})
            result_object = env[model].sudo().search_read([('id', '=', review_id)])
            if result_object:
                result_object = result_object[0]
                result_object['login_user'] = env.uid
                result_object['type'] = 'set'
                if result_object['signer']:
                    self.send_email(result_object['signer'].split(',')[1], review_id, env)
                    self.send_wechat(result_object['signer'].split(',')[1], review_id, env)
            env.cr.commit()
            success = True
            message = "success"
        except Exception as e:
            result_object, result_object, success, message = '', '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'message': message, 'data': result_object, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v12/getAccountReviewById/<string:model>'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_account_review_by_id12(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 25
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        domain, filters, result, look_profit = [], [], {}, True
        try:
            review_id = int(kw.get("id"))
            domain.append(('id', '=', review_id))
            main_form = env["xlcrm.account"].sudo().search_read(domain)
            station_no = main_form[0]['station_no']
            from_station_ = env['xlcrm.account.partial'].sudo().search_read(
                [('review_id', '=', review_id)], order='init_time desc', limit=1)
            station_no = from_station_[0]['from_station'] if from_station_ and from_station_[0][
                'sign_over'] == 'N' else station_no
            # signer_id = ','.join(main_form[0]['signer'].split(',')[1:-1]) if main_form[0]['signer'] else ''
            dict_model = self.get_model_by_station(station_no)
            base_model = 'xlcrm.account'
            for key, value in dict_model.items():
                tar_model = base_model + '.' + value
                tar_domain = [('review_id', '=', review_id), ('station_no', '=', key)]
                res_tmp = env[tar_model].sudo().search_read(tar_domain, filters, order='update_time desc')
                if key == 36:
                    value = 'fdm'
                    if not res_tmp:
                        tar_domain = [('review_id', '=', review_id), ('station_no', '=', 35)]
                        res_tmp = env[tar_model].sudo().search_read(tar_domain, filters, order='update_time desc')
                        res_tmp = [res_tmp[0]] if res_tmp else []
                if key == 35:
                    res_tmp = [res_tmp[0]] if res_tmp else []
                if key == 20:
                    self._get_pm_profit(res_tmp, env)
                result[value] = res_tmp
                if result[value]:
                    signer = [env['xlcrm.users'].sudo().search_read([('id', '=', item['update_user'][0])],
                                                                    ['nickname'])[0][
                                  'nickname'] + ' ' + datetime.datetime.strftime(item['update_time'],
                                                                                 '%Y-%m-%d %H:%M:%S') for item in
                              result[value]]
                    # signer='-'.join(signer)
                    # 判断是否回签，回签后是否已签
                    signer_id = [item['update_user'][0] for item in result[value]]
                    re_back_ = env['xlcrm.account.partial'].sudo().search_read(
                        [('review_id', '=', review_id)], order='init_time desc', limit=1)
                    re_back = re_back_ if re_back_ and re_back_[0]['sign_over'] == 'N' else ''
                    if re_back:
                        sign_station = re_back[0]["sign_station"] if re_back[0]['sign_station'] else ''
                        if str(self.get_stations_reject(value)) + ',' in sign_station:
                            signer_id = []
                    if value in ('pm', 'pmins', 'pur', 'pmm'):
                        for rs in result[value]:
                            rs['signer'] = [
                                env['xlcrm.users'].sudo().search_read([('id', '=', rs['update_user'][0])],
                                                                      ['nickname'])[0][
                                    'nickname'] + ' ' + datetime.datetime.strftime(rs['update_time'],
                                                                                   '%Y-%m-%d %H:%M:%S')]
                            rs['signer_id'] = [rs['update_user'][0]]
                            rs['init_nickname'] = \
                                env['xlcrm.users'].sudo().search_read([('id', '=', rs['update_user'][0])],
                                                                      ['nickname'])[0]['nickname']
                        continue
                    result[value] = result[value][0]
                    result[value]['init_nickname'] = \
                        env['xlcrm.users'].sudo().search_read([('id', '=', result[value]['update_user'][0])],
                                                              ['nickname'])[0]['nickname']
                    result[value]['signer'] = signer
                    result[value]['signer_id'] = signer_id
                    if value == "sales":
                        result['sales']['products'] = self.literal_eval(result['sales']['products']) if \
                            result['sales']['products'] else []
                    if value == 'risk':
                        result[value]['signer'] = signer[::-1]
                        result[value]['signer_id'] = signer_id[::-1]
                        result[value]['products_overdue'] = self.literal_eval(result[value]['products_overdue']) if \
                            result[value]['products_overdue'] else []
                        result[value]['products_contract'] = self.literal_eval(result[value]['products_contract']) if \
                            result[value]['products_contract'] else []
                else:
                    signer_tmp = {'id': '', 'signer_id': [], 'signer': []}
                    result[value] = signer_tmp
                    # result[value] = [signer_tmp] if key in range(20, 31) else signer_tmp
            if 'sales' in result and result['sales'] and env.uid in result['sales']['signer_id']:
                look_profit = False
            if 'salesm' in result and result['salesm'] and env.uid in result['salesm']['signer_id']:
                look_profit = False
            if 'salesvp' in result and result['salesvp'] and env.uid in result['salesvp']['signer_id']:
                look_profit = False
            if 'pm' in result and isinstance(result['pm'], list):
                self.update_pm_profit(result['pm'], look_profit, env)
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result}
        return self.json_response(rp)

    @http.route(['/api/v11/getBrandListFromU8'], auth='none', type='http', csrf=False, methods=['GET'])
    def get_u8_brands(self, model=None, ids=None, **kw):
        success, message, data = True, '', []
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            mssql = connect_mssql.Mssql('stock')
            res = mssql.query('select distinct [品牌] from [v_Inventory_sunray]')
            for _res in res:
                data.append(_res[0])
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.json_response(
                {'status': 200, 'success': success, 'message': message, 'data': data})

    @http.route(['/api/v11/getPaymentFromU8'], auth='none', type='http', csrf=False, methods=['GET'])
    def get_u8_payment(self, model=None, ids=None, **kw):
        success, message, data = True, '', []
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            res = mssql.query('select cValue from UserDefine where cID=70')
            for _res in res:
                data.append(_res[0])
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.json_response(
                {'status': 200, 'success': success, 'message': message, 'data': data})

    @http.route(['/api/v11/getAccountRemarkListFromU8'], auth='none', type='http', csrf=False, methods=['GET'])
    def get_u8_account_remark(self, model=None, ids=None, **kw):
        success, message, data = True, '', []
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            res = mssql.query('select cValue from UserDefine where cID=65')
            for _res in res:
                data.append(_res[0])
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.json_response(
                {'status': 200, 'success': success, 'message': message, 'data': data})

    @http.route(['/api/v11/getMaterialListFromU8'], auth='none', type='http', csrf=False, methods=['GET'])
    def get_u8_materials(self, model=None, ids=None, **kw):
        success, message, data = True, '', []
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            brand_name = kw.get('brand_name')
            from ..public import connect_mssql
            mssql = connect_mssql.Mssql('stock')
            sql = "select [品牌],[存货编号] from [v_Inventory_sunray] where 品牌='%s'" % brand_name
            res = mssql.query(sql)
            for _res in res:
                _tmp = dict()
                _tmp['brand_name'] = _res[0]
                _tmp['inventory_code'] = _res[1]
                data.append(_tmp)
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.json_response(
                {'status': 200, 'success': success, 'message': message, 'data': data})

    @http.route(['/api/v11/getCustomerClassFromU8'], auth='none', type='http', csrf=False, methods=['GET'])
    def get_u8_customerclass(self, model=None, ids=None, **kw):
        success, message, data = True, '', []
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        try:
            from ..public import connect_mssql
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            res = mssql.query('select cCCCode,cCCName from CustomerClass where iCCGrade=4')
            for _res in res:
                data.append({'value': _res[0], 'label': _res[1]})
        except Exception as e:
            success, message = False, str(e)
        finally:
            return self.json_response(
                {'status': 200, 'success': success, 'message': message, 'data': data})

    @http.route([
        '/api/v11/getSignerList'
    ], auth='none', type='http', csrf=False, methods=['GET'])
    def get_user_list(self, model=None, ids=None, **kw):
        success, message, result, count, offset, limit = True, '', '', 0, 0, 5000
        token = kw.pop('token')
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        domain = []
        fields = eval(kw.get('fields', "[]"))
        order = kw.get('order', 'id desc')
        if kw.get("data"):
            query_filter = self.literal_eval(kw.get("data"))
            offset = query_filter.pop("page_no") - 1
            limit = query_filter.pop("page_size")
            if query_filter and query_filter.get("code"):
                domain = [('code', '=', query_filter.get("code"))]
            if query_filter and query_filter.get("code_name"):
                domain = ['|', ('code', 'like', query_filter.get("code_name")),
                          ('name', 'like', query_filter.get("code_name"))]
            if query_filter and query_filter.get("order_field"):
                order = query_filter.get("order_field") + " " + query_filter.get("order_type")
        try:
            count = env["xlcrm.account.special.signers"].sudo().search_count(domain)
            result = env["xlcrm.account.special.signers"].sudo().search_read(domain, fields, offset * limit, limit,
                                                                             order)

            for res in result:
                res['fd'] = '是' if res['fd'] else '否'
                res['lg'] = '是' if res['lg'] else '否'
                res['riskm'] = '是' if res['riskm'] else '否'
            message = "success"
            success = True
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'message': message, 'success': success, 'data': result, 'total': count, 'page': offset + 1,
              'per_page': limit}
        return self.json_response(rp)

    @http.route([
        '/api/v11/createSigner',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def create_signer(self, model=None, success=False, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            data["init_user"] = env.uid
            data['fd'] = 1 if data['fd'] == '是' else 0
            data['lg'] = 1 if data['lg'] == '是' else 0
            data['riskm'] = 1 if data['riskm'] == '是' else 0
            create_id = env['xlcrm.account.special.signers'].sudo().create(data).id
            result_object = env['xlcrm.account.special.signers'].sudo().search_read([('id', '=', create_id)])[0]
            result_object['fd'] = '是' if result_object['fd'] else '否'
            result_object['lg'] = '是' if result_object['lg'] else '否'
            result_object['riskm'] = '是' if result_object['riskm'] else '否'
            env.cr.commit()
            message = "success"
            success = True
        except Exception as e:
            success, result_object, message = False, '', str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/updateSigner',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def update_signer(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        ret_object = []
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            obj_id = data["id"]
            data["update_user"] = env.uid
            data['fd'] = 1 if data['fd'] == '是' else 0
            data['lg'] = 1 if data['lg'] == '是' else 0
            data['riskm'] = 1 if data['riskm'] == '是' else 0
            result = env["xlcrm.account.special.signers"].sudo().browse(obj_id).write(data)
            ret_object = env["xlcrm.account.special.signers"].sudo().search_read([('id', '=', obj_id)])[0]
            ret_object['fd'] = '是' if ret_object['fd'] else '否'
            ret_object['lg'] = '是' if ret_object['lg'] else '否'
            ret_object['riskm'] = '是' if ret_object['riskm'] else '否'
            env.cr.commit()
            message = "success"
        except Exception as e:
            result, success, message = '', False, str(e)
        finally:
            env.cr.close()

        rp = {'status': 200, 'data': ret_object, 'message': message}
        return self.json_response(rp)

    @http.route([
        '/api/v11/importSignerItem',
    ], auth='none', type='http', csrf=False, methods=['POST'])
    def import_user_item(self, model=None, success=True, message='', **kw):
        token = kw.pop('token')
        data = self.literal_eval(list(kw.keys())[0]).get("data")
        env = self.authenticate(token)
        if not env:
            return self.no_token()
        if not self.check_sign(token, kw):
            return self.no_sign()
        try:
            data['code'] = data['code'].replace("'", "")
            data['name'] = data['name'].replace("'", "")
            data['date'] = data['date'].replace("'", "")
            data['fd'] = 1 if data['fd'] == '是' else 0
            data['lg'] = 1 if data['lg'] == '是' else 0
            data['riskm'] = 1 if data['riskm'] == '是' else 0
            res = env['xlcrm.account.special.signers'].sudo().search([('code', '=', data['code'])], limit=1)
            if res:
                env["xlcrm.account.special.signers"].sudo().browse(res['id']).write(data)
            else:
                env["xlcrm.account.special.signers"].sudo().create(data)
            env.cr.commit()
            success = True
            message = "导入完成！"
            result_object = ''
        except Exception as e:
            result_object, success, message = '', False, str(e)
        finally:
            env.cr.close()
        rp = {'status': 200, 'data': result_object, 'message': message, 'success': success}
        return self.json_response(rp)

    @http.route([
        '/api/v11/upload/addfileaccount'
    ], auth='none', type='http', csrf=False, methods=['POST', 'OPTIONS'])
    def upload_addfile_account(self, success=False, message='', ret_data='', file='', **kw):
        if file:
            token = kw.pop('token')
            env = self.authenticate(token)
            if not env:
                return self.no_token()
            try:
                res_id = kw.get('res_id')
                materials = kw.get('materials')
                description = materials if materials else ''
                from ..public import account_public
                success, url, name, size, message = account_public.saveFile(env.uid, file)
                if not success:
                    rp = {'status': 200, 'data': [], 'success': success, 'message': message}
                    return self.json_response(rp)
                file_data = {'name': name,
                             'datas_fname': file.filename,
                             'res_model': 'xlcrm.account',
                             # 'db_datas': base64.b64encode(file_content),
                             'mimetype': file.mimetype,
                             'create_user_id': env.uid,
                             'file_size': size,
                             'res_id': res_id,
                             'type': 'url',
                             'description': description,
                             'url': url}
                create_id = env['xlcrm.documents'].sudo().create(file_data).id
                env.cr.commit()
                if description:
                    self.insert_brandlimit_toU8(int(res_id), env)
                result_object = env['xlcrm.documents'].sudo().search_read([('id', '=', create_id)])[0]
                ret_data = {'document_id': result_object['id'],
                            'document_name': result_object['datas_fname'],
                            'document_file_url': odoo.tools.config['serve_url'] + '/crm/file/' + str(
                                result_object['id']),
                            'init_user': result_object['create_user_id'][0],
                            'init_usernickname': env['xlcrm.users'].sudo().search_read(
                                [('id', '=', result_object['create_user_id'][0])])[0]['nickname'],
                            'init_time': result_object['create_date_time'],
                            'description': f"料号：{result_object['description']}的合规许可证附件" if result_object[
                                'description'] else ''
                            }

                success = True
            except Exception as e:
                ret_data, success, message = '', False, str(e)
            finally:
                env.cr.close()
        rp = {'status': 200, 'data': ret_data, 'success': success, 'message': message}
        return self.json_response(rp)
