from . import send_email, connect_mssql
import odoo
from odoo import modules


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
                    # sheet.col(15).width = self.len_byte(material)
                    profit = f'{item.get("profit")}%' if item.get('profit', "") else ''
                    sheet.write(main_start, 16, profit, style)
                    # sheet.col(16).width = self.len_byte(profit)
                    sheet.write(main_start, 17, period[index].get('kc_company', ""), style)
                    # sheet.col(17).width = self.len_byte(period[index].get('kc_company', ""))
                    sheet.write(main_start, 18, period[index].get('release_time', ""), style)
                    # sheet.col(18).width = self.len_byte(period[index].get('release_time', ""))
                    sheet.write(main_start, 19, period[index].get('payment_method', ""), style)
                    # sheet.col(19).width = self.len_byte(period[index].get('payment_method', ""))
                    sheet.write(main_start, 20,
                                f'{period[index].get("credit_limit_now", "")}{period[index].get("credit_limit_now_currency", "")}',
                                style)
                    # sheet.col(20).width = self.len_byte(
                    #     f'{period[index].get("credit_limit_now", "")}{period[index].get("credit_limit_now_currency", "")}')
                    sheet.write(main_start, 21, period[index].get('transaction_status', ""), style)
                    # sheet.col(21).width = self.len_byte(period[index].get('transaction_status', ""))
                    main_start += 1

            # file_path = modules.module.get_module_resource('xl_crm') + '/static/test.xls'
            workbook.save(file_path)
            return file_path
        except Exception as e:
            print(e)

    @staticmethod
    def synchronization_cus(res):
        try:
            import requests, json
            from .u8_login_user import U8User
            desc = {'ok': False, 'msg': ''}
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            u8user = U8User()
            login_data, login_url, add_url = u8user.product(res.a_company) if odoo.tools.config[
                                                                                  "enviroment"] == 'PRODUCT' else u8user.test(
                res.a_company)
            login = requests.post(login_url, json.dumps(login_data),
                                  headers=headers)
            if login.ok:
                headers['apiToken'] = json.loads(login.text)
                data = {
                    "customer": {
                        "code": res['code'],
                        "name": res['name'],
                        "abbrname": res['abbrname'],
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
                        "ccusexch_name": res['ccusexch_name'],
                        "seed_date": res['seed_date'],
                    }
                }
                cus = requests.post(add_url, data=json.dumps(data),
                                    headers=headers)
                resp = json.loads(cus.text)
                if resp['item']["@dsc"] == 'ok':
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
                query_data = list(map(lambda item: (item.ccusmnemcode, item.code), filter(lambda x: x.a_company == _c, res)))
                mssql.batch_in_up_de(
                    [[f'update {u8_account_name(_c,odoo.tools.config["enviroment"])}.dbo.Customer set ccusmnemcode=%s where cCusCode=%s', query_data]])
            mssql.commit()
            mssql.close()
            desc['msg'] = 'ok'
        except Exception as e:
            desc['msg'] = e
        finally:
            return desc
