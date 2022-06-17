# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import datetime, pytz


class Send_email:
    def __init__(self, from_addr="crm@szsunray.com", qqCode="Sunray201911"):
        self.from_addr = from_addr  # 邮件发送账号
        self.qqCode = qqCode  # 授权码（这个要填自己获取到的）,sunray邮箱的授权为邮箱密码
        self.smtp_server = "smtp.szsunray.com"  # 固定写死
        self.smtp_port = 465  # 固定端口
        self.mail = MIMEMultipart()

    def certify(self):
        if not self.from_addr:
            return {"code": 500, "msg": "发送者的邮箱地址为空,请联系管理员确认人事资料是否有维护个人邮箱地址"}
        if not self.qqCode:
            return {"code": 500, "msg": "发送者的邮箱密码为空,不能发送,请到修改密码页面维护个人邮箱密码"}
        self.smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)  # 配置服务器
        self.smtp.login(self.from_addr, self.qqCode)

    def send(self, subject="", to=[], cc=[], content="", subtype='html', env=''):
        """
        发送邮件模块
        :param subject: 邮件主旨
        :param to: list 收件人邮箱地址
        :param cc: list 抄送人邮箱地址
        :param content: 邮件内容
        :param subtype: 内容形式text or html
        :return: {"code":200,"msg":"发送成功"} or {"code":500,"msg":"错误信息"}
        """
        result = {"code": 200, "msg": "发送成功"}
        tz = pytz.timezone('Asia/Shanghai')
        subject = "(测试邮件)" + subject
        subject += datetime.datetime.strftime(datetime.datetime.now(tz=tz), '%Y-%m-%d %H:%M:%S')
        data = {"code": 200, "message": "发送成功", "subject": subject, "content": content,
                "to_email": ','.join(to), "cc_email": ','.join(cc)}
        try:
            cer_msg = self.certify()
            if cer_msg:
                return cer_msg
            self.mail = MIMEText(content, _subtype=subtype, _charset='utf-8')
            self.mail["subject"] = Header(subject, 'utf-8').encode()
            self.mail["from"] = self.from_addr  # 需与邮件服务器的认证用户一致
            self.mail["to"] = ','.join(to)
            self.mail["cc"] = ','.join(cc)
            recivers = to + cc
            self.smtp.sendmail("crm@szsunray.com", recivers, self.mail.as_string())
            self.smtp.quit()

        except Exception as e:
            result = {"code": 500, "msg": str(e)}
            data["code"] = 500
            data["message"] = str(e)
        finally:
            env['xlcrm.maillogs'].sudo().create(data)
            return result


def getCode():
    import random
    from . import connect_mssql
    res = [1]
    code = 100000
    while res:
        code = random.randint(100000, 999999)
        mssql = connect_mssql.connect_mssql.Mssql('wechart')
        res = mssql.query('select id from Wx_email where Code=%d' % code)
    return code
