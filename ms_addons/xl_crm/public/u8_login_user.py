import datetime, odoo
import requests
import json


class U8Login:
    enviroment = odoo.tools.config["enviroment"]

    def __init__(self, account):
        self.token = None
        self.login_url = None
        self.logout_url = None
        self.login_data = None
        self.account = account
        self.headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.get_params()

    def get_params(self):
        if self.enviroment == "PRODUCT":
            params = self.product()
        else:
            params = self.test()
        self.login_data, self.login_url, self.logout_url = params

    def __enter__(self):
        login = requests.post(self.login_url, json.dumps(self.login_data),
                              headers=self.headers)
        if login.ok:
            self.token = json.loads(login.text)
        return login

    def __exit__(self, exc_type, exc_val, exc_tb):
        res = requests.get(f"{self.logout_url}{self.token}")
        print(res.text)

    def test(self):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"test@{self.account}",
                     "sLoginDate": f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.158:13399/Login/Token'
        logout_url = f"http://192.168.0.158:13399/Login/LoginOut?apiToken="
        return base_info, login_url, logout_url

    def product(self):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"(default)@{self.account}",
                     "sLoginDate": f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.154:13399/Login/Token'
        logout_url = f"http://192.168.0.154:13399/Login/LoginOut?apiToken="
        return base_info, login_url, logout_url

    @classmethod
    def cus_exit(cls, account, code):
        from . import connect_mssql, public
        con_str = '158_999'
        if cls.enviroment == 'PRODUCT':
            con_str = '154_999'
        mssql = connect_mssql.Mssql(con_str)
        database = public.u8_account_name(account, cls.enviroment)
        res = mssql.query(f"select cCusCode from {database}.dbo.Customer where cCusCode='{code}'")
        if isinstance(res, list) and len(res) > 0:
            return 'edit'
        return 'add'

    @classmethod
    def get_cus_url(cls, account, code):
        url = f'http://192.168.0.158:13399/BasicArchive/customer/{cls.cus_exit(account, code)}'
        if cls.enviroment == "PRODUCT":
            url = f'http://192.168.0.154:13399/BasicArchive/customer/{cls.cus_exit(account, code)}'
        return url
