# -*- coding: utf-8 -*-
from odoo import models, fields

class Xlccfusergroup(models.Model):
    _name = 'xlcrm.user.ccfgroup'
    name = fields.Char(string='组英文名称')
    label = fields.Char(string='组名称')
    users = fields.Char(string='组成员')
    status = fields.Integer('状态', default=0)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', "用户组已经存在!"),
    # ]