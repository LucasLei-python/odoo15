# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Xlmenu(models.Model):
    _name = 'xlcrm.auth.rule'
    name = fields.Char(string='权限名称', required=True)
    module = fields.Char(string='模块')
    menu_auth = fields.Char(string='菜单权限')
    log_auth = fields.Char(string='数据权限')
    status = fields.Integer(string='状态', default=1)
    sort = fields.Integer(string='排序')
    group_id = fields.Many2one("xlcrm.user.group", string='用户组', store=True)
    create_date_time = fields.Datetime(string='创建时间', default=lambda self: fields.Datetime.now())
    create_user_id = fields.Many2one('xlcrm.users', store=True, string='创建人员', readonly=True)
    write_user_id = fields.Many2one('xlcrm.users', store=True, string='修改人员', readonly=True)
    create_user_name = fields.Char(related='create_user_id.username', string='创建人', store=False)
    write_user_name = fields.Char(related='write_user_id.username', string='修改人', store=False)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "权限名称已经存在!"),
    ]

