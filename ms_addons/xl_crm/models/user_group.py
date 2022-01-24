# -*- coding: utf-8 -*-
from odoo import models, fields

class Xlusergroup(models.Model):
    _name = 'xlcrm.user.group'
    name = fields.Char(string='用户组', required=True)
    sort = fields.Integer(string='排序值')
    status = fields.Integer('状态', required=True, default=1)
    system = fields.Integer('系统用户', required=True, default=1)
    description = fields.Text('备注')
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.utc_now(self))

    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "用户组已经存在!"),
    ]