from . import send_email, connect_mssql
import odoo
from apscheduler.schedulers.blocking import BlockingScheduler
from threading import Thread


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
