import datetime


class U8User:
    @staticmethod
    def test(account):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"test@{account}", "sLoginDate":f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.158:13399/Login/Token'
        add_url = 'http://192.168.0.158:13399/BasicArchive/customer/add'
        return base_info, login_url, add_url

    @staticmethod
    def product(account):
        base_info = {"sServer": "192.168.0.158", "sAccID": f"test@{account}", "sLoginDate": f"{datetime.date.today()}",
                     "sUserID": "EDI2", "sPassword": "@Yyh2022", "sSubId": "AS", "sSerial": "abc@123"}
        login_url = 'http://192.168.0.158:13399/Login/Token'
        add_url = 'http://192.168.0.158:13399/BasicArchive/customer/add'
        return base_info, login_url, add_url
