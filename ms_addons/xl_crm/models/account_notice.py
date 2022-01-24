# -*- coding: utf-8 -*-
from odoo import models, fields

class Xlccfusernotice(models.Model):
    _name = 'xlcrm.user.ccfnotice'
    a_company = fields.Char(string='交易主体')
    a_companycode = fields.Char(string='交易主体代码')
    lg = fields.Char(string='法务组邮件通知人')
    risk = fields.Char(string='风控组邮件通知人')
    fd = fields.Char(string='财务组邮件通知人')
    init_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    init_users = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    update_time = fields.Datetime(string='更新时间')
    update_user = fields.Char(string='更新人')

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', "用户组已经存在!"),
    # ]