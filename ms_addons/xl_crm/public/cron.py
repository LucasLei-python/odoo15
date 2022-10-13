from . import send_email, connect_mssql
import odoo, json
from odoo import modules


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


class Aps:
    @staticmethod
    def send_email_brand_limit():
        try:
            to_email = [odoo.tools.config["test_username"]]
            con_str, remark_brand, remark_material = '158_999', [], []
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
                to_email = ['zhuxiaolian@szsunray.com']
            mssql = connect_mssql.Mssql(con_str)
            db_name = mssql.query("select code,dataname from EF_Table_Database where status=1")
            for db in db_name:
                res = mssql.query(f"select cBrand from {db[1]}.dbo.EF_BrandLimit where cAuditer is null or cAuditer=''")
                if res:
                    b_ = [f'交易主体：{db[0]}-品牌：{item[0]}' for item in res]
                    remark_brand.append(';'.join(b_))
                res_ = mssql.query(
                    f"select cInvCode from {db[1]}.dbo.EF_InvPermit where cAuditer is null or cAuditer=''")
                if res_:
                    m_ = [f'交易主体：{db[0]}-料号：{item[0]}' for item in res_]
                    remark_material.append(';'.join(m_))

            send = send_email.Send_email()
            send.send('U8品牌限制需要审核', to_email, content=f'请去U8品牌限制审核表进行审核。{";".join(remark_brand)}')
            send.send('U8有存货许可编辑未审核', to_email, content=f'请去CCF对应料号上传合规许可证或在U8的存货许可审核表进行审核。{";".join(remark_material)}')
        except Exception as e:
            raise repr(e)

    def send_email_account_list(self, env):
        try:
            import datetime
            from .ccf import CCF
            ccf = CCF()
            to_time = datetime.datetime.today().replace(hour=10, minute=0, second=0)
            day = datetime.datetime.weekday(datetime.datetime.today())
            from_time = to_time - datetime.timedelta(days=day + 1)
            # to_time = datetime.datetime.strptime('2022-06-26 10:00:00', '%Y-%m-%d %H:%M:%S')
            # from_time = datetime.datetime.strptime('2022-06-19 10:00:00', '%Y-%m-%d %H:%M:%S')
            to_email = [odoo.tools.config["test_username"]]
            cc_email = []
            bcc_email = []
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                to_email = ['zhongjuan@szsunray.com', 'liuchenyu@szsunray.com']
                cc_email = ['lidongming@szsunray.com']
                bcc_email = ['leihui@szsunray.com', 'dengliming@szsunray.com', 'songqinghua@szsunray.com']
            a_res = env['xlcrm.account'].sudo().search_read(
                [('update_time', '<=', to_time), ('update_time', '>=', from_time), ('status_id', '=', 3)])
            res = ccf.export_query_list(a_res, env)
            send = send_email.Send_email()
            file_name = f'{datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d%H%M%S")}.xls'
            file_path = modules.module.get_module_resource('xl_crm') + '/static/account/' + file_name
            self.export_excel(res, file_path)
            send.send_file_email(f'本周CCF结案资料表', to_email, cc_email,
                                 content=f'本周({datetime.datetime.strftime(from_time, "%Y-%m-%d %H:%M:%S")}至{datetime.datetime.strftime(to_time, "%Y-%m-%d %H:%M:%S")})CCF结案资料如附件，请查收！谢谢！',
                                 env=env,
                                 file_name=file_name, file_path=file_path, bcc=bcc_email)
        except Exception as e:
            raise repr(e)

    @staticmethod
    def len_byte(value):
        length = len(value)
        utf8_length = len(value.encode('utf-8'))
        length = (utf8_length - length) / 2 + length
        length = 256 * (length + 1)
        return int(length)

    def export_excel(self, data, file_path):
        try:
            import xlwt
            workbook = xlwt.Workbook(encoding='utf-8')  # 写入excel文件
            sheet = workbook.add_sheet('Sheet1', cell_overwrite_ok=True)  # 新增一个sheet工作表
            headlist = [
                ('序号', '客户名称', '客服', '销售', '销售部', '申请时间', '当前签核描述', '结案时间', '注册资本', '实缴资本', '上市公司/控股子公司（是/否）', '参保人数',
                 '保理额度', '收货确认人', '收货公司名称', '产品线', '毛利率', '现有账期', '申请账期', '其他'),
                (
                    '交易主体', '放账时间', '付款方式', '信用额度', '交易情况', '交易主体', '放账时间(申请)', '付款方式(申请)', '信用额度',
                    '信用额/实缴资金占比%')]  # 写入数据头
            row, col, start = 0, 0, 17
            style = xlwt.XFStyle()
            style.borders.left = 0x02
            style.borders.right = 0x02
            style.borders.bottom = 0x02
            style.borders.top = 0x02
            style.alignment.vert = 0x01
            for i, head in enumerate(headlist):
                for j, label in enumerate(head):
                    h, w = 0, 0
                    if i == 0:
                        if j in (17, 18):
                            w = 4
                        else:
                            h, w = 1, 0
                        if j < 18:
                            col = j
                        elif j > 17:
                            col += 5
                        sheet.write_merge(i, i + h, col, w + col, label, style)
                    if i == 1:
                        col = start + j
                        sheet.write(i, col, label, style)
                    sheet.col(col).width = self.len_byte(label)
                row += 1
            main_start = 2
            for i, _data in enumerate(data):
                _data['seq'] = i + 1
                _data['update_time'] = f"{_data['update_time']}"
                _data['apply_date'] = f"{_data['apply_date']}"
                _data[
                    'credit_limit'] = f"{_data['credit_limit']}{_data['unit'] if _data['unit'] else ''}{_data['currency']}"
                _data['percent'] = ''
                base_data = ['seq', 'kc_company', 'init_usernickname', 'apply_user', 'department', 'apply_date',
                             'signer_desc', 'update_time', 'registered_captial', 'paid_capital', 'listed_company',
                             'insured_persons', 'factoring',
                             'receipt_confirmer', 'krc_company', 'a_company', 'release_time_apply'
                    , 'payment_method_apply', 'credit_limit', 'percent', 'others']
                if _data['release_time_apply']:
                    tmp_days = ''
                    if _data['release_time_apply'] == '月结':
                        tmp_days = f"{_data['release_time_applyM']}天"
                    elif _data['release_time_apply'] == '其他':
                        tmp_days = f"{_data['release_time_applyO']}天"
                    _data['release_time_apply'] = f"{_data['release_time_apply']}{tmp_days}"
                else:
                    _data['release_time_apply'] = _data['release_time_apply_new']
                if _data['payment_method_apply']:
                    tmp_days = ''
                    if _data['payment_method_apply'] == '承兑':
                        tmp_days = f"{_data['payment_method_apply']}天"
                    elif _data['payment_method_apply'] == '电汇加承兑':
                        tmp_days = f"{_data['telegraphic_days_apply']}天"
                    _data['payment_method_apply'] = f"{_data['payment_method_apply']}{tmp_days}"
                else:
                    if _data['payment_method_apply_new'] == '电汇':
                        tmp_days = f"{_data['wire_apply_per']}%电汇{_data['wire_apply_type']}{_data['wire_apply_days']}天"
                    elif _data['payment_method_apply_new'] == '天数':
                        tmp_days = f"{_data['days_apply_type']}{_data['days_apply_days']}天"
                    elif _data['payment_method_apply_new'] == '其他':
                        tmp_days = f"{_data['payment_method_apply_new']}{_data['others_apply']}"
                    else:
                        tmp_days = f"{_data['payment_method_apply_new']}"
                    _data['payment_method_apply'] = tmp_days
                _data['release_time_apply'] = _data['release_time_apply'].replace('amp;', '&').replace(
                    'eq;', '=').replace('plus;', '+').replace('per;', '%')
                _data['payment_method_apply'] = _data['payment_method_apply'].replace('amp;', '&').replace(
                    'eq;', '=').replace('plus;', '+').replace('per;', '%')
                profit, period = _data['brand_profit'], _data['current_account_period']
                h = max(len(profit), len(period)) - 1
                base_index = [_i for _i in range(15)] + [_i for _i in range(22, 28)]
                for k, j in enumerate(base_index):
                    label = _data[base_data[k]]
                    sheet.write_merge(main_start, h + main_start, j, j, label, style)
                    # sheet.col(j).width = self.len_byte(str(label))
                for du in range(abs(len(profit) - len(period))):
                    if len(profit) > len(period):
                        period.append({
                            'credit_limit_now': "",
                            'credit_limit_now_currency': "",
                            'kc_company': "",
                            'payment_method': "",
                            'release_time': "",
                            'transaction_status': "",
                        })
                    else:
                        profit.append({
                            'material': "",
                            'profit': "",
                            'compliance': ''
                        })
                for index, item in enumerate(profit):
                    material = item.get('material').replace('amp;', '&').replace(
                        'eq;', '=').replace('plus;', '+').replace('per;', '%')
                    sheet.write(main_start, 15, material, style)
                    profit = f'{item.get("profit")}%' if item.get('profit', "") else ''
                    sheet.write(main_start, 16, profit, style)
                    sheet.write(main_start, 17, period[index].get('kc_company', ""), style)
                    sheet.write(main_start, 18, period[index].get('release_time', "").replace('amp;', '&').replace(
                        'eq;', '=').replace('plus;', '+').replace('per;', '%'), style)
                    sheet.write(main_start, 19, period[index].get('payment_method', "").replace('amp;', '&').replace(
                        'eq;', '=').replace('plus;', '+').replace('per;', '%'), style)
                    sheet.write(main_start, 20,
                                f'{period[index].get("credit_limit_now", "")}{period[index].get("credit_limit_now_currency", "")}',
                                style)
                    sheet.write(main_start, 21, period[index].get('transaction_status', ""), style)
                    main_start += 1

            # file_path = modules.module.get_module_resource('xl_crm') + '/static/test.xls'
            workbook.save(file_path)
            return file_path
        except Exception as e:
            print(e)

    def synchronization_cus(self, res, env, login):
        try:
            import requests
            import json
            from .u8_login_user import U8Login
            desc = {'ok': False, 'msg': ''}
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            if login.ok:
                headers['apiToken'] = json.loads(login.text)
                cusdeliveradd = env['xlcrm.u8_customer_deliver_add'].sudo().search_read(
                    [('review_id', '=', res.review_id.id)],
                    fields=['caddcode',
                            'cdeliveradd',
                            'cenglishadd2',
                            'cenglishadd3',
                            'cenglishadd4',
                            'clinkperson',
                            'cdeliverunit',
                            'bdefault'])
                auth_res = env['xlcrm.u8_customer_authdimen'].sudo().search_read([('review_id', '=', res.review_id.id)])
                auth_data = list()
                auth_data.append({
                    "account_id": res.code,
                    "privilege_type": "0",
                    "privilege_id": res.super_dept
                })
                if res.a_company != '999' and auth_res:
                    for auth in auth_res:
                        tmp = dict()
                        tmp["account_id"] = res.code
                        tmp["privilege_type"] = "5"
                        tmp["privilege_id"] = auth["cadcode"]
                        auth_data.append(tmp)

                for address in cusdeliveradd:
                    address.pop('id')
                    address['ccuscode'] = res['code']
                    address['cdeliveradd'] = address['cdeliveradd'] if address['cdeliveradd'] else ''
                    address['cenglishadd2'] = address['cenglishadd2'] if address['cenglishadd2'] else ''
                    address['cenglishadd3'] = address['cenglishadd3'] if address['cenglishadd3'] else ''
                    address['cenglishadd4'] = address['cenglishadd4'] if address['cenglishadd4'] else ''
                    address['clinkperson'] = address['clinkperson'] if address['clinkperson'] else ''
                    address['cdeliverunit'] = address['cdeliverunit'] if address['cdeliverunit'] else ''
                trade_terms = env['xlcrm.account.cus'].sudo().search([("review_id", "=", res.review_id.id)]).trade_terms
                reg_cash = float(res['reg_cash']) * 10000 if res['reg_cash'] else ""
                data = {
                    "customer": {
                        "code": res['code'],
                        "name": res['name'],
                        "abbrname": res['abbrname'],
                        "super_dept": res['super_dept'],
                        "spec_operator": res['spec_operator'],
                        "phone": res["phone"],
                        "contact": res['contact'],
                        "mobile": res['mobile'],
                        "email": res['email'],
                        "ccuscreditcompany": res['code'],
                        "ccdefine14": res['credit_rank'],
                        "credit_amount": res['credit_amount'],
                        "Credit": res['credit'],
                        "CreditDate": res['creditdate'],
                        "ccussaprotocol": res['ccussaprotocol'],
                        "devliver_site": {
                            "cusdeliveradd": cusdeliveradd
                        },
                        "sort_code": res['sort_code'],
                        "self_define9": res['payment'].replace('amp;', '&').replace('eq;', '=').replace('plus;',
                                                                                                        '+').replace(
                            'per;', '%'),
                        "ccusmngtypecode": res['ccusmngtypecode'],
                        "self_define4": res['account_remark'].replace('amp;', '&').replace('eq;', '=').replace('plus;',
                                                                                                               '+').replace(
                            'per;', '%'),
                        "ccdefine2": res['ccdefine2'],
                        "ccdefine10": res['payment'].replace('amp;', '&').replace('eq;', '=').replace('plus;',
                                                                                                      '+').replace(
                            'per;', '%'),
                        "ccussscode": res["ccussscode"].split('-')[0],
                        "ccusexch_name": res['ccusexch_name'],
                        "InvoiceCompany": res.code,
                        "cCusMnemCode": res.ccusmnemcode,
                        "customer_authall": {
                            "customer_auth": auth_data
                        },
                        "self_define8": res.cus_en_address,
                        "self_define11": env['xlcrm.account.sales'].sudo().search([("review_id", "=",
                                                                                    res.review_id.id)]).employees,
                        "self_define13": reg_cash,
                        "legal_man": res.legal_man,
                        "dDepBeginDate": res.begin_date,
                        "tax_reg_code": res.tax_reg_code,
                        "iCusTaxRate": res.cus_tax_rate,
                        "ccdefine15": res.vmi,
                        "address": res.address,
                        "self_define6": res.loa,
                        "self_define10": res.name_used_before,
                        "self_define2": res.invoicing_date,
                        "self_define3": res.settlement_date,
                        "ccdefine11": res.customer_class,
                        "self_define7": res.review_id.ke_company,
                        "self_define1": res.review_id.reconciliation_date,
                        "self_define5": trade_terms,
                        "ccdefine3": res.review_id.ccusabbname_en,
                        "seed_date":res.review_id.update_time
                    }
                }
                # 更新支付方式
                self.update_cus_payment(res)
                url = U8Login.get_cus_url(res.a_company, res.code)
                if url.split("/")[-1] == "add":
                    data['customer']['CreatePerson'] = res.review_id.init_user.nickname
                    # data['customer']['ccdefine3'] = res.ccdefine3
                else:
                    data['customer']['seed_date'] = res.seed_date
                    data['customer']['ModifyPerson'] = res.review_id.init_user.nickname
                    data['customer']['ModifyDate'] = res.review_id.update_time
                print("before requests", res.a_company, url, data)
                cus = requests.post(url, json.dumps(data, ensure_ascii=False, cls=MyEncoder).encode("utf-8"),
                                    headers=headers)
                resp = json.loads(cus.text)
                print("request success", resp)
                if resp['item']["@dsc"] == 'ok':
                    bank_data = env['xlcrm.u8_customer_bank'].sudo().search_read([('review_id', '=', res.review_id.id)],
                                                                                 fields=['cbank', 'cbranch',
                                                                                         'caccountnum', 'caccountname',
                                                                                         'bdefault'])

                    self.update_cus_bank(res, bank_data, url.split("/")[-1])
                    # self.update_cus_ccdefine(res)
                    desc['ok'] = True
                    desc['msg'] = resp['item']['@u8key']
                else:
                    desc['msg'] = resp['item']['@dsc']
            else:
                desc['msg'] = login.text
        except Exception as e:
            desc['msg'] = e
        finally:
            return desc

    @staticmethod
    def update_cus_bank(res, bank_data, category):
        desc = dict()
        from .public import u8_account_name
        try:
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            query_bank = list(
                map(lambda item: (
                    res.code, item["cbank"], item["cbranch"], item["caccountname"], item["caccountnum"],
                    item["bdefault"]), bank_data))
            if category == 'edit':
                mssql.in_up_de(
                    f"delete from {u8_account_name(res.a_company, odoo.tools.config['enviroment'])}.dbo.CustomerBank where cCusCode='{res.code}'")

            mssql.batch_in_up_de(
                [[
                    f'insert into {u8_account_name(res.a_company, odoo.tools.config["enviroment"])}.dbo.CustomerBank(cCusCode,cBank,cBranch,cAccountName,cAccountNum,bDefault)values(%s,%s,%s,%s,%s,%s)',
                    query_bank]])

            mssql.commit()
            mssql.close()
            desc['msg'] = 'ok'
        except Exception as e:
            desc['msg'] = e
        finally:
            return desc

    @staticmethod
    def update_cus_ccdefine(res):
        desc = dict()
        from .public import u8_account_name
        try:
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            q_sql = f"select cCusCode from {u8_account_name(res.a_company, odoo.tools.config['enviroment'])}.dbo.Customer_extradefine where cCusCode='{res.code}'"
            query_res = mssql.query(q_sql)
            if query_res:
                mssql.in_up_de(
                    f"update {u8_account_name(res.a_company, odoo.tools.config['enviroment'])}.dbo.Customer_extradefine set ccdefine15='{res.vmi}' where cCusCode='{res.code}'")

            else:
                mssql.in_up_de(
                    f"insert into {u8_account_name(res.a_company, odoo.tools.config['enviroment'])}.dbo.Customer_extradefine(cCusCode,ccdefine15)values('{res.code}','{res.vmi}')")
            mssql.commit()
            mssql.close()
            desc['msg'] = 'ok'
        except Exception as e:
            desc['msg'] = e
        finally:
            return desc

    @staticmethod
    def update_cus_payment(res):
        desc = dict()
        from .public import u8_account_name
        try:
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            payment = res.payment.replace('amp;', '&').replace('eq;', '=').replace('plus;', '+').replace('per;', '%')
            mssql.in_up_de(
                f"insert into {u8_account_name(res.a_company, odoo.tools.config['enviroment'])}.dbo.UserDefine(cID,cValue)values('70','{payment}')")
            mssql.commit()
            mssql.close()
            desc['msg'] = 'ok'
        except Exception as e:
            pass

    @staticmethod
    def synchronization_cus_mcode(res):
        desc = dict()
        from .public import u8_account_name
        try:
            con_str = '158_999'
            if odoo.tools.config["enviroment"] == 'PRODUCT':
                con_str = '154_999'
            mssql = connect_mssql.Mssql(con_str)
            count = set(map(lambda x: x.a_company, res))
            for _c in count:
                query_data = list(
                    map(lambda item: (item.ccusmnemcode, item.code), filter(lambda x: x.a_company == _c, res)))
                mssql.batch_in_up_de(
                    [[
                        f'update {u8_account_name(_c, odoo.tools.config["enviroment"])}.dbo.Customer set ccusmnemcode=%s where cCusCode=%s',
                        query_data]])
            mssql.commit()
            mssql.close()
            desc['msg'] = 'ok'
        except Exception as e:
            desc['msg'] = e
        finally:
            return desc

    @classmethod
    def grab_consolidated(cls, env):
        import requests
        js_res = requests.get('https://api.trade.gov/static/consolidated_screening_list/consolidated.json')
        results = json.loads(js_res.text)['results']
        data = list(map(lambda x: {"name": x['name']}, results))
        env['consolidated'].sudo().search([(1, '=', 1)]).unlink()
        env['consolidated'].sudo().create(data)
        env.cr.commit()

    @classmethod
    def suit_consolidated(cls, env):
        from .connect_mssql import Mssql
        import re
        # mssql = Mssql("ErpCrmDB")
        # sql = "select cCusCode,cCusName,cCusType,cCusMnemCode,companycode from " \
        #       "[dbo].[v_Customer_CCF_ALL] where cCusMnemCode is not null"
        # data = mssql.query(sql)
        data = []
        db_sql = "SELECT name FROM MASter..SysDatabASes  where  name  like 'UFDATA_%' and name not like 'UFDATA_999_%'"
        con_str, enviroment = '158_999', odoo.tools.config["enviroment"]
        if enviroment == 'PRODUCT':
            con_str = '154_999'
        con_str = '154_999'
        with Mssql(con_str) as mssql:
            db_res = mssql.query(db_sql)
            for db in db_res:
                try:
                    sql = f"""
                            use {db[0]};
                            select distinct c.cCusCode,c.cCusName,c.cCusMnemCode from Sales_FHD_W a
                             left join Sales_FHD_T b on a.dlid=b.dlid  
                             left join Customer c on a.cdefine23=c.cCusCode
                             where(cVouchType=N'05' and (bFirst=1 or (bFirst=0 and dDate>=(select cvalue from accinformation where csysid=N'SA' and cName=N'dStartDate')))) 
                             and ( dDate>=GETDATE()-365
                              And (cInvDefine2 IN (N'BROADCOM',N'AVAGO',N'SYNAPTICS'))) and isnull(cchildcode,N'')=N'' and isnull(cCusMnemCode,N'')<>N''
                        """
                    res = mssql.query(sql)
                    for _res in res:
                        tmp = dict()
                        tmp['code'] = _res[0].strip()
                        tmp['name'] = _res[1].strip()
                        tmp['ccusmnemcode'] = _res[2].strip()
                        tmp['a_company'] = re.search(r"UFDATA_(.*?)_", db[0]).group(1)
                        data.append(tmp)
                except Exception as e:
                    pass
        tar = []
        for _data in data:
            res = env['consolidated'].sudo().search_read([('name', 'ilike', _data['ccusmnemcode'])])
            if res:
                tmp = list(map(lambda x: x["name"], res))
                tar.append({"code": _data['code'], "name": _data['name'], "source": "U8档案",
                            "a_company": _data['a_company'],
                            "ccusmnemcode": _data['ccusmnemcode'], "result": ';'.join(tmp),
                            "a_companycode": _data['a_company']})

        env["u8.cus.consolidated"].sudo().search([('review_id', '=', False)]).unlink()
        env["u8.cus.consolidated"].sudo().create(tar)
        env.cr.commit()

    @staticmethod
    def update_brand_limit_to_u8(res, brand):
        import datetime
        if res.brand_limit == 1:
            from . import connect_mssql
            con_str = '154_999' if odoo.tools.config["enviroment"] == 'PRODUCT' else '158_999'
            mssql = connect_mssql.Mssql(con_str)
            data_insert, data_update = [], []
            for _brand in brand:
                res_brand = mssql.query(
                    f"select id from EF_BrandLimit where companyCode='{res.a_companycode}' and cCusCode='{res.code}' and cBrand='{_brand['brand_name']}'")
                if not res_brand:
                    mssql.in_up_de(
                        "insert into EF_BrandLimit(companyCode,cCusCode,cBrand,cEditor,cEditDate,cAuditer,cAuditDate)"
                        f"values('{res.a_companycode}','{res.code}','{_brand['brand_name']}','{_brand['init_nickname']}','{datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d')}','{_brand['pm']}','{datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d')}')")
                else:
                    mssql.in_up_de(
                        f"update EF_BrandLimit set cEditor='{_brand['init_nickname']}',cEditDate='{datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d')}',cAuditer='{_brand['pm']}',cAuditDate='{datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d')}' "
                        f"where companyCode='{res.a_companycode}' and cCusCode='{res.code}' and cBrand='{_brand['brand_name']}'"
                    )
                material = _brand["material"]
                for item in material:
                    material = item.get('material_limit').replace('amp;', '&').replace('eq;', '=').replace('plus;',
                                                                                                           '+').replace(
                        'per;', '%')
                    start_date = datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d')
                    end_date = datetime.datetime.strftime(
                        _brand['init_time'].replace(year=_brand['init_time'].year + 99), '%Y-%m-%d')
                    if material:
                        res_ma = mssql.query(f"select id from EF_InvPermit where companyCode='{res.a_companycode}'"
                                             f" and cCusCode='{res.code}' and cInvCode='{material}'")
                        if not res_ma:
                            data_insert.append((res.a_companycode, res.code, material,
                                                start_date, end_date, _brand["init_nickname"],
                                                start_date, _brand["pm"],
                                                datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d') if _brand[
                                                    'init_time'] else ''))
                        else:
                            data_update.append((start_date, end_date, _brand["init_nickname"],
                                                start_date, _brand["pm"],
                                                datetime.datetime.strftime(_brand['init_time'], '%Y-%m-%d') if _brand[
                                                    'init_time'] else '', res.a_companycode, res.code, material))
            if data_insert:
                mssql.batch_in_up_de(
                    [[
                        "insert into EF_InvPermit(companyCode,cCusCode,cInvCode,cStartDate,cEndDate,cEditor,cEditDate,cAuditer,cAuditDate)values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        data_insert]])
            if data_update:
                mssql.batch_in_up_de(
                    [[
                        "update EF_InvPermit set cStartDate=%s,cEndDate=%s,cEditor=%s,cEditDate=%s,cAuditer=%s,cAuditDate=%s where companyCode=%s and cCusCode=%s and cInvCode=%s ",
                        data_update]])
            res.status = 2
            mssql.commit()
            mssql.close()
