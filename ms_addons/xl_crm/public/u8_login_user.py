import datetime, odoo


class U8User:
    @classmethod
    def test(cls,account, code):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"test@{account}", "sLoginDate": f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.158:13399/Login/Token'
        url = f'http://192.168.0.158:13399/BasicArchive/customer/{cls.cus_exit(account,code)}'
        return base_info, login_url, url

    @classmethod
    def product(cls,account, code):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"(default)@{account}",
                     "sLoginDate": f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.154:13399/Login/Token'
        url = f'http://192.168.0.154:13399/BasicArchive/customer/{cls.cus_exit(account,code)}'
        return base_info, login_url, url

    @staticmethod
    def cus_exit(account,code):
        from . import connect_mssql,public
        con_str = '158_999'
        if odoo.tools.config["enviroment"] == 'PRODUCT':
            con_str = '154_999'
        mssql = connect_mssql.Mssql(con_str)
        database = public.u8_account_name(account, odoo.tools.config['enviroment'])
        res = mssql.query(f"select cCusCode from {database}.dbo.Customer where cCusCode='{code}'")
        if isinstance(res, list) and len(res) > 0:
            return 'edit'
        return 'add'
